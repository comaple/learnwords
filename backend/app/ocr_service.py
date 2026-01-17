import os
import requests
import re
import base64
import time
from typing import Dict


class OCRService:
    def __init__(self, api_key: str = None):
        # Allow passing an explicit API key (useful for tests).
        # If not provided, read from env. Don't raise here so tests can
        # instantiate and monkeypatch methods without needing env vars.
        self.api_key = api_key or os.getenv('GEMINI_API_KEY', '')
        self.disabled = not bool(self.api_key)
        self.model = os.getenv('GEMINI_MODEL', 'gemini-image-1')
        self.url = f'https://generativelanguage.googleapis.com/v1/models/{self.model}:predict'
        # retry settings
        try:
            self.max_attempts = int(os.getenv('GEMINI_MAX_ATTEMPTS', '3'))
        except Exception:
            self.max_attempts = 3
        try:
            self.base_timeout = float(os.getenv('GEMINI_TIMEOUT', '30'))
        except Exception:
            self.base_timeout = 30.0

    def _call_gemini(self, image_path: str) -> Dict:
        if self.disabled:
            raise RuntimeError('GEMINI_API_KEY must be set')
        with open(image_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')

        # Construct a minimal request payload. Adjust to match the exact Generative API schema if needed.
        payload = {
            'instances': [
                {
                    'image': {
                        'image_bytes': b64
                    },
                    'instructions': 'Extract the textual content from the image and return plain text.'
                }
            ]
        }

        params = {}
        headers = {}
        # If the key looks like an API key (AIza...), send as query param; otherwise try Bearer token.
        if self.api_key.startswith('AIza'):
            params['key'] = self.api_key
        else:
            headers['Authorization'] = f'Bearer {self.api_key}'

        last_exc = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                resp = requests.post(self.url, params=params, headers=headers, json=payload, timeout=self.base_timeout)
                resp.raise_for_status()
                try:
                    return resp.json()
                except ValueError:
                    # Non-JSON response
                    return {'_raw_text': resp.text}
            except requests.RequestException as e:
                last_exc = e
                # exponential backoff with jitter
                if attempt < self.max_attempts:
                    sleep_for = (2 ** (attempt - 1)) + (0.1 * attempt)
                    time.sleep(sleep_for)
                    continue
                # exhausted retries
                raise RuntimeError(f'Gemini API request failed after {self.max_attempts} attempts: {e}')

    def _extract_text_from_response(self, resp_json: Dict) -> str:
        texts = []

        def walk(obj):
            if isinstance(obj, str):
                texts.append(obj)
            elif isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(resp_json)
        return '\n'.join(texts)

    def process_document(self, file_path: str) -> Dict:
        try:
            result = self._call_gemini(file_path)
        except Exception:
            raise

        raw_text = self._extract_text_from_response(result)
        words = re.findall(r"\b[A-Za-z]+\b", raw_text)
        english_words = list({w.lower() for w in words if len(w) > 2})
        return {
            'raw_result': result,
            'words': english_words,
            'count': len(english_words),
        }

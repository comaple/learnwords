# Frontend Setup & Development

## Quick Start

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start dev server (runs on http://localhost:5173):
```bash
npm run dev
```

## Features

- **Authentication**: Register and login with email/password
- **Document Upload**: Upload files for OCR processing
- **Learning Plan**: View words extracted via OCR
- **Progress Tracking**: Submit learning progress (Hard/Medium/Easy)

## Architecture

- **Vite**: Fast build tool and dev server
- **React**: Component-based UI framework
- **Axios**: HTTP client for API calls
- **CSS**: Responsive styling with modern design

## API Integration

The frontend communicates with the backend API at `http://localhost:8000/api/v1`:
- `/users/register` - User registration
- `/users/login` - User login
- `/upload` - File upload with OCR
- `/upload/{upload_id}` - Get upload status
- `/learning/plan` - Get learning plan
- `/learning/progress` - Submit progress

## Build for Production

```bash
npm run build
```

The build output will be in the `dist/` directory.

## Tauri Integration (Future)

To integrate with Tauri for desktop deployment:
```bash
npm install @tauri-apps/cli
npm run tauri dev
```

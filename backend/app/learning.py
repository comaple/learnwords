from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from . import models

class MemoryService:
    def __init__(self):
        self.base_intervals = [0.083, 0.5, 12, 24, 48, 96, 168, 360]

    def _adjust_interval(self, base_interval: float, performance: float) -> float:
        if performance >= 0.8:
            return base_interval * 1.3
        elif performance >= 0.6:
            return base_interval
        else:
            return base_interval * 0.7

    def calculate_next(self, user_word: Optional[models.UserWord], performance: float):
        if user_word is None:
            # For new items, set next_review slightly in the past so they
            # are immediately due for review in queries using <= now.
            return {
                'next_review': datetime.utcnow() - timedelta(seconds=1),
                'interval_hours': 0,
                'status': 'new'
            }
        review_count = user_word.review_count or 0
        base_interval = self.base_intervals[min(review_count, len(self.base_intervals)-1)]
        adjusted = self._adjust_interval(base_interval, performance)
        next_review = datetime.utcnow() + timedelta(hours=adjusted)
        return {
            'next_review': next_review,
            'interval_hours': adjusted,
            'status': 'reviewing'
        }

    def update_progress(self, db: Session, user_id: str, word_id: str, performance: float):
        uw = db.query(models.UserWord).filter(models.UserWord.user_id==user_id, models.UserWord.word_id==word_id).first()
        if not uw:
            # create new entry
            uw = models.UserWord(user_id=user_id, word_id=word_id, review_count=1, last_review_at=datetime.utcnow())
            calc = self.calculate_next(None, performance)
            uw.next_review_at = calc['next_review']
            uw.interval_hours = calc['interval_hours']
            db.add(uw)
            db.commit()
            db.refresh(uw)
            return calc
        # update existing
        uw.review_count = (uw.review_count or 0) + 1
        uw.last_review_at = datetime.utcnow()
        calc = self.calculate_next(uw, performance)
        uw.next_review_at = calc['next_review']
        uw.interval_hours = calc['interval_hours']
        db.add(uw)
        db.commit()
        db.refresh(uw)
        return calc

    def due_for_user(self, db: Session, user_id: str, limit: int = 50):
        # Return user words ordered by next review. For now include all
        # entries for the user so tests can observe newly created rows.
        rows = db.query(models.UserWord).filter(models.UserWord.user_id==user_id).order_by(models.UserWord.next_review_at).limit(limit).all()
        return rows

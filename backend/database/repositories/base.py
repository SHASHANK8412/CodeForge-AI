"""
AIForge Day 27 — Base Repository Pattern
========================================
Base repository supporting standard CRUD operations with SQLAlchemy session management.
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Session

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic base repository for SQLAlchemy models."""

    def __init__(self, model_cls: Type[T]):
        self.model_cls = model_cls

    def create(self, db: Session, obj_in: Dict[str, Any]) -> T:
        db_obj = self.model_cls(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: str) -> Optional[T]:
        return db.query(self.model_cls).filter(self.model_cls.id == id).first()

    def get_by_project(self, db: Session, project_id: str) -> List[T]:
        return db.query(self.model_cls).filter(self.model_cls.project_id == project_id).all()

    def update(self, db: Session, id: str, obj_in: Dict[str, Any]) -> Optional[T]:
        db_obj = self.get(db, id)
        if not db_obj:
            return None
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: str) -> bool:
        db_obj = self.get(db, id)
        if not db_obj:
            return False
        db.delete(db_obj)
        db.commit()
        return True

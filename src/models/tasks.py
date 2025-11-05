from sqlalchemy import Column, DateTime, String

from src.models.abstract import AbstractBase


class Tasks(AbstractBase):
    __tablename__ = "tasks"

    task_id = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="PENDING")
    completed_at = Column(DateTime(timezone=True), nullable=True)


    def __repr__(self):
        return f"{self.task_id} - {self.status}"

from sqlalchemy import Column, Integer, String

from src.models.abstract import AbstractBase


class ApiKey(AbstractBase):
    __tablename__ = "api_keys"

    key = Column(String(255), nullable=False)

    def __repr__(self):
        return f"{self.id}"

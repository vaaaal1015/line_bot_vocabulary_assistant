from ..shared.db import db
from sqlalchemy.orm import Mapped, mapped_column


class Vocabulary(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    english: Mapped[str] = mapped_column(unique=True)
    chinese: Mapped[str] = mapped_column(nullable=False)

    def __init__(self, english: str, chinese: str):
        self.english = english
        self.chinese = chinese

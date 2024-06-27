from ..shared.db import db
from sqlalchemy.orm import Mapped, mapped_column


class Vocabulary(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    english: Mapped[str] = mapped_column(unique=True, nullable=False)
    chinese: Mapped[str] = mapped_column(nullable=False)
    point: Mapped[int] = mapped_column(nullable=False, default=5)

    def __init__(self, english: str, chinese: str) -> None:
        self.english = english
        self.chinese = chinese
        self.point = 0

    def __str__(self) -> str:
        return f"{self.english} {self.chinese}"

    def deduct_point(self):
        self.point = self.point - 1

    def bonus_point(self):
        self.point = self.point + 1

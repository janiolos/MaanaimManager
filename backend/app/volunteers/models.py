from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Voluntario(Base):
    """Model para Voluntário."""

    __tablename__ = "core_voluntario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    igreja: Mapped[str] = mapped_column(String(255), default="")
    area: Mapped[str] = mapped_column(String(255), default="")
    regiao: Mapped[str] = mapped_column(String(255), default="")
    especialidade: Mapped[str] = mapped_column(String(255), default="")

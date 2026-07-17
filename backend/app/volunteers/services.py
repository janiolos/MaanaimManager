from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.volunteers.models import Voluntario
from app.volunteers.schemas import VoluntarioCreate, VoluntarioUpdate


class VoluntarioService:
    """Serviço para gerenciar voluntários."""

    @staticmethod
    async def list_all(session: AsyncSession) -> Sequence[Voluntario]:
        stmt = select(Voluntario).order_by(Voluntario.nome)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get(session: AsyncSession, voluntario_id: int) -> Voluntario:
        stmt = select(Voluntario).where(Voluntario.id == voluntario_id)
        result = await session.execute(stmt)
        voluntario = result.scalar_one_or_none()
        if voluntario is None:
            raise NoResultFound(f"Voluntário {voluntario_id} não encontrado")
        return voluntario

    @staticmethod
    async def create(session: AsyncSession, payload: VoluntarioCreate) -> Voluntario:
        voluntario = Voluntario(**payload.model_dump())
        session.add(voluntario)
        await session.flush()
        return voluntario

    @staticmethod
    async def update(session: AsyncSession, voluntario: Voluntario, payload: VoluntarioUpdate) -> Voluntario:
        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(voluntario, key, value)
        await session.flush()
        return voluntario

    @staticmethod
    async def delete(session: AsyncSession, voluntario: Voluntario) -> None:
        await session.delete(voluntario)
        await session.flush()

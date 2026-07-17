from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VoluntarioBase(BaseModel):
    nome: str
    igreja: str = ""
    area: str = ""
    regiao: str = ""
    especialidade: str = ""


class VoluntarioCreate(VoluntarioBase):
    pass


class VoluntarioUpdate(BaseModel):
    nome: str | None = None
    igreja: str | None = None
    area: str | None = None
    regiao: str | None = None
    especialidade: str | None = None


class VoluntarioOut(VoluntarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

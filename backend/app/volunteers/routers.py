from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_scopes
from app.db.session import get_session
from app.volunteers import schemas, services

router = APIRouter(prefix="/voluntarios", tags=["voluntarios"])


@router.get("", response_model=list[schemas.VoluntarioOut])
async def list_voluntarios(
    current: Annotated[CurrentUser, Depends(require_scopes("core:read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.VoluntarioOut]:
    items = await services.VoluntarioService.list_all(session)
    return [schemas.VoluntarioOut.model_validate(x) for x in items]


@router.post("", response_model=schemas.VoluntarioOut, status_code=201)
async def create_voluntario(
    current: Annotated[CurrentUser, Depends(require_scopes("core:write"))],
    payload: schemas.VoluntarioCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.VoluntarioOut:
    voluntario = await services.VoluntarioService.create(session, payload)
    return schemas.VoluntarioOut.model_validate(voluntario)


@router.get("/{voluntario_id}", response_model=schemas.VoluntarioOut)
async def get_voluntario(
    current: Annotated[CurrentUser, Depends(require_scopes("core:read"))],
    voluntario_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.VoluntarioOut:
    try:
        voluntario = await services.VoluntarioService.get(session, voluntario_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado") from exc
    return schemas.VoluntarioOut.model_validate(voluntario)


@router.patch("/{voluntario_id}", response_model=schemas.VoluntarioOut)
async def update_voluntario(
    current: Annotated[CurrentUser, Depends(require_scopes("core:write"))],
    voluntario_id: int,
    payload: schemas.VoluntarioUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.VoluntarioOut:
    try:
        voluntario = await services.VoluntarioService.get(session, voluntario_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado") from exc
    voluntario = await services.VoluntarioService.update(session, voluntario, payload)
    return schemas.VoluntarioOut.model_validate(voluntario)


@router.delete("/{voluntario_id}", status_code=204)
async def delete_voluntario(
    current: Annotated[CurrentUser, Depends(require_scopes("core:write"))],
    voluntario_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    try:
        voluntario = await services.VoluntarioService.get(session, voluntario_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=404, detail="Voluntário não encontrado") from exc
    await services.VoluntarioService.delete(session, voluntario)
    return None

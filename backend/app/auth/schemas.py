"""Schemas Pydantic do módulo auth."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"
    expires_in: int = Field(description="Tempo de vida do access token em segundos")


class RefreshOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class GroupOut(BaseModel):
    id: int
    name: str


class UserOut(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    is_superuser: bool
    is_staff: bool
    groups: list[GroupOut]
    scopes: list[str]


class MeOut(UserOut):
    pass


from app.auth.scopes import groups_to_scopes  # noqa: E402  (evita forward-annotation)


class _UserOutAdapter:
    @classmethod
    def from_dto(cls, user_id: int, username: str, first_name: str, last_name: str, email: str,
                 is_superuser: bool, is_staff: bool, groups: list[GroupOut]) -> UserOut:
        scopes = groups_to_scopes([g.name for g in groups], is_superuser)
        return UserOut(
            id=user_id, username=username, first_name=first_name, last_name=last_name,
            email=email, is_superuser=is_superuser, is_staff=is_staff,
            groups=groups, scopes=scopes,
        )


TokenOut.model_rebuild()
UserOut.model_rebuild()
MeOut.model_rebuild()
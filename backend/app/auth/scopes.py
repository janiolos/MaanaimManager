"""Mapa de papéis (Django Groups) -> scopes JWT.

Substitui apps/core/permissions.py do Django legado.
Superuser bypassa todos os gates.
"""

from __future__ import annotations

# Papéis (espelham apps/core/permissions.py)
ROLE_ADMINISTRADOR = "ADMINISTRADOR"
ROLE_FINANCEIRO = "FINANCEIRO"
ROLE_FINANCEIRO_LEITURA = "FINANCEIRO_LEITURA"
ROLE_ESTOQUE = "ESTOQUE"
ROLE_ESTOQUE_LEITURA = "ESTOQUE_LEITURA"
ROLE_HOSPEDAGEM = "HOSPEDAGEM"
ROLE_HOSPEDAGEM_LEITURA = "HOSPEDAGEM_LEITURA"
ROLE_MENSAGENS = "MENSAGENS"
ROLE_MENSAGENS_LEITURA = "MENSAGENS_LEITURA"
ROLE_COORDENADOR = "COORDENADOR"
ROLE_VISUALIZACAO = "VISUALIZACAO"

# Legacy aliases
LEGACY_ADMIN = "ADMIN"
LEGACY_FINANCEIRO = "TESOURARIA"
LEGACY_VISUALIZACAO = "LEITURA"

# Grupos que concedem escopo de escrita por módulo
_WRITE_GROUPS = {
    "core": {ROLE_ADMINISTRADOR, ROLE_COORDENADOR, LEGACY_ADMIN},
    "finance": {ROLE_ADMINISTRADOR, ROLE_FINANCEIRO, LEGACY_FINANCEIRO, ROLE_COORDENADOR, LEGACY_ADMIN},
    "inventory": {ROLE_ADMINISTRADOR, ROLE_ESTOQUE, ROLE_COORDENADOR, LEGACY_ADMIN},
    "lodging": {ROLE_ADMINISTRADOR, ROLE_HOSPEDAGEM, ROLE_COORDENADOR, LEGACY_ADMIN},
    "admin": {ROLE_ADMINISTRADOR, ROLE_COORDENADOR, LEGACY_ADMIN},
}

# _LEITURA suffix -> read scope no mesmo módulo
_READ_GROUPS = {
    "finance": {ROLE_FINANCEIRO_LEITURA},
    "inventory": {ROLE_ESTOQUE_LEITURA},
    "lodging": {ROLE_HOSPEDAGEM_LEITURA},
}


def groups_to_scopes(groups: list[str], is_superuser: bool = False) -> list[str]:
    """Converte lista de nomes de Group em scopes JWT (ex: 'finance:write')."""
    if is_superuser:
        return [
            "core:read", "core:write",
            "finance:read", "finance:write",
            "inventory:read", "inventory:write",
            "lodging:read", "lodging:write",
            "admin:read", "admin:write",
        ]
    scopes: set[str] = set()
    for module, names in _WRITE_GROUPS.items():
        if any(g in names for g in groups):
            scopes.add(f"{module}:read")
            scopes.add(f"{module}:write")
    for module, names in _READ_GROUPS.items():
        if any(g in names for g in groups):
            scopes.add(f"{module}:read")
    # todo usuário autenticado pode ler core
    scopes.add("core:read")
    return sorted(scopes)
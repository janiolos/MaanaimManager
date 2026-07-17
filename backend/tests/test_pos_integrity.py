"""Regressões das regras de integridade introduzidas no PDV."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.main import app
from app.pos.schemas import (
    LocalVendaCreate,
    ProdutoLocalCreate,
    TransferenciaEstoqueLocalCreate,
)


def test_openapi_expoe_transferencia_de_estoque() -> None:
    assert "/api/v1/pos/transferencias" in app.openapi()["paths"]


@pytest.mark.parametrize("desconto", [-1, 101])
def test_rejeita_limite_de_desconto_invalido(desconto: int) -> None:
    with pytest.raises(ValidationError):
        LocalVendaCreate(nome="Cantina", desconto_maximo_perc=desconto)


def test_rejeita_saldo_inicial_negativo() -> None:
    with pytest.raises(ValidationError):
        ProdutoLocalCreate(produto_id=1, estoque_atual=Decimal("-0.01"))


def test_rejeita_transferencia_sem_quantidade_positiva() -> None:
    with pytest.raises(ValidationError):
        TransferenciaEstoqueLocalCreate(
            produto_local_id=1,
            quantidade=Decimal("0"),
            data="2026-07-15",
        )

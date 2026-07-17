"""Testes de turnos de caixa e consolidação financeira do PDV."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.pos.finance_integration import POSFinanceIntegration
from app.pos.models import LocalVenda, TurnoCaixa, VendaMobile, PagamentoVenda
from app.core.models import Evento
from app.finance.models import CategoriaFinanceira, ContaCaixa


@pytest.mark.asyncio
@patch("weasyprint.HTML")
@patch("builtins.open")
@patch("os.makedirs")
async def test_consolidar_turno_e_fechar_sucesso(
    mock_makedirs, mock_open, mock_html
) -> None:
    session = AsyncMock(spec=AsyncSession)

    # Mock LocalVenda
    local = LocalVenda(
        id=1,
        evento_id=1,
        nome="Cantina",
        caixa_aberto=True,
        caixa_atual_turno_id=10,
    )
    
    # Mock TurnoCaixa
    turno = TurnoCaixa(
        id=10,
        local_id=1,
        evento_id=1,
        aberto_em=None,
        aberto_por_id=1,
        fechado=False,
    )

    # Mock Vendas
    venda1 = VendaMobile(id=1, total=Decimal("50.00"), turno_id=10)
    venda1.pagamentos = [PagamentoVenda(tipo="PIX", valor=Decimal("50.00"))]
    venda1.itens = []
    
    venda2 = VendaMobile(id=2, total=Decimal("30.00"), turno_id=10)
    venda2.pagamentos = [PagamentoVenda(tipo="DINHEIRO", valor=Decimal("30.00"))]
    venda2.itens = []

    # Mock Categoria and Conta
    categoria = CategoriaFinanceira(id=2, nome="Vendas PDV")
    conta = ContaCaixa(id=3, nome="Caixa PDV")

    # Mock execute results
    # 1. Lock LocalVenda
    mock_local_res = MagicMock()
    mock_local_res.scalar_one_or_none.return_value = local
    
    # 2. Get Vendas
    mock_vendas_res = MagicMock()
    mock_vendas_res.scalars.return_value.unique.return_value.all.return_value = [venda1, venda2]

    # 3. Items summary query
    mock_items_res = MagicMock()
    mock_items_res.all.return_value = [] # no items for simplicity

    session.execute.side_effect = [
        mock_local_res,      # local query
        mock_vendas_res,     # vendas query
        mock_items_res,      # items query
    ]

    async def mock_get(model, ident, **kwargs):
        if model == TurnoCaixa and ident == 10:
            return turno
        if model == Evento and ident == 1:
            return Evento(id=1, nome="Retiro das Rosas")
        return None
    session.get = mock_get

    with patch.object(
        POSFinanceIntegration, "_get_or_create_categoria_receita", return_value=categoria
    ), patch.object(
        POSFinanceIntegration, "_get_or_create_conta_caixa", return_value=conta
    ):
        result_local = await POSFinanceIntegration.consolidar_turno_e_fechar(
            session=session,
            local_id=1,
            user_id=9,
        )

        assert result_local.caixa_aberto is False
        assert result_local.caixa_atual_turno_id is None
        assert turno.fechado is True
        assert turno.fechado_por_id == 9
        assert turno.valor_fechamento == Decimal("80.00")
        assert turno.relatorio_pdf == "pos/fechamento_10.pdf"

        # Check mock pdf generation called
        mock_html.assert_called_once()
        mock_open.assert_called_once()

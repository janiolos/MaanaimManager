"""Integração do módulo POS com Finance.

Cria LancamentoFinanceiro de RECEITA automaticamente para cada venda do PDV.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro
from app.pos.models import VendaMobile
from app.pos.schemas import PagamentoIn


class POSFinanceIntegration:
    """Helper para gerar lançamentos financeiros a partir de vendas do PDV."""

    CATEGORIA_NOME = "Vendas PDV"
    CONTA_NOME = "Caixa PDV"

    # Mapeamento de formas do PDV → formas do financeiro
    FORMA_MAP = {
        "DINHEIRO": LancamentoFinanceiro.DINHEIRO,
        "PIX": LancamentoFinanceiro.PIX,
        "DÉBITO": LancamentoFinanceiro.CARTAO,
        "CRÉDITO": LancamentoFinanceiro.CARTAO,
        "MISTO": LancamentoFinanceiro.OUTRO,
    }

    @staticmethod
    async def _get_or_create_categoria_receita(session: AsyncSession) -> CategoriaFinanceira:
        stmt = select(CategoriaFinanceira).where(
            CategoriaFinanceira.tipo == CategoriaFinanceira.RECEITA,
            CategoriaFinanceira.nome == POSFinanceIntegration.CATEGORIA_NOME,
        )
        result = await session.execute(stmt)
        cat = result.scalars().first()
        if cat is None:
            # tenta qualquer categoria de receita
            stmt2 = select(CategoriaFinanceira).where(
                CategoriaFinanceira.tipo == CategoriaFinanceira.RECEITA
            ).order_by(CategoriaFinanceira.id)
            result2 = await session.execute(stmt2)
            cat = result2.scalars().first()
        if cat is None:
            cat = CategoriaFinanceira(nome=POSFinanceIntegration.CATEGORIA_NOME, tipo=CategoriaFinanceira.RECEITA)
            session.add(cat)
            await session.flush()
        return cat

    @staticmethod
    async def _get_or_create_conta_caixa(session: AsyncSession) -> ContaCaixa:
        stmt = select(ContaCaixa).where(
            ContaCaixa.nome == POSFinanceIntegration.CONTA_NOME,
            ContaCaixa.ativo.is_(True),
        )
        result = await session.execute(stmt)
        conta = result.scalars().first()
        if conta is None:
            stmt2 = select(ContaCaixa).where(ContaCaixa.ativo.is_(True)).order_by(ContaCaixa.id)
            result2 = await session.execute(stmt2)
            conta = result2.scalars().first()
        if conta is None:
            conta = ContaCaixa(nome=POSFinanceIntegration.CONTA_NOME, ativo=True)
            session.add(conta)
            await session.flush()
        return conta

    @staticmethod
    async def criar_lancamentos_da_venda(
        session: AsyncSession,
        venda: VendaMobile,
        pagamentos: list[PagamentoIn],
        local_nome: str,
        user_id: int,
    ) -> list[LancamentoFinanceiro]:
        """Cria um ou mais LancamentoFinanceiro de RECEITA para a venda.

        Agrupa pagamentos pela forma de pagamento mapeada e cria um lançamento
        por grupo.  Se todos os pagamentos são da mesma forma, cria um único
        lançamento.
        """
        categoria = await POSFinanceIntegration._get_or_create_categoria_receita(session)
        conta = await POSFinanceIntegration._get_or_create_conta_caixa(session)

        # Agrupa pagamentos por forma mapeada
        grupos: dict[str, Decimal] = {}
        for pgto in pagamentos:
            forma = POSFinanceIntegration.FORMA_MAP.get(pgto.tipo, LancamentoFinanceiro.OUTRO)
            grupos[forma] = grupos.get(forma, Decimal("0")) + Decimal(str(pgto.valor))

        lancamentos: list[LancamentoFinanceiro] = []
        hoje = date.today()

        for forma, valor in grupos.items():
            desc = (
                f"Venda PDV #{venda.id_referencia[:8]} — "
                f"Local: {local_nome} — "
                f"Forma: {forma}"
            )
            lanc = LancamentoFinanceiro(
                evento_id=venda.evento_id,
                tipo=LancamentoFinanceiro.RECEITA,
                categoria_id=categoria.id,
                conta_id=conta.id,
                data=hoje,
                descricao=desc,
                valor=valor,
                forma_pagamento=forma,
                criado_por_id=user_id,
                setor_origem="pos",
                pessoa=local_nome,
            )
            session.add(lanc)
            lancamentos.append(lanc)

        await session.flush()
        return lancamentos

    @staticmethod
    async def consolidar_turno_e_fechar(
        session: AsyncSession,
        local_id: int,
        user_id: int,
    ) -> LocalVenda:
        import os
        from datetime import datetime, UTC
        from weasyprint import HTML
        from sqlalchemy import select, func
        from sqlalchemy.orm import selectinload
        
        from app.pos.models import LocalVenda, TurnoCaixa, VendaMobile, PagamentoVenda, ItemVendaMobile
        from app.finance.models import LancamentoFinanceiro, AnexoLancamento
        from app.core.models import Evento, User
        
        # 1. Lock LocalVenda
        stmt_local = select(LocalVenda).where(LocalVenda.id == local_id).with_for_update()
        result_local = await session.execute(stmt_local)
        local = result_local.scalar_one_or_none()
        if not local:
            raise ValueError("Local de venda não encontrado")
        if not local.caixa_aberto or not local.caixa_atual_turno_id:
            raise ValueError("Caixa já está fechado")
            
        # 2. Get TurnoCaixa
        turno = await session.get(TurnoCaixa, local.caixa_atual_turno_id)
        if not turno:
            raise ValueError("Turno de caixa não encontrado")
            
        # Update closing info on TurnoCaixa
        turno.fechado_em = datetime.now(UTC)
        turno.fechado_por_id = user_id
        turno.fechado = True
        
        # Fetch Event name
        evento_nome = "Geral"
        evt_id = turno.evento_id or local.evento_id
        if evt_id:
            evt = await session.get(Evento, evt_id)
            if evt:
                evento_nome = evt.nome
                
        # 3. Get all sales for this turn
        stmt_vendas = (
            select(VendaMobile)
            .options(selectinload(VendaMobile.pagamentos), selectinload(VendaMobile.itens))
            .where(VendaMobile.turno_id == turno.id)
        )
        vendas = (await session.execute(stmt_vendas)).scalars().unique().all()
        
        total_vendas_sum = sum(v.total for v in vendas)
        turno.valor_fechamento = total_vendas_sum
        
        # Group payments by type
        por_forma = {}
        for v in vendas:
            for p in v.pagamentos:
                tipo_financeiro = POSFinanceIntegration.FORMA_MAP.get(p.tipo, LancamentoFinanceiro.OUTRO)
                por_forma[tipo_financeiro] = por_forma.get(tipo_financeiro, Decimal("0.00")) + p.valor
                
        # Get items summary
        stmt_items = (
            select(
                ItemVendaMobile.nome_produto,
                ItemVendaMobile.familia_produto,
                func.sum(ItemVendaMobile.quantidade).label("qtd"),
                func.sum(ItemVendaMobile.total_item).label("total")
            )
            .join(VendaMobile, ItemVendaMobile.venda_id == VendaMobile.id)
            .where(VendaMobile.turno_id == turno.id)
            .group_by(ItemVendaMobile.nome_produto, ItemVendaMobile.familia_produto)
            .order_by(ItemVendaMobile.nome_produto)
        )
        items_summary = (await session.execute(stmt_items)).all()
        
        # 4. Generate HTML and PDF
        # Formatting functions
        def format_currency(val) -> str:
            return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
        def format_datetime_br(dt) -> str:
            if not dt:
                return ""
            # simple BR formatting
            return dt.strftime("%d/%m/%Y %H:%M:%S")
            
        rows_forma = "".join(
            f"<tr><td>{forma}</td><td class='text-right'>{format_currency(valor)}</td></tr>"
            for forma, valor in por_forma.items() if valor > 0
        )
        if not rows_forma:
            rows_forma = "<tr><td colspan='2' style='text-align: center; color: #777;'>Nenhuma venda no período.</td></tr>"

        rows_items = "".join(
            f"<tr><td>{row[0]}</td><td>{row[1]}</td><td class='text-center'>{row[2]}</td><td class='text-right'>{format_currency(row[3])}</td></tr>"
            for row in items_summary
        )
        if not rows_items:
            rows_items = "<tr><td colspan='4' style='text-align: center; color: #777;'>Nenhum item vendido.</td></tr>"
            
        html_str = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <title>Fechamento de Caixa - {local.nome}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 2cm;
      @bottom-right {{
        content: "Página " counter(page) " de " counter(pages);
        font-size: 10pt;
        color: #666;
      }}
    }}
    body {{
      font-family: Arial, sans-serif;
      color: #333;
      font-size: 11pt;
    }}
    h1 {{
      color: #206bc4;
      text-align: center;
      margin-bottom: 5px;
    }}
    .header-info {{
      text-align: center;
      margin-bottom: 30px;
      color: #555;
      font-size: 10pt;
      border-bottom: 2px solid #206bc4;
      padding-bottom: 15px;
    }}
    .section-title {{
      font-size: 13pt;
      font-weight: bold;
      color: #206bc4;
      margin-top: 25px;
      margin-bottom: 10px;
      border-bottom: 1px solid #e0e0e0;
      padding-bottom: 5px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 20px;
      font-size: 10pt;
    }}
    th, td {{
      padding: 6px 8px;
      border-bottom: 1px solid #e0e0e0;
      text-align: left;
    }}
    th {{
      background-color: #f8f9fa;
      font-weight: bold;
    }}
    .text-right {{
      text-align: right;
    }}
    .text-center {{
      text-align: center;
    }}
    .text-strong {{
      font-weight: bold;
    }}
    .total-box {{
      background-color: #f8f9fa;
      border: 1px solid #e0e0e0;
      padding: 15px;
      margin-top: 30px;
      text-align: right;
      font-size: 12pt;
    }}
  </style>
</head>
<body>
  <h1>Relatório de Fechamento de Caixa</h1>
  <div class="header-info">
    <strong>PDV:</strong> {local.nome} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Evento:</strong> {evento_nome}<br>
    <strong>Turno:</strong> #{turno.id} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Status:</strong> FECHADO<br>
    <strong>Abertura:</strong> {format_datetime_br(turno.aberto_em)} ({turno.aberto_por.username if turno.aberto_por else 'Sistema'})<br>
    <strong>Fechamento:</strong> {format_datetime_br(turno.fechado_em)} ({turno.fechado_por.username if turno.fechado_por else 'Sistema'})
  </div>

  <div class="section-title">Resumo por Forma de Pagamento</div>
  <table>
    <thead>
      <tr>
        <th>Forma de Pagamento</th>
        <th class="text-right">Valor Total</th>
      </tr>
    </thead>
    <tbody>
      {rows_forma}
      <tr class="text-strong">
        <td>Total Geral</td>
        <td class="text-right">{format_currency(total_vendas_sum)}</td>
      </tr>
    </tbody>
  </table>

  <div class="section-title">Itens Vendidos (Consolidado)</div>
  <table>
    <thead>
      <tr>
        <th>Produto</th>
        <th>Família</th>
        <th class="text-center">Quantidade</th>
        <th class="text-right">Total</th>
      </tr>
    </thead>
    <tbody>
      {rows_items}
    </tbody>
  </table>

  <div class="total-box">
    <strong>Total do Caixa a Conciliar:</strong> <span class="text-strong" style="color: #2fb344; font-size: 14pt;">{format_currency(total_vendas_sum)}</span>
  </div>
</body>
</html>
"""
        # Render PDF via WeasyPrint
        pdf_bytes = HTML(string=html_str).write_pdf()
        
        # Save to media_dir/pos/fechamento_{turno.id}.pdf
        media_dir = "/app/media" if os.path.exists("/app/media") else "./media"
        pos_media_dir = os.path.join(media_dir, "pos")
        os.makedirs(pos_media_dir, exist_ok=True)
        
        pdf_filename = f"fechamento_{turno.id}.pdf"
        pdf_rel_path = f"pos/{pdf_filename}"
        pdf_full_path = os.path.join(pos_media_dir, pdf_filename)
        
        with open(pdf_full_path, "wb") as f:
            f.write(pdf_bytes)
            
        turno.relatorio_pdf = pdf_rel_path
        
        # 5. Create financial entries per payment method
        categoria = await POSFinanceIntegration._get_or_create_categoria_receita(session)
        conta = await POSFinanceIntegration._get_or_create_conta_caixa(session)
        
        hoje = datetime.now(UTC).date()
        
        for forma, valor in por_forma.items():
            if valor <= 0:
                continue
                
            desc = (
                f"Consolidação Fechamento Caixa {local.nome} — "
                f"Turno: #{turno.id} — "
                f"Forma: {forma}"
            )
            evt_id = turno.evento_id or local.evento_id
            if not evt_id:
                raise ValueError("Não foi possível fechar o caixa pois não há evento associado a este turno.")
                
            lanc = LancamentoFinanceiro(
                evento_id=evt_id,
                tipo=LancamentoFinanceiro.RECEITA,
                categoria_id=categoria.id,
                conta_id=conta.id,
                data=hoje,
                descricao=desc,
                valor=valor,
                forma_pagamento=forma,
                criado_por_id=user_id,
                setor_origem="pos",
                pessoa=local.nome,
            )
            session.add(lanc)
            await session.flush() # get lanc.id
            
            # Add attachment (AnexoLancamento) pointing to the PDF
            anexo = AnexoLancamento(
                lancamento_id=lanc.id,
                arquivo=pdf_rel_path,
                descricao=f"Relatório de Fechamento de Caixa - Turno #{turno.id}",
                enviado_por_id=user_id,
                enviado_em=datetime.now(UTC),
            )
            session.add(anexo)
            
        # 6. Reset LocalVenda state
        local.caixa_aberto = False
        local.caixa_aberto_em = None
        local.caixa_aberto_por_id = None
        local.caixa_atual_turno_id = None
        
        await session.flush()
        return local

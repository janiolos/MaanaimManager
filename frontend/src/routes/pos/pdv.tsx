import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLocais, useProdutosLocal, useCriarVenda, useFamilias, useAbrirCaixa, useFecharCaixa, usePosLocalAtual, useCaixaAtual } from "@/routes/pos/hooks";
import type { PagamentoPayload, ProdutoLocal } from "@/routes/pos/types";
import { PAGAMENTO_LABELS, PAGAMENTO_COLORS } from "@/routes/pos/types";
import { cn, formatBRL } from "@/lib/utils";
import { api } from "@/lib/api";
import { POSNav } from "./pos-nav";

interface CartItem {
  produtoLocal: ProdutoLocal;
  quantidade: number;
  descontoPerc: number;
}

type PagamentoTipo = "DINHEIRO" | "PIX" | "DÉBITO" | "CRÉDITO";

export function PDVPage() {
  const { data: locais } = useLocais();
  const { localId: localSelecionado, setLocalId: setLocalSelecionado } = usePosLocalAtual();
  const { data: produtos } = useProdutosLocal(localSelecionado ?? 0);
  const { data: familias } = useFamilias(localSelecionado ?? 0);
  const criarVenda = useCriarVenda();
  const abrirCaixa = useAbrirCaixa();
  const fecharCaixa = useFecharCaixa();
  const barcodeRef = useRef<HTMLInputElement>(null);

  const localAtual = useMemo(
    () => locais?.find((l) => l.id === localSelecionado),
    [locais, localSelecionado]
  );

  const { data: resumoCaixa } = useCaixaAtual(localSelecionado ?? 0);

  const [offlineVendas, setOfflineVendas] = useState<import("@/routes/pos/types").VendaPayload[]>(() => {
    try {
      const stored = localStorage.getItem("maanaim-offline-vendas");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    localStorage.setItem("maanaim-offline-vendas", JSON.stringify(offlineVendas));
  }, [offlineVendas]);

  const [cart, setCart] = useState<CartItem[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [barcodeTerm, setBarcodeTerm] = useState("");
  const [familiaFiltro, setFamiliaFiltro] = useState<string>("");
  const [pagamentos, setPagamentos] = useState<PagamentoPayload[]>([]);
  const [pagamentoTipo, setPagamentoTipo] = useState<PagamentoTipo>("DINHEIRO");
  const [clock, setClock] = useState(() => new Date());

  const total = useMemo(() => {
    return cart.reduce((acc, item) => {
      const preco = Number(item.produtoLocal.preco_venda) * item.quantidade;
      const desc = preco * (item.descontoPerc / 100);
      return acc + (preco - desc);
    }, 0);
  }, [cart]);

  const totalPagamentos = useMemo(
    () => pagamentos.reduce((acc, p) => acc + Number(p.valor), 0),
    [pagamentos]
  );

  const diferenca = total - totalPagamentos;
  const troco = Math.max(0, totalPagamentos - total);
  const itemAtivo = cart.at(-1);

  const produtosFiltrados = useMemo(() => {
    if (!produtos) return [];
    return produtos.filter(
      (p) =>
        p.ativo &&
        (p.produto_nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.produto_sku.toLowerCase().includes(searchTerm.toLowerCase())) &&
        (familiaFiltro === "" || p.familia_nome === familiaFiltro)
    );
  }, [produtos, searchTerm, familiaFiltro]);

  const addToCart = useCallback(
    (pl: ProdutoLocal) => {
      setCart((prev) => {
        const idx = prev.findIndex((c) => c.produtoLocal.id === pl.id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = { ...next[idx], quantidade: next[idx].quantidade + 1 };
          return next;
        }
        return [...prev, { produtoLocal: pl, quantidade: 1, descontoPerc: 0 }];
      });
    },
    []
  );

  const buscarPorBarcode = useCallback(
    (codigo: string) => {
      if (!produtos || !codigo.trim()) return;
      const encontrado = produtos.find(
        (p) =>
          p.ativo &&
          (p.produto_sku.toLowerCase() === codigo.toLowerCase() ||
            String(p.produto_id) === codigo)
      );
      if (encontrado) {
        addToCart(encontrado);
        setBarcodeTerm("");
        barcodeRef.current?.focus();
      } else {
        toast.error("Produto não encontrado");
      }
    },
    [produtos, addToCart]
  );

  const updateQty = useCallback((idx: number, qty: number) => {
    setCart((prev) => {
      if (qty <= 0) return prev.filter((_, i) => i !== idx);
      const next = [...prev];
      next[idx] = { ...next[idx], quantidade: qty };
      return next;
    });
  }, []);

  const updateDesconto = useCallback((idx: number, desc: number) => {
    setCart((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], descontoPerc: desc };
      return next;
    });
  }, []);

  const addPagamento = useCallback(() => {
    if (diferenca <= 0) return;
    setPagamentos((prev) => [
      ...prev,
      { tipo: pagamentoTipo, valor: diferenca.toFixed(2) },
    ]);
  }, [diferenca, pagamentoTipo]);

  const limparVenda = useCallback(() => {
    setCart([]);
    setPagamentos([]);
    setSearchTerm("");
    setBarcodeTerm("");
    barcodeRef.current?.focus();
  }, []);

  const removePagamento = useCallback((idx: number) => {
    setPagamentos((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const updatePagamentoValor = useCallback((idx: number, valor: string) => {
    setPagamentos((prev) => {
      const next = [...prev];
      next[idx] = { ...next[idx], valor };
      return next;
    });
  }, []);

  const imprimirExtrato = useCallback((venda: any) => {
    const win = window.open("", "_blank", "width=400,height=600");
    if (!win) return;
    const localNome = locais?.find((l) => l.id === localSelecionado)?.nome ?? "PDV";
    const html = `
      <html><head><title>Extrato #${venda.id}</title></head>
      <body style="font-family:monospace;width:300px;margin:0 auto;color:#000;padding:16px;">
        <h3 style="text-align:center;margin-bottom:4px;font-size:16px;">${localNome}</h3>
        <p style="text-align:center;margin-top:0;font-size:12px;">
          ${new Date(venda.data_hora).toLocaleString("pt-BR")}<br>
          Cupom Não Fiscal — Ref: ${venda.id_referencia.slice(0, 8)}
        </p>
        <hr style="border-top:1px dashed #000;margin:8px 0;">
        <table style="width:100%;font-size:12px;">
          <thead><tr><th style="text-align:left;">Item</th><th>Qtd</th><th style="text-align:right;">Total</th></tr></thead>
          <tbody>
            ${venda.itens
              .map(
                (i: any) =>
                  `<tr>
                    <td style="text-align:left;">${i.nome_produto}</td>
                    <td style="text-align:center;">${i.quantidade}</td>
                    <td style="text-align:right;">${formatBRL(Number(i.total_item))}</td>
                  </tr>`
              )
              .join("")}
          </tbody>
        </table>
        <hr style="border-top:1px dashed #000;margin:8px 0;">
        <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:14px;">
          <span>TOTAL</span>
          <span>${formatBRL(Number(venda.total))}</span>
        </div>
        <div style="margin-top:8px;font-size:11px;">
          ${venda.pagamentos
            .map(
              (p: any) =>
                `<div style="display:flex;justify-content:space-between;">
                  <span>${PAGAMENTO_LABELS[p.tipo] ?? p.tipo}</span>
                  <span>${formatBRL(Number(p.valor))}</span>
                </div>`
            )
            .join("")}
        </div>
      </body></html>
    `;
    win.document.write(html);
    win.document.close();
    setTimeout(() => win.print(), 250);
  }, [locais, localSelecionado]);

  const sincronizarOffline = useCallback(async () => {
    if (offlineVendas.length === 0 || syncing) return;
    setSyncing(true);
    let sucessos = 0;
    const falhas: import("@/routes/pos/types").VendaPayload[] = [];

    for (const venda of offlineVendas) {
      try {
        await api.post("/pos/vendas", venda);
        sucessos++;
      } catch (err) {
        falhas.push(venda);
      }
    }

    setOfflineVendas(falhas);
    setSyncing(false);

    if (sucessos > 0) {
      toast.success(`${sucessos} venda(s) offline sincronizada(s) com sucesso!`);
    }
    if (falhas.length > 0) {
      toast.error(`Falha ao sincronizar ${falhas.length} venda(s). Verifique sua conexão.`);
    }
  }, [offlineVendas, syncing]);

  const imprimirFechamento = useCallback(() => {
    if (!resumoCaixa) return;
    const win = window.open("", "_blank", "width=400,height=600");
    if (!win) return;
    const localNome = locais?.find((l) => l.id === localSelecionado)?.nome ?? "PDV";
    const formasHtml = Object.entries(resumoCaixa.por_forma)
      .map(
        ([forma, valor]) =>
          `<div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span>${PAGAMENTO_LABELS[forma] ?? forma}</span>
            <span>${formatBRL(valor)}</span>
          </div>`
      )
      .join("");

    const html = `
      <html><head><title>Fechamento de Caixa — ${localNome}</title></head>
      <body style="font-family:monospace;width:300px;margin:0 auto;color:#000;padding:16px;">
        <h3 style="text-align:center;margin-bottom:4px;font-size:16px;">FECHAMENTO DE CAIXA</h3>
        <h4 style="text-align:center;margin-top:0;font-size:14px;">${localNome}</h4>
        <p style="text-align:center;font-size:11px;">
          Aberto em: ${resumoCaixa.aberto_em ? new Date(resumoCaixa.aberto_em).toLocaleString("pt-BR") : "N/A"}<br>
          Gerado em: ${new Date().toLocaleString("pt-BR")}
        </p>
        <hr style="border-top:1px dashed #000;margin:8px 0;">
        <div style="font-size:12px;">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span>Qtd Vendas:</span>
            <span>${resumoCaixa.total_vendas}</span>
          </div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px;font-weight:bold;">
            <span>Total Geral:</span>
            <span>${formatBRL(resumoCaixa.soma_total)}</span>
          </div>
        </div>
        <hr style="border-top:1px dashed #000;margin:8px 0;">
        <h5 style="margin:8px 0 4px 0;font-size:12px;text-align:left;">RESUMO POR FORMA DE PAGAMENTO</h5>
        <div style="font-size:11px;">
          ${formasHtml || '<div style="text-align:center;color:#666;">Nenhuma venda realizada</div>'}
        </div>
        <hr style="border-top:1px dashed #000;margin:16px 0 24px 0;">
        <div style="text-align:center;font-size:10px;margin-top:16px;">
          __________________________________<br>
          Assinatura do Operador
        </div>
      </body></html>
    `;
    win.document.write(html);
    win.document.close();
    setTimeout(() => win.print(), 250);
  }, [resumoCaixa, locais, localSelecionado]);

  const confirmarVenda = useCallback(async () => {
    if (cart.length === 0) return toast.error("Carrinho vazio");
    if (diferenca > 0.01) return toast.error("Pagamentos não conferem com o total");

    let restante = total;
    const pagamentosEfetivos = pagamentos
      .map((p) => {
        const valorInformado = Number(p.valor);
        const valorEfetivo = Math.min(valorInformado, Math.max(restante, 0));
        restante -= valorEfetivo;
        return { tipo: p.tipo, valor: valorEfetivo.toFixed(2) };
      })
      .filter((p) => Number(p.valor) > 0);

    const payload: import("@/routes/pos/types").VendaPayload = {
      local_id: localSelecionado,
      id_referencia: crypto.randomUUID(),
      itens: cart.map((c) => ({
        produto_local_id: c.produtoLocal.id,
        nome_produto: c.produtoLocal.produto_nome,
        codigo_produto: c.produtoLocal.produto_sku,
        familia_produto: c.produtoLocal.familia_nome,
        quantidade: c.quantidade,
        preco_unitario: c.produtoLocal.preco_venda,
        desconto_perc: String(c.descontoPerc),
      })),
      pagamentos: pagamentosEfetivos,
    };

    try {
      const venda = await criarVenda.mutateAsync(payload);
      toast.success(`Venda #${payload.id_referencia.slice(0, 8)} confirmada!`);
      imprimirExtrato(venda);
      setCart([]);
      setPagamentos([]);
    } catch (err: any) {
      const isNetworkError = !err.response || err.code === "ERR_NETWORK" || !navigator.onLine;
      if (isNetworkError) {
        setOfflineVendas((prev) => [...prev, payload]);
        toast.warning(`Sem conexão com o servidor. Venda #${payload.id_referencia.slice(0, 8)} salva offline.`);
        setCart([]);
        setPagamentos([]);
      } else {
        toast.error(err?.response?.data?.detail || "Erro ao registrar venda");
      }
    }
  }, [cart, pagamentos, diferenca, total, localSelecionado, criarVenda, imprimirExtrato, offlineVendas]);

  useEffect(() => {
    if (localSelecionado) {
      barcodeRef.current?.focus();
    }
  }, [localSelecionado]);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="space-y-4">
      <POSNav />
      <div className="min-h-[calc(100vh-13rem)] overflow-hidden rounded-md border border-slate-300 bg-[#e8ebef] p-2 text-slate-950 shadow-mm">
        <div className="flex items-stretch justify-between gap-3">
          <div className="flex min-h-12 flex-1 items-center justify-center rounded-br-2xl border-b-2 border-r-2 border-white bg-[#1c276a] px-4">
            <h1 className="text-center text-lg font-black uppercase text-[#d62828] [text-shadow:1px_1px_2px_#000]">
              PDV Maanaim
            </h1>
          </div>
          <div className="flex min-w-44 items-center justify-center rounded-bl-2xl border-b-2 border-l-2 border-white bg-[#1c276a] px-5">
            <span className="font-mono text-xl font-black text-[#ffcc00]">
              {clock.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
            </span>
          </div>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs font-bold">
          <label className="flex items-center gap-2">
            Local
            <select
              className="h-8 rounded border border-slate-400 bg-white px-2 text-xs"
              value={localSelecionado ?? ""}
              onChange={(e) => {
                setLocalSelecionado(Number(e.target.value) || null);
                limparVenda();
              }}
            >
              <option value="">Selecione...</option>
              {locais?.filter((l) => l.modulo_pdv && l.ativo).map((l) => (
                <option key={l.id} value={l.id}>{l.nome}</option>
              ))}
            </select>
          </label>

          {localAtual?.caixa_aberto ? (
            <Badge className="border-emerald-200 bg-emerald-500/20 text-emerald-700">Caixa aberto</Badge>
          ) : (
            <Badge variant="destructive">Caixa fechado</Badge>
          )}

          {localAtual && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={localAtual.caixa_aberto ? "outline" : "default"}
                className={cn("h-8 text-xs", !localAtual.caixa_aberto && "bg-mm-accent text-white")}
                onClick={async () => {
                  try {
                    if (localAtual.caixa_aberto) {
                      const turnoId = localAtual.caixa_atual_turno_id;
                      await fecharCaixa.mutateAsync(localAtual.id);
                      toast.success("Caixa fechado com sucesso!");
                      if (turnoId) {
                        window.open(`/media/pos/fechamento_${turnoId}.pdf`, "_blank");
                      }
                    } else {
                      await abrirCaixa.mutateAsync(localAtual.id);
                      toast.success("Caixa aberto");
                    }
                  } catch (err: any) {
                    toast.error(err?.response?.data?.detail || "Erro ao atualizar caixa");
                  }
                }}
                disabled={abrirCaixa.isPending || fecharCaixa.isPending}
              >
                {localAtual.caixa_aberto ? "Fechar caixa" : "Abrir caixa"}
              </Button>

              {localAtual.caixa_aberto && (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-8 text-xs border-slate-400 text-slate-800 bg-white hover:bg-slate-100"
                  onClick={imprimirFechamento}
                  disabled={!resumoCaixa}
                >
                  Relatório Turno
                </Button>
              )}
            </div>
          )}

          {offlineVendas.length > 0 && (
            <Button
              size="sm"
              variant="destructive"
              className="h-8 text-xs bg-amber-600 hover:bg-amber-700 text-white animate-pulse"
              onClick={sincronizarOffline}
              disabled={syncing}
            >
              {syncing ? "Sincronizando..." : `Sincronizar (${offlineVendas.length}) Vendas Offline`}
            </Button>
          )}

          <span className="ml-auto text-slate-600">
            {cart.length} item(ns) no cupom
          </span>
        </div>

        <div className="mt-2 flex min-h-[520px] flex-col gap-3 lg:flex-row">
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <div className="flex min-h-20 overflow-hidden rounded-md border-2 border-white bg-[#1c276a] text-white">
              <div className="flex w-24 items-center justify-center border-r-2 border-white text-3xl font-black">
                {itemAtivo?.quantidade ?? 0}
              </div>
              <div className="flex flex-1 items-center px-4 text-2xl font-black uppercase">
                {itemAtivo?.produtoLocal.produto_nome ?? "Aguardando produto"}
              </div>
            </div>

            <div className="grid gap-3 rounded-md border border-slate-300 bg-white p-3 md:grid-cols-[1fr_1fr_180px]">
              <div className="space-y-1">
                <Label className="text-xs font-bold uppercase text-slate-700">Codigo / SKU / ID</Label>
                <Input
                  ref={barcodeRef}
                  className="h-11 border-2 border-slate-400 text-base font-semibold"
                  placeholder="Leia o codigo ou digite o ID"
                  value={barcodeTerm}
                  onChange={(e) => setBarcodeTerm(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      buscarPorBarcode(barcodeTerm);
                    }
                  }}
                  disabled={!localSelecionado}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-bold uppercase text-slate-700">Buscar produto</Label>
                <Input
                  className="h-11 border-2 border-slate-400 text-base"
                  placeholder="Nome ou SKU"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  disabled={!localSelecionado}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs font-bold uppercase text-slate-700">Familia</Label>
                <select
                  className="h-11 w-full rounded-md border-2 border-slate-400 bg-white px-3 text-sm"
                  value={familiaFiltro}
                  onChange={(e) => setFamiliaFiltro(e.target.value)}
                  disabled={!localSelecionado}
                >
                  <option value="">Todas</option>
                  {familias?.map((f) => (
                    <option key={f.id} value={f.nome}>{f.nome}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid flex-1 auto-rows-min grid-cols-2 gap-2 overflow-y-auto rounded-md border border-slate-300 bg-white p-2 md:grid-cols-3 xl:grid-cols-4">
              {!localSelecionado && (
                <p className="col-span-full py-10 text-center text-sm text-slate-500">
                  Selecione um local para carregar produtos.
                </p>
              )}
              {localSelecionado && produtosFiltrados.length === 0 && (
                <p className="col-span-full py-10 text-center text-sm text-slate-500">
                  Nenhum produto encontrado.
                </p>
              )}
              {produtosFiltrados.map((pl) => {
                const estAtual = Number(pl.estoque_atual);
                const estMin = Number(pl.estoque_minimo);
                const isEstoqueBaixo = estAtual > 0 && estAtual <= estMin;

                return (
                  <button
                    key={pl.id}
                    onClick={() => addToCart(pl)}
                    className={cn(
                      "relative min-h-28 rounded border border-slate-300 bg-[#f8fafc] p-2 text-left transition hover:border-[#1c276a] hover:bg-[#eef6ff]",
                      estAtual <= 0 && "cursor-not-allowed opacity-40"
                    )}
                    disabled={estAtual <= 0}
                  >
                    {isEstoqueBaixo && (
                      <span className="absolute right-1 top-1 rounded bg-amber-500 px-1 py-0.5 text-[9px] font-bold text-white uppercase shadow-sm">
                        Baixo
                      </span>
                    )}
                    <p className="truncate text-sm font-bold pr-8">{pl.produto_nome}</p>
                    <p className="mt-1 text-xs text-slate-500">{pl.produto_sku}</p>
                    <p className="mt-2 text-base font-black text-[#1c276a]">{formatBRL(Number(pl.preco_venda))}</p>
                    <p className="text-xs text-slate-500">Estoque: {pl.estoque_atual}</p>
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-3 gap-2">
              <Button variant="outline" className="h-11 border-[#1c276a] bg-[#1c276a] text-white hover:bg-[#25338b]" onClick={limparVenda}>
                Nova venda
              </Button>
              <Button variant="outline" className="h-11" onClick={() => barcodeRef.current?.focus()}>
                Focar codigo
              </Button>
              <Button variant="outline" className="h-11" onClick={() => setSearchTerm("")}>
                Limpar busca
              </Button>
            </div>
          </div>

          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <div className="min-h-0 flex-1 overflow-auto rounded-md border-2 border-slate-400 bg-white">
              <table className="w-full border-collapse text-xs">
                <thead className="sticky top-0 bg-slate-200">
                  <tr>
                    <th className="border border-slate-300 px-2 py-2 text-left">Item</th>
                    <th className="border border-slate-300 px-2 py-2">Qtd</th>
                    <th className="border border-slate-300 px-2 py-2">Unit.</th>
                    <th className="border border-slate-300 px-2 py-2">Desc.</th>
                    <th className="border border-slate-300 px-2 py-2 text-right">Total</th>
                    <th className="border border-slate-300 px-2 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {cart.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-16 text-center text-sm text-slate-500">
                        Cupom vazio
                      </td>
                    </tr>
                  )}
                  {cart.map((item, idx) => {
                    const sub = Number(item.produtoLocal.preco_venda) * item.quantidade;
                    const desc = sub * (item.descontoPerc / 100);
                    return (
                      <tr key={item.produtoLocal.id} className={idx === cart.length - 1 ? "bg-[#a8d5ff] font-semibold" : undefined}>
                        <td className="border border-slate-200 px-2 py-2">
                          <p className="max-w-64 truncate">{item.produtoLocal.produto_nome}</p>
                          <p className="text-[10px] text-slate-500">{item.produtoLocal.produto_sku}</p>
                        </td>
                        <td className="border border-slate-200 px-2 py-2">
                          <div className="flex items-center justify-center gap-1">
                            <Button size="sm" variant="outline" className="h-6 w-6 p-0" onClick={() => updateQty(idx, item.quantidade - 1)}>-</Button>
                            <span className="w-7 text-center">{item.quantidade}</span>
                            <Button size="sm" variant="outline" className="h-6 w-6 p-0" onClick={() => updateQty(idx, item.quantidade + 1)}>+</Button>
                          </div>
                        </td>
                        <td className="border border-slate-200 px-2 py-2 text-right">{formatBRL(Number(item.produtoLocal.preco_venda))}</td>
                        <td className="border border-slate-200 px-2 py-2">
                          <Input
                            type="number"
                            className="h-7 w-16 px-1 text-xs"
                            value={item.descontoPerc}
                            onChange={(e) => updateDesconto(idx, Number(e.target.value))}
                            min={0}
                            max={100}
                          />
                        </td>
                        <td className="border border-slate-200 px-2 py-2 text-right font-bold">{formatBRL(sub - desc)}</td>
                        <td className="border border-slate-200 px-2 py-2 text-center">
                          <Button size="sm" variant="ghost" className="h-7 px-2 text-destructive" onClick={() => updateQty(idx, 0)}>
                            x
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="grid gap-2 rounded-md border border-slate-300 bg-white p-3 md:grid-cols-[1fr_210px]">
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  {(["DINHEIRO", "PIX", "DÉBITO", "CRÉDITO"] as const).map((t) => (
                    <Button
                      key={t}
                      size="sm"
                      variant={pagamentoTipo === t ? "default" : "outline"}
                      onClick={() => setPagamentoTipo(t)}
                      className={cn("h-8 text-xs", pagamentoTipo === t && "bg-[#1c276a] text-white")}
                    >
                      {PAGAMENTO_LABELS[t]}
                    </Button>
                  ))}
                  <Button size="sm" variant="outline" className="h-8" onClick={addPagamento} disabled={diferenca <= 0.01}>
                    Adicionar restante
                  </Button>
                </div>
                <div className="space-y-1">
                  {pagamentos.length === 0 && (
                    <p className="text-xs text-slate-500">Nenhum pagamento informado.</p>
                  )}
                  {pagamentos.map((p, i) => (
                    <div key={`${p.tipo}-${i}`} className="flex items-center gap-2">
                      <Badge className={cn("min-w-20 justify-center text-xs", PAGAMENTO_COLORS[p.tipo])}>
                        {PAGAMENTO_LABELS[p.tipo]}
                      </Badge>
                      <Input
                        type="number"
                        className="h-8 max-w-40"
                        value={p.valor}
                        onChange={(e) => updatePagamentoValor(i, e.target.value)}
                        min={0}
                        step={0.01}
                      />
                      <Button size="sm" variant="ghost" className="h-8 px-2 text-destructive" onClick={() => removePagamento(i)}>
                        x
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex h-11 items-center justify-between rounded border-2 border-slate-800 bg-white px-3">
                  <span className="text-sm font-black uppercase">Total</span>
                  <span className="font-mono text-2xl font-black">{formatBRL(total)}</span>
                </div>
                <div className="flex h-10 items-center justify-between rounded border border-slate-400 bg-white px-3">
                  <span className="text-xs font-bold uppercase">Pago</span>
                  <span className="font-mono text-lg font-bold">{formatBRL(totalPagamentos)}</span>
                </div>
                <div className="flex h-10 items-center justify-between rounded border border-slate-400 bg-white px-3">
                  <span className="text-xs font-bold uppercase">{diferenca > 0 ? "Falta" : "Troco"}</span>
                  <span className={cn("font-mono text-lg font-bold", diferenca > 0.01 ? "text-destructive" : "text-emerald-700")}>
                    {formatBRL(diferenca > 0 ? diferenca : troco)}
                  </span>
                </div>
                {!localAtual?.caixa_aberto && (
                  <p className="text-center text-xs font-semibold text-destructive">Caixa fechado</p>
                )}
                <Button
                  className="h-12 w-full bg-mm-accent text-white hover:bg-mm-accent/90"
                  disabled={cart.length === 0 || diferenca > 0.01 || criarVenda.isPending || !localAtual?.caixa_aberto}
                  onClick={confirmarVenda}
                >
                  {criarVenda.isPending ? "Processando..." : "Finalizar venda"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

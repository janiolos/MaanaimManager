import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Plus } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { formatBRL, formatDateTime } from "@/lib/utils";
import { useCategorias, useContas } from "@/routes/finance/hooks";
import { useFornecedores } from "@/routes/inventory/hooks";
import type { PaginatedCotacoes } from "@/routes/inventory/types";
import { COTACAO_STATUS_LABELS, FORMA_PAGAMENTO_LABELS } from "@/routes/inventory/types";

export function CotacoesListPage() {
  const { data, refetch } = useQuery<PaginatedCotacoes>({
    queryKey: ["inventory", "cotacoes"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedCotacoes>("/inventory/cotacoes", {
        params: { page: 1, page_size: 50 },
      });
      return data;
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold font-display">Cotações de compra</h1>
          <p className="text-sm text-mm-muted">{data?.total ?? 0} cotação(ões)</p>
        </div>
        <Button asChild>
          <Link to="/inventory/cotacoes/novo">
            <Plus className="mr-2" size={16} /> Nova cotação
          </Link>
        </Button>
      </div>

      <div className="space-y-3">
        {data?.items.map((c) => (
          <CotacaoCard key={c.id} cotacao={c} onAction={() => refetch()} />
        ))}
        {data?.items.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-mm-muted">
              Nenhuma cotação neste evento.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function CotacaoCard({ cotacao, onAction }: { cotacao: PaginatedCotacoes["items"][0]; onAction: () => void }) {
  const [abrindo, setAbrindo] = useState(false);

  async function fechar() {
    if (!confirm("Fechar cotação? Depois disso só poderá aprovar.")) return;
    try {
      await api.post(`/inventory/cotacoes/${cotacao.id}/fechar`);
      toast.success("Cotação fechada");
      onAction();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao fechar");
    }
  }

  async function cancelar() {
    if (!confirm("Cancelar cotação?")) return;
    try {
      await api.post(`/inventory/cotacoes/${cotacao.id}/cancelar`);
      toast.success("Cotação cancelada");
      onAction();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao cancelar");
    }
  }

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm">{cotacao.numero}</span>
              <Badge
                variant={
                  cotacao.status === "FECHADA"
                    ? "success"
                    : cotacao.status === "CANCELADA"
                    ? "destructive"
                    : "secondary"
                }
              >
                {COTACAO_STATUS_LABELS[cotacao.status] ?? cotacao.status}
              </Badge>
            </div>
            <p className="text-xs text-mm-muted mt-1">
              {formatDateTime(cotacao.criado_em)} · {cotacao.itens.length} item(s)
            </p>
            {cotacao.observacao && <p className="text-sm mt-2">{cotacao.observacao}</p>}
            {cotacao.fornecedor_aprovado_id !== null && cotacao.valor_aprovado !== null && (
              <p className="text-sm mt-2 font-mono">
                Aprovado: {formatBRL(cotacao.valor_aprovado)}
              </p>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {cotacao.status === "ABERTA" && (
              <>
                <Button asChild variant="outline" size="sm">
                  <Link to={`/inventory/cotacoes/${cotacao.id}/editar`}>Editar</Link>
                </Button>
                <Button size="sm" variant="secondary" onClick={fechar}>
                  Fechar
                </Button>
                <Button size="sm" variant="destructive" onClick={cancelar}>
                  Cancelar
                </Button>
              </>
            )}
            {cotacao.status === "ABERTA" && (
              <Button size="sm" onClick={() => setAbrindo(true)}>
                <CheckCircle2 className="mr-2" size={14} /> Aprovar...
              </Button>
            )}
          </div>
        </div>
        {abrindo && <AprovarDialog cotacao={cotacao} onDone={() => { setAbrindo(false); onAction(); }} onCancel={() => setAbrindo(false)} />}
      </CardContent>
    </Card>
  );
}

function AprovarDialog({ cotacao, onDone, onCancel }: {
  cotacao: PaginatedCotacoes["items"][0];
  onDone: () => void;
  onCancel: () => void;
}) {
  const { data: fornecedores } = useFornecedores();
  const { data: categorias } = useCategorias("DESPESA");
  const { data: contas } = useContas();

  // fornecedores que têm preços para todos os itens
  const fornecedoresCompativeis = (fornecedores ?? []).filter((f) => {
    return cotacao.itens.every((it) => it.precos.some((p) => p.fornecedor_id === f.id));
  });

  const [fornecedorId, setFornecedorId] = useState<string>("");
  const [categoriaId, setCategoriaId] = useState<string>("");
  const [contaId, setContaId] = useState<string>("");
  const [forma, setForma] = useState("DINHEIRO");
  const [data, setData] = useState(new Date().toISOString().slice(0, 10));
  const [saving, setSaving] = useState(false);

  async function aprovar() {
    if (!fornecedorId || !categoriaId || !contaId) {
      toast.error("Preencha todos os campos");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/inventory/cotacoes/${cotacao.id}/aprovar`, {
        fornecedor_id: Number(fornecedorId),
        categoria_despesa_id: Number(categoriaId),
        conta_id: Number(contaId),
        forma_pagamento: forma,
        data,
      });
      toast.success("Cotação aprovada - LancamentoFinanceiro + OrdemCompra + entrada em estoque criados");
      onDone();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao aprovar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-4 p-4 rounded-md border border-mm-accent/40 bg-mm-accent/5">
      <p className="text-sm font-medium mb-3">Aprovação - cria despesa financeira + ordem de compra + entrada em estoque</p>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="space-y-1.5">
          <Label className="text-xs">Fornecedor</Label>
          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={fornecedorId} onChange={(e) => setFornecedorId(e.target.value)}>
            <option value="">Selecione...</option>
            {fornecedoresCompativeis.map((f) => (
              <option key={f.id} value={f.id}>{f.nome}</option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Categoria (despesa)</Label>
          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)}>
            <option value="">Selecione...</option>
            {categorias?.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Conta</Label>
          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={contaId} onChange={(e) => setContaId(e.target.value)}>
            <option value="">Selecione...</option>
            {contas?.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Forma de pagamento</Label>
          <select className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={forma} onChange={(e) => setForma(e.target.value)}>
            {Object.entries(FORMA_PAGAMENTO_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Data</Label>
          <Input type="date" value={data} onChange={(e) => setData(e.target.value)} />
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-3">
        <Button variant="outline" size="sm" onClick={onCancel}>Cancelar</Button>
        <Button size="sm" onClick={aprovar} disabled={saving}>
          {saving ? "Aprovando..." : "Aprovar e gerar documentos"}
        </Button>
      </div>
    </div>
  );
}
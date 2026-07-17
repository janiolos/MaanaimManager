import { useState } from "react";
import { toast } from "sonner";
import { Plus, Settings, Tags, Package, ArrowRight, ShoppingCart, BarChart3, Boxes } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLocais, useCriarLocal, useAtualizarLocal, usePosLocalAtual } from "@/routes/pos/hooks";
import { POSNav } from "./pos-nav";
import { Link } from "react-router-dom";

export function LocaisListPage() {
  const { data: locais, isLoading } = useLocais();
  const { localId: localAtualId, setLocalId: setLocalAtualId } = usePosLocalAtual();
  const criarLocal = useCriarLocal();
  const atualizarLocal = useAtualizarLocal();

  const [novoNome, setNovoNome] = useState("");
  const [editando, setEditando] = useState<number | null>(null);
  const [editNome, setEditNome] = useState("");

  const handleCriar = async () => {
    if (!novoNome.trim()) return toast.error("Informe o nome do local");
    try {
      await criarLocal.mutateAsync({ nome: novoNome.trim() });
      setNovoNome("");
      toast.success("Local criado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar local");
    }
  };

  const toggleField = async (local: any, field: string, value: boolean | number) => {
    try {
      await atualizarLocal.mutateAsync({ id: local.id, payload: { [field]: value } });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao atualizar");
    }
  };

  const salvarNome = async (id: number) => {
    if (!editNome.trim()) return;
    try {
      await atualizarLocal.mutateAsync({ id, payload: { nome: editNome.trim() } });
      setEditando(null);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao renomear");
    }
  };

  return (
    <div className="space-y-4">
      <POSNav />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Locais de Venda</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Novo Local</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input
            placeholder="Nome do local (ex: Cantina)"
            value={novoNome}
            onChange={(e) => setNovoNome(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCriar()}
          />
          <Button onClick={handleCriar} disabled={criarLocal.isPending}>
            <Plus className="h-4 w-4 mr-1" /> Criar
          </Button>
        </CardContent>
      </Card>

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {locais?.filter((l) => !l.is_deposito_interno).map((local) => (
          <Card key={local.id} className={localAtualId === local.id ? "ring-2 ring-mm-accent" : undefined}>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                {editando === local.id ? (
                  <div className="flex gap-2 flex-1">
                    <Input
                      value={editNome}
                      onChange={(e) => setEditNome(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") salvarNome(local.id);
                        if (e.key === "Escape") setEditando(null);
                      }}
                      autoFocus
                    />
                    <Button size="sm" onClick={() => salvarNome(local.id)}>Salvar</Button>
                  </div>
                ) : (
                  <>
                    <CardTitle className="text-base">{local.nome}</CardTitle>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" asChild>
                        <Link to={`/pos/locais/${local.id}/familias`}>
                          <Tags className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button size="sm" variant="ghost" asChild>
                        <Link to={`/pos/locais/${local.id}/produtos`}>
                          <Package className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setEditando(local.id);
                          setEditNome(local.nome);
                        }}
                      >
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between rounded-md border border-border bg-muted/30 p-2">
                <div>
                  <p className="text-xs text-mm-muted">Local operacional do POS</p>
                  <p className="text-sm font-medium">
                    {localAtualId === local.id ? "Selecionado" : "Não selecionado"}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant={localAtualId === local.id ? "outline" : "default"}
                  className={localAtualId === local.id ? undefined : "bg-mm-accent text-white"}
                  onClick={() => setLocalAtualId(local.id)}
                >
                  {localAtualId === local.id ? "Atual" : "Selecionar"}
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-2 text-sm">
                <ToggleRow
                  label="Ativo"
                  value={local.ativo}
                  onChange={(v) => toggleField(local, "ativo", v)}
                />
                <ToggleRow
                  label="Dashboard"
                  value={local.modulo_dashboard}
                  onChange={(v) => toggleField(local, "modulo_dashboard", v)}
                />
                <ToggleRow
                  label="PDV (Caixa)"
                  value={local.modulo_pdv}
                  onChange={(v) => toggleField(local, "modulo_pdv", v)}
                />
                <ToggleRow
                  label="Vendas"
                  value={local.modulo_vendas}
                  onChange={(v) => toggleField(local, "modulo_vendas", v)}
                />
                <ToggleRow
                  label="Produtos"
                  value={local.modulo_produtos}
                  onChange={(v) => toggleField(local, "modulo_produtos", v)}
                />
                <ToggleRow
                  label="Estoque"
                  value={local.modulo_estoque}
                  onChange={(v) => toggleField(local, "modulo_estoque", v)}
                />
                <ToggleRow
                  label="Desconto"
                  value={local.permite_desconto}
                  onChange={(v) => toggleField(local, "permite_desconto", v)}
                />
                <ToggleRow
                  label="Pagamento Misto"
                  value={local.permite_pagamento_misto}
                  onChange={(v) => toggleField(local, "permite_pagamento_misto", v)}
                />
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2">
                {local.modulo_dashboard && (
                  <Button size="sm" variant="outline" asChild>
                    <Link to="/pos/dashboard" onClick={() => setLocalAtualId(local.id)}>
                      <BarChart3 className="h-4 w-4 mr-1" /> Dashboard
                    </Link>
                  </Button>
                )}
                {local.modulo_pdv && (
                  <Button size="sm" variant="outline" asChild>
                    <Link to="/pos" onClick={() => setLocalAtualId(local.id)}>
                      <ShoppingCart className="h-4 w-4 mr-1" /> Caixa
                    </Link>
                  </Button>
                )}
                {local.modulo_vendas && (
                  <Button size="sm" variant="outline" asChild>
                    <Link to="/pos/vendas" onClick={() => setLocalAtualId(local.id)}>
                      <ArrowRight className="h-4 w-4 mr-1" /> Vendas
                    </Link>
                  </Button>
                )}
                {local.modulo_produtos && (
                  <Button size="sm" variant="outline" asChild>
                    <Link to={`/pos/locais/${local.id}/produtos`} onClick={() => setLocalAtualId(local.id)}>
                      <Package className="h-4 w-4 mr-1" /> Produtos
                    </Link>
                  </Button>
                )}
                {local.modulo_estoque && (
                  <Button size="sm" variant="outline" asChild>
                    <Link to="/pos/entradas/novo" onClick={() => setLocalAtualId(local.id)}>
                      <Boxes className="h-4 w-4 mr-1" /> Estoque
                    </Link>
                  </Button>
                )}
                <Button size="sm" variant="outline" asChild>
                  <Link to={`/pos/locais/${local.id}/familias`} onClick={() => setLocalAtualId(local.id)}>
                    <Tags className="h-4 w-4 mr-1" /> Famílias
                  </Link>
                </Button>
              </div>

              {local.permite_desconto && (
                <div className="flex items-center gap-2">
                  <Label className="text-xs">Desconto Máx. (%)</Label>
                  <Input
                    type="number"
                    className="h-7 w-20 text-xs"
                    value={local.desconto_maximo_perc}
                    min={0}
                    max={100}
                    onChange={(e) =>
                      toggleField(local, "desconto_maximo_perc", Number(e.target.value))
                    }
                  />
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function ToggleRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between p-2 rounded border border-border cursor-pointer hover:bg-muted/50">
      <span className="text-xs font-medium">{label}</span>
      <input
        type="checkbox"
        checked={value}
        onChange={(e) => onChange(e.target.checked)}
        className="h-4 w-4 accent-mm-accent"
      />
    </label>
  );
}

import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Plus, Trash2, Edit2, Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useLocais,
  useProdutosLocal,
  useCriarProdutoLocal,
  useAtualizarProdutoLocal,
  useDeletarProdutoLocal,
  useFamilias,
  usePosLocalAtual,
} from "@/routes/pos/hooks";
import { useProdutos } from "@/routes/inventory/hooks";
import type { ProdutoLocal, ProdutoLocalUpdate } from "@/routes/pos/types";
import { formatBRL } from "@/lib/utils";
import { POSNav } from "./pos-nav";

export function ProdutosLocalListPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const localId = Number(id);

  const { data: locais } = useLocais();
  const { setLocalId } = usePosLocalAtual();
  const { data: produtosLocal, isLoading } = useProdutosLocal(localId);
  const { data: familias } = useFamilias(localId);
  const { data: produtosEstoque } = useProdutos({ ativo: true, page_size: 1000 });
  const criar = useCriarProdutoLocal();
  const atualizar = useAtualizarProdutoLocal();
  const deletar = useDeletarProdutoLocal();

  const local = locais?.find((l) => l.id === localId);
  useEffect(() => {
    if (localId) setLocalId(localId);
  }, [localId, setLocalId]);

  const [modoAdd, setModoAdd] = useState(false);
  const [produtoId, setProdutoId] = useState<number | null>(null);
  const [precoVenda, setPrecoVenda] = useState("");
  const [familiaId, setFamiliaId] = useState<number | null>(null);
  const [estoqueMin, setEstoqueMin] = useState("0");
  const [estoqueMax, setEstoqueMax] = useState("0");
  const [pontoReab, setPontoReab] = useState("0");

  const [editando, setEditando] = useState<number | null>(null);
  const [editPayload, setEditPayload] = useState<Partial<ProdutoLocalUpdate>>({});

  const produtosDisponiveis = useMemo(() => {
    const vinculados = new Set(produtosLocal?.map((p) => p.produto_id) ?? []);
    return produtosEstoque?.items.filter((p) => !vinculados.has(p.id)) ?? [];
  }, [produtosEstoque, produtosLocal]);

  const handleCriar = async () => {
    if (!produtoId) return toast.error("Selecione um produto");
    try {
      await criar.mutateAsync({
        localId,
        payload: {
          produto_id: produtoId,
          familia_id: familiaId,
          preco_venda: precoVenda || "0",
          estoque_minimo: estoqueMin,
          estoque_maximo: estoqueMax,
          ponto_reabastecimento: pontoReab,
          ativo: true,
        },
      });
      setModoAdd(false);
      setProdutoId(null);
      setPrecoVenda("");
      setFamiliaId(null);
      toast.success("Produto vinculado ao local");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao vincular produto");
    }
  };

  const handleDeletar = async (plId: number) => {
    if (!confirm("Remover produto deste local?")) return;
    try {
      await deletar.mutateAsync(plId);
      toast.success("Produto removido do local");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao remover");
    }
  };

  const iniciarEdicao = (pl: ProdutoLocal) => {
    setEditando(pl.id);
    setEditPayload({
      familia_id: pl.familia_id,
      preco_venda: pl.preco_venda,
      estoque_minimo: pl.estoque_minimo,
      ponto_reabastecimento: pl.ponto_reabastecimento,
      estoque_maximo: pl.estoque_maximo,
      ativo: pl.ativo,
    });
  };

  const salvarEdicao = async (plId: number) => {
    try {
      await atualizar.mutateAsync({ id: plId, payload: editPayload });
      setEditando(null);
      toast.success("Atualizado");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao atualizar");
    }
  };

  return (
    <div className="space-y-4">
      <POSNav />
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={() => navigate("/pos/locais")}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-2xl font-bold tracking-tight">
          Produtos — {local?.nome ?? `Local #${localId}`}
        </h1>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Vincular Produto do Estoque</CardTitle>
            <Button size="sm" variant={modoAdd ? "outline" : "default"} onClick={() => setModoAdd(!modoAdd)}>
              {modoAdd ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
              {modoAdd ? "Cancelar" : "Adicionar"}
            </Button>
          </div>
        </CardHeader>
        {modoAdd && (
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">Produto do Estoque</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={produtoId ?? ""}
                  onChange={(e) => setProdutoId(Number(e.target.value) || null)}
                >
                  <option value="">Selecione...</option>
                  {produtosDisponiveis.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome} ({p.sku || "sem SKU"}) — Estoque: {p.estoque_atual}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Família</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={familiaId ?? ""}
                  onChange={(e) => setFamiliaId(Number(e.target.value) || null)}
                >
                  <option value="">Sem família</option>
                  {familias?.map((f) => (
                    <option key={f.id} value={f.id}>{f.nome}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Preço de Venda</Label>
                <Input
                  type="number"
                  step="0.01"
                  placeholder="0,00"
                  value={precoVenda}
                  onChange={(e) => setPrecoVenda(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Estoque Mínimo</Label>
                <Input
                  type="number"
                  value={estoqueMin}
                  onChange={(e) => setEstoqueMin(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Ponto de Reabastecimento</Label>
                <Input
                  type="number"
                  value={pontoReab}
                  onChange={(e) => setPontoReab(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Estoque Máximo</Label>
                <Input
                  type="number"
                  value={estoqueMax}
                  onChange={(e) => setEstoqueMax(e.target.value)}
                />
              </div>
            </div>
            <Button onClick={handleCriar} disabled={criar.isPending} className="bg-mm-accent text-white">
              <Plus className="h-4 w-4 mr-1" /> Vincular Produto
            </Button>
          </CardContent>
        )}
      </Card>

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      <div className="space-y-2">
        {produtosLocal?.map((pl) => (
          <Card key={pl.id}>
            <CardContent className="py-3">
              {editando === pl.id ? (
                <div className="grid grid-cols-1 md:grid-cols-6 gap-3 items-end">
                  <div className="md:col-span-2">
                    <Label className="text-xs">Produto</Label>
                    <p className="text-sm font-medium">{pl.produto_nome}</p>
                  </div>
                  <div>
                    <Label className="text-xs">Família</Label>
                    <select
                      className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                      value={editPayload.familia_id ?? ""}
                      onChange={(e) =>
                        setEditPayload((p) => ({
                          ...p,
                          familia_id: e.target.value ? Number(e.target.value) : null,
                        }))
                      }
                    >
                      <option value="">Sem família</option>
                      {familias?.map((f) => (
                        <option key={f.id} value={f.id}>{f.nome}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label className="text-xs">Preço Venda</Label>
                    <Input
                      type="number"
                      step="0.01"
                      className="h-9 text-xs"
                      value={editPayload.preco_venda ?? ""}
                      onChange={(e) =>
                        setEditPayload((p) => ({ ...p, preco_venda: e.target.value }))
                      }
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Ativo</Label>
                    <select
                      className="flex h-9 w-full rounded-md border border-input bg-background px-2 py-1 text-xs"
                      value={editPayload.ativo ? "true" : "false"}
                      onChange={(e) =>
                        setEditPayload((p) => ({ ...p, ativo: e.target.value === "true" }))
                      }
                    >
                      <option value="true">Sim</option>
                      <option value="false">Não</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="ghost" onClick={() => salvarEdicao(pl.id)}>
                      <Check className="h-4 w-4 text-emerald-600" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditando(null)}>
                      <X className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-x-6 gap-y-1 text-sm flex-1">
                    <div>
                      <p className="text-xs text-mm-muted">Produto</p>
                      <p className="font-medium">{pl.produto_nome}</p>
                      <p className="text-xs text-mm-muted">{pl.produto_sku}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Família</p>
                      <p>{pl.familia_nome || "—"}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Preço Venda</p>
                      <p className="font-medium">{formatBRL(Number(pl.preco_venda))}</p>
                    </div>
                    <div>
                      <p className="text-xs text-mm-muted">Estoque Local</p>
                      <p className={Number(pl.estoque_atual) <= Number(pl.estoque_minimo) ? "text-destructive font-medium" : ""}>
                        {pl.estoque_atual}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button size="sm" variant="ghost" onClick={() => iniciarEdicao(pl)}>
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-destructive"
                      onClick={() => handleDeletar(pl.id)}
                      disabled={deletar.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {produtosLocal?.length === 0 && !isLoading && (
        <p className="text-sm text-mm-muted">Nenhum produto vinculado a este local.</p>
      )}
    </div>
  );
}

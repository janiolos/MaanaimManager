import { useState } from "react";
import { toast } from "sonner";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLocais, useProdutosLocal, useCriarTransferenciaLocal, usePosLocalAtual } from "@/routes/pos/hooks";
import { POSNav } from "./pos-nav";

export function EntradaFormPage() {
  const { data: locais } = useLocais();
  const { localId, setLocalId } = usePosLocalAtual();
  const { data: produtos } = useProdutosLocal(localId ?? 0);
  const criarTransferencia = useCriarTransferenciaLocal();

  const [produtoLocalId, setProdutoLocalId] = useState<number | null>(null);
  const [quantidade, setQuantidade] = useState("");
  const [data, setData] = useState(new Date().toISOString().split("T")[0]);
  const [observacao, setObservacao] = useState("");

  const handleSubmit = async () => {
    if (!produtoLocalId || !quantidade || !data) {
      return toast.error("Preencha produto, quantidade e data");
    }
    try {
      await criarTransferencia.mutateAsync({
        produto_local_id: produtoLocalId,
        quantidade,
        data,
        observacao,
      });
      toast.success("Transferência concluída; depósito e ponto de venda atualizados");
      setQuantidade("");
      setObservacao("");
      setProdutoLocalId(null);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao registrar entrada");
    }
  };

  return (
    <div className="space-y-4">
      <POSNav />
      <h1 className="text-2xl font-bold tracking-tight">Transferir Estoque para o PDV</h1>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle className="text-base">Depósito central → ponto de venda</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Local de Venda</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={localId ?? ""}
              onChange={(e) => {
                setLocalId(Number(e.target.value) || null);
                setProdutoLocalId(null);
              }}
            >
              <option value="">Selecione...</option>
              {locais?.filter((l) => l.modulo_estoque && l.ativo && !l.is_deposito_interno).map((l) => (
                <option key={l.id} value={l.id}>{l.nome}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label>Produto</Label>
            <select
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={produtoLocalId ?? ""}
              onChange={(e) => setProdutoLocalId(Number(e.target.value) || null)}
              disabled={!localId}
            >
              <option value="">Selecione...</option>
              {produtos?.map((pl) => (
                <option key={pl.id} value={pl.id}>
                  {pl.produto_nome} (SKU: {pl.produto_sku}) — Est: {pl.estoque_atual}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-3">
            <div className="space-y-1.5">
              <Label>Quantidade</Label>
              <Input
                type="number"
                step="0.01"
                value={quantidade}
                onChange={(e) => setQuantidade(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Data</Label>
            <Input type="date" value={data} onChange={(e) => setData(e.target.value)} />
          </div>

          <div className="space-y-1.5">
            <Label>Observação</Label>
            <Input value={observacao} onChange={(e) => setObservacao(e.target.value)} />
          </div>

          <Button onClick={handleSubmit} disabled={criarTransferencia.isPending} className="w-full">
            <Plus className="h-4 w-4 mr-1" />
            {criarTransferencia.isPending ? "Transferindo..." : "Transferir Estoque"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

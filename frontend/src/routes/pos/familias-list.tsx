import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useLocais, useFamilias, useCriarFamilia, useDeletarFamilia, usePosLocalAtual } from "@/routes/pos/hooks";
import { POSNav } from "./pos-nav";

export function FamiliasListPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const localId = Number(id);

  const { data: locais } = useLocais();
  const { setLocalId } = usePosLocalAtual();
  const { data: familias, isLoading } = useFamilias(localId);
  const criarFamilia = useCriarFamilia();
  const deletarFamilia = useDeletarFamilia();

  const local = locais?.find((l) => l.id === localId);
  useEffect(() => {
    if (localId) setLocalId(localId);
  }, [localId, setLocalId]);

  const [novoNome, setNovoNome] = useState("");

  const handleCriar = async () => {
    if (!novoNome.trim()) return toast.error("Informe o nome da família");
    try {
      await criarFamilia.mutateAsync({ localId, payload: { nome: novoNome.trim() } });
      setNovoNome("");
      toast.success("Família criada");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao criar família");
    }
  };

  const handleDeletar = async (familiaId: number) => {
    if (!confirm("Tem certeza que deseja excluir esta família?")) return;
    try {
      await deletarFamilia.mutateAsync({ localId, familiaId });
      toast.success("Família removida");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Erro ao remover família");
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
          Famílias — {local?.nome ?? `Local #${localId}`}
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Nova Família</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input
            placeholder="Nome da família (ex: Bebidas)"
            value={novoNome}
            onChange={(e) => setNovoNome(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCriar()}
          />
          <Button onClick={handleCriar} disabled={criarFamilia.isPending}>
            <Plus className="h-4 w-4 mr-1" /> Criar
          </Button>
        </CardContent>
      </Card>

      {isLoading && <p className="text-sm text-mm-muted">Carregando...</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {familias?.map((f) => (
          <Card key={f.id}>
            <CardContent className="flex items-center justify-between py-4">
              <span className="font-medium">{f.nome}</span>
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive"
                onClick={() => handleDeletar(f.id)}
                disabled={deletarFamilia.isPending}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {familias?.length === 0 && !isLoading && (
        <p className="text-sm text-mm-muted">Nenhuma família cadastrada neste local.</p>
      )}
    </div>
  );
}

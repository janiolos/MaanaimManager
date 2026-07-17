import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Plus, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { PaginatedRequisicoes } from "@/routes/inventory/types";
import { REQUISICAO_AREA_LABELS, REQUISICAO_STATUS_LABELS } from "@/routes/inventory/types";

export function RequisicoesListPage() {
  const { data, refetch, isFetching } = useQuery<PaginatedRequisicoes>({
    queryKey: ["inventory", "requisicoes"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedRequisicoes>("/inventory/requisicoes", {
        params: { page: 1, page_size: 50 },
      });
      return data;
    },
    placeholderData: (prev) => prev,
  });

  async function finalizar(id: number) {
    if (!confirm("Finalizar requisição? Esta ação baixa o estoque atomicamente e NÃO pode ser desfeita.")) return;
    try {
      await api.post(`/inventory/requisicoes/${id}/finalizar`);
      toast.success("Requisição finalizada - estoque baixado");
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao finalizar");
    }
  }

  async function cancelar(id: number) {
    if (!confirm("Cancelar requisição?")) return;
    try {
      await api.post(`/inventory/requisicoes/${id}/cancelar`);
      toast.success("Requisição cancelada");
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao cancelar");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold font-display">Requisições de saída</h1>
          <p className="text-sm text-mm-muted">{data?.total ?? 0} requisição(ões)</p>
        </div>
        <Button asChild>
          <Link to="/inventory/requisicoes/novo">
            <Plus className="mr-2" size={16} /> Nova requisição
          </Link>
        </Button>
      </div>

      <Card>
        <CardContent>
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            Atualizar
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {data?.items.map((r) => (
          <Card key={r.id}>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm">{r.numero}</span>
                    <Badge
                      variant={
                        r.status === "FINALIZADA" ? "success" : r.status === "CANCELADA" ? "destructive" : "secondary"
                      }
                    >
                      {REQUISICAO_STATUS_LABELS[r.status] ?? r.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-mm-muted mt-1">
                    {REQUISICAO_AREA_LABELS[r.area] ?? r.area} · {formatDateTime(r.data_solicitacao)} · {r.itens.length} item(s)
                  </p>
                  {r.observacao && <p className="text-sm mt-2">{r.observacao}</p>}
                </div>
                <div className="flex gap-2">
                  {r.status === "ABERTA" && (
                    <>
                      <Button asChild variant="outline" size="sm">
                        <Link to={`/inventory/requisicoes/${r.id}/editar`}>Editar</Link>
                      </Button>
                      <Button size="sm" onClick={() => finalizar(r.id)}>
                        <CheckCircle2 className="mr-2" size={14} /> Finalizar
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => cancelar(r.id)}>
                        <XCircle className="mr-2" size={14} /> Cancelar
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
        {data?.items.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-mm-muted">
              Nenhuma requisição neste evento.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
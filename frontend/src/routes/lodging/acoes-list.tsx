import { useQuery } from "@tanstack/react-query";
import { Plus, XCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { useChales } from "@/routes/lodging/hooks";
import type { PaginatedAcoes } from "@/routes/lodging/types";
import { ACAO_TIPO_LABELS } from "@/routes/lodging/types";

export function AcoesListPage() {
  const { data: chales } = useChales();
  const { data, refetch } = useQuery<PaginatedAcoes>({
    queryKey: ["lodging", "acoes"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedAcoes>("/lodging/acoes", {
        params: { page: 1, page_size: 50 },
      });
      return data;
    },
  });

  async function cancelar(id: number) {
    if (!confirm("Cancelar esta ação?")) return;
    try {
      await api.post(`/lodging/acoes/${id}/cancelar`);
      toast.success("Ação cancelada");
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold font-display">Ações de chalé</h1>
          <p className="text-sm text-mm-muted">Bloqueios / manutenções - {data?.total ?? 0}</p>
        </div>
        <Button asChild>
          <Link to="/lodging/acoes/novo">
            <Plus className="mr-2" size={16} /> Nova ação
          </Link>
        </Button>
      </div>

      <div className="space-y-3">
        {data?.items.map((a) => {
          const chale = chales?.find((c) => c.id === a.chale_id);
          return (
            <Card key={a.id} className={a.ativo ? "" : "opacity-60"}>
              <CardContent className="pt-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">#{a.id}</span>
                      <Badge variant={a.tipo === "BLOQUEIO" ? "destructive" : "warning"}>
                        {ACAO_TIPO_LABELS[a.tipo] ?? a.tipo}
                      </Badge>
                      {chale && <Badge variant="outline">{chale.codigo}</Badge>}
                      {!a.ativo && <Badge variant="secondary">inativa</Badge>}
                    </div>
                    <p className="text-sm mt-1 font-medium">{a.titulo}</p>
                    <p className="text-xs text-mm-muted mt-1">
                      {formatDate(a.data_inicio)} → {formatDate(a.data_fim)}
                    </p>
                    {a.descricao && <p className="text-sm mt-2 text-mm-muted">{a.descricao}</p>}
                  </div>
                  {a.ativo && (
                    <Button size="sm" variant="outline" onClick={() => cancelar(a.id)}>
                      <XCircle className="mr-2" size={14} /> Cancelar
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
        {data?.items.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-mm-muted">
              Nenhuma ação ativa.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
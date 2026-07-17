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
import type { PaginatedReservas } from "@/routes/lodging/types";
import { RESERVA_STATUS_LABELS } from "@/routes/lodging/types";

export function ReservasListPage() {
  const { data: chales } = useChales();
  const { data, refetch } = useQuery<PaginatedReservas>({
    queryKey: ["lodging", "reservas"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedReservas>("/lodging/reservas", {
        params: { page: 1, page_size: 50 },
      });
      return data;
    },
  });

  async function cancelar(id: number) {
    if (!confirm("Cancelar esta reserva?")) return;
    try {
      await api.post(`/lodging/reservas/${id}/cancelar`);
      toast.success("Reserva cancelada");
      refetch();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao cancelar");
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold font-display">Reservas</h1>
          <p className="text-sm text-mm-muted">{data?.total ?? 0} reserva(s)</p>
        </div>
        <Button asChild>
          <Link to="/lodging/reservas/novo">
            <Plus className="mr-2" size={16} /> Nova reserva
          </Link>
        </Button>
      </div>

      <div className="space-y-3">
        {data?.items.map((r) => {
          const chale = chales?.find((c) => c.id === r.chale_id);
          const variant =
            r.status === "CONFIRMADA" ? "success" : r.status === "CANCELADA" ? "destructive" : "secondary";
          return (
            <Card key={r.id} className={r.status === "CANCELADA" ? "opacity-60" : undefined}>
              <CardContent className="pt-6">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">#{r.id}</span>
                      <Badge variant={variant}>{RESERVA_STATUS_LABELS[r.status] ?? r.status}</Badge>
                      {chale && <Badge variant="outline">{chale.codigo}</Badge>}
                    </div>
                    <p className="text-sm mt-1 font-medium">{r.responsavel_nome}</p>
                    <p className="text-xs text-mm-muted mt-1">
                      {r.data_entrada ? formatDate(r.data_entrada) : "?"} → {r.data_saida ? formatDate(r.data_saida) : "?"}
                      {" · "}
                      {r.qtd_pessoas} adulto(s) + {r.qtd_criancas} criança(s)
                      {r.pago && " · pago"}
                    </p>
                    {r.observacoes && <p className="text-sm mt-2 text-mm-muted">{r.observacoes}</p>}
                  </div>
                  {r.status !== "CANCELADA" && (
                    <Button size="sm" variant="destructive" onClick={() => cancelar(r.id)}>
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
              Nenhuma reserva neste evento.
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
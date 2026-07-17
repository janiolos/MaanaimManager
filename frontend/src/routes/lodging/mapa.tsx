import { Calendar } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useMapa } from "@/routes/lodging/hooks";
import type { MapaCell } from "@/routes/lodging/types";
import { cn, formatDate } from "@/lib/utils";

const tipoColor: Record<string, string> = {
  RESERVA: "bg-mm-accent/80 text-white",
  ACAAO: "bg-mm-warning/80 text-black",
  ACAO: "bg-mm-warning/80 text-black",
  LIVRE: "bg-muted text-mm-muted",
};

export function MapaPage() {
  const { data, isLoading } = useMapa(14);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Mapa de chalés</h1>
          <p className="text-sm text-mm-muted">Timeline dos próximos 14 dias</p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/lodging/reservas/novo">
            <Calendar className="mr-2" size={14} /> Nova reserva
          </Link>
        </Button>
      </div>

      {isLoading || !data ? (
        <p className="text-mm-muted">Carregando mapa...</p>
      ) : (
        <Card>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="text-xs">
                <thead>
                  <tr>
                    <th className="sticky left-0 bg-card z-10 px-2 py-2 text-left">Chalé</th>
                    {data.dias.map((d) => {
                      const dt = new Date(d);
                      const isWeekend = dt.getDay() === 0 || dt.getDay() === 6;
                      return (
                        <th
                          key={d}
                          className={cn(
                            "px-1 py-2 text-center min-w-[80px]",
                            isWeekend && "bg-muted/30"
                          )}
                        >
                          <div className="font-medium">
                            {dt.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" })}
                          </div>
                          <div className="text-mm-muted font-normal">
                            {dt.toLocaleDateString("pt-BR", { weekday: "short" })}
                          </div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {data.chales.map((chale, rowIdx) => (
                    <tr key={chale.id} className="border-t border-border">
                      <th className="sticky left-0 bg-card z-10 px-2 py-2 text-left font-mono">
                        {chale.codigo}
                      </th>
                      {data.celulas[rowIdx]?.map((cell: MapaCell, i) => (
                        <td key={i} className="p-0.5">
                          <div
                            className={cn(
                              "rounded text-center px-1 py-1 truncate min-h-[28px] flex items-center justify-center",
                              tipoColor[cell.tipo] ?? "bg-muted"
                            )}
                            title={`${cell.chale_codigo} · ${formatDate(cell.data)} · ${cell.tipo}: ${cell.label}`}
                          >
                            {cell.tipo === "LIVRE" ? "·" : cell.label || cell.tipo[0]}
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex gap-4 text-xs text-mm-muted">
              <span><span className="inline-block w-3 h-3 rounded bg-mm-accent/80 align-middle mr-1" /> Reserva</span>
              <span><span className="inline-block w-3 h-3 rounded bg-mm-warning/80 align-middle mr-1" /> Bloqueio/Manutenção</span>
              <span><span className="inline-block w-3 h-3 rounded bg-muted align-middle mr-1" /> Livre</span>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
import { BedDouble, CalendarCheck, Home, Wrench } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useLodgingDashboard } from "@/routes/lodging/hooks";

export function LodgingDashboardPage() {
  const { data, isLoading } = useLodgingDashboard();
  if (isLoading) return <p className="text-mm-muted">Carregando dashboard...</p>;
  if (!data) return null;

  const cards = [
    { title: "Chalés ativos", value: data.chales_ativos, hint: `${data.total_chales} totais`, icon: Home, variant: "text-mm-accent" },
    { title: "Em manutenção", value: data.chales_manutencao, icon: Wrench, variant: "text-mm-warning" },
    { title: "Reservas ativas", value: data.reservas_ativas, hint: `${data.reservas_confirmadas} confirmadas`, icon: CalendarCheck },
    { title: "Ações ativas", value: data.acoes_ativas, icon: BedDouble },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap justify-between items-center gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Hospedagem</h1>
          <p className="text-sm text-mm-muted">Visão geral dos chalés</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/lodging/chales" className="px-3 py-2 rounded border border-input hover:bg-accent text-sm">Chalés</Link>
          <Link to="/lodging/reservas" className="px-3 py-2 rounded border border-input hover:bg-accent text-sm">Reservas</Link>
          <Link to="/lodging/acoes" className="px-3 py-2 rounded border border-input hover:bg-accent text-sm">Ações</Link>
          <Link to="/lodging/mapa" className="px-3 py-2 rounded border border-input hover:bg-accent text-sm">Mapa</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => (
          <Card key={c.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-mm-muted">{c.title}</CardTitle>
              <c.icon className={`size-5 ${c.variant ?? "text-mm-accent"}`} />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${c.variant ?? ""}`}>{c.value}</div>
              {c.hint && <p className="text-xs text-mm-muted mt-1">{c.hint}</p>}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
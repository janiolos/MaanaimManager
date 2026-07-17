import { CalendarPlus, CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { useEventoStore, type Evento } from "@/stores/evento-store";

interface EventoApi extends Evento {
  taxa_base: string;
  taxa_trabalhador: string;
  adicional_chale: string;
  prev_participantes: number | null;
  prev_trabalhadores: number | null;
  observacoes: string;
  fechado: boolean;
  responsavel_geral_id: number | null;
  centro_custo_id: number | null;
}

export function SelecionarEventoPage() {
  const { setEvento, eventoId } = useEventoStore();
  const navigate = useNavigate();
  const [eventos, setEventos] = useState<EventoApi[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<EventoApi[]>("/core/eventos", { params: { apenas_ativos: true } })
      .then((res) => setEventos(res.data))
      .catch(() => toast.error("Não foi possível carregar eventos"))
      .finally(() => setLoading(false));
  }, []);

  function escolher(ev: EventoApi) {
    setEvento(ev);
    toast.success(`Evento selecionado: ${ev.nome}`);
    navigate("/");
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold font-display">Selecionar Evento</h1>
          <p className="text-sm text-mm-muted">
            Escolha o ciclo atual. Todas as operações serão contextuais a este evento.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to="/core/eventos/novo">
            <CalendarPlus className="mr-2" size={16} /> Novo evento
          </Link>
        </Button>
      </div>

      {loading ? (
        <p className="text-mm-muted">Carregando...</p>
      ) : eventos.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-mm-muted">Nenhum evento ativo. Crie o primeiro.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {eventos.map((ev) => (
            <Card
              key={ev.id}
              className={ev.id === eventoId ? "border-mm-accent" : undefined}
            >
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{ev.nome}</CardTitle>
                <Badge variant={ev.status === "EM_ANDAMENTO" ? "success" : "secondary"}>
                  {ev.status.replace("_", " ")}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-mm-muted">
                  {formatDateTime(ev.data_inicio)} → {formatDateTime(ev.data_fim)}
                </p>
                <Button
                  className="mt-4 w-full"
                  variant={ev.id === eventoId ? "secondary" : "default"}
                  onClick={() => escolher(ev)}
                >
                  <CheckCircle2 className="mr-2" size={16} />
                  {ev.id === eventoId ? "Selecionado" : "Selecionar"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
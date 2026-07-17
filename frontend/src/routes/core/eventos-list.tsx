import { Calendar, ChevronLeft, ChevronRight, Edit2, Lock, Plus, Search, X } from "lucide-react";
import { useState, useMemo } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useEventos } from "@/routes/core/hooks";
import { formatDateTime, formatDate } from "@/lib/utils";

const MONTH_NAMES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
];

const WEEK_DAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];

export function EventosListPage() {
  const [busca, setBusca] = useState("");
  const [statusFiltro, setStatusFiltro] = useState("");
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);

  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());

  // Fetch all events (including inactive ones if we want, but let's fetch all, apenas_ativos: false)
  const { data: allEvents = [], isLoading } = useEventos(false);

  // Month navigation
  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(y => y - 1);
    } else {
      setCurrentMonth(m => m - 1);
    }
    setSelectedDay(null);
  };

  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(y => y + 1);
    } else {
      setCurrentMonth(m => m + 1);
    }
    setSelectedDay(null);
  };

  // Calendar calculations
  const startDayOfWeek = useMemo(() => {
    return new Date(currentYear, currentMonth, 1).getDay();
  }, [currentYear, currentMonth]);

  const daysInMonth = useMemo(() => {
    return new Date(currentYear, currentMonth + 1, 0).getDate();
  }, [currentYear, currentMonth]);

  const calendarDays = useMemo(() => {
    const days: (Date | null)[] = [];
    // Blank padding for days of previous month
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null);
    }
    // Days of current month
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(currentYear, currentMonth, i));
    }
    return days;
  }, [currentYear, currentMonth, startDayOfWeek, daysInMonth]);

  // Helper to check if an event occurs on a specific day
  const getEventsForDay = (day: Date) => {
    const dayStart = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 0, 0, 0);
    const dayEnd = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 23, 59, 59);

    return allEvents.filter((ev) => {
      const evStart = new Date(ev.data_inicio);
      const evEnd = new Date(ev.data_fim);
      return evStart <= dayEnd && evEnd >= dayStart;
    });
  };

  // Filter events list
  const filteredEvents = useMemo(() => {
    return allEvents.filter((ev) => {
      // 1. Search term
      if (busca && !ev.nome.toLowerCase().includes(busca.toLowerCase())) {
        return false;
      }
      // 2. Status filter
      if (statusFiltro && ev.status !== statusFiltro) {
        return false;
      }
      // 3. Selected day from calendar
      if (selectedDay) {
        const dayStart = new Date(selectedDay.getFullYear(), selectedDay.getMonth(), selectedDay.getDate(), 0, 0, 0);
        const dayEnd = new Date(selectedDay.getFullYear(), selectedDay.getMonth(), selectedDay.getDate(), 23, 59, 59);
        const evStart = new Date(ev.data_inicio);
        const evEnd = new Date(ev.data_fim);
        if (!(evStart <= dayEnd && evEnd >= dayStart)) {
          return false;
        }
      }
      return true;
    });
  }, [allEvents, busca, statusFiltro, selectedDay]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Ciclos de Eventos</h1>
          <p className="text-sm text-mm-muted">
            Configure e controle os ciclos de eventos gerais do sistema
          </p>
        </div>
        <Button asChild>
          <Link to="/core/eventos/novo">
            <Plus className="mr-2" size={16} /> Novo evento
          </Link>
        </Button>
      </div>

      {/* Main Grid: Calendar left, list right */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left Col: Calendar (lg:span-5) */}
        <Card className="lg:col-span-5 h-fit">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg font-medium flex items-center gap-2">
              <Calendar size={18} className="text-primary" />
              <span>Calendário</span>
            </CardTitle>
            <div className="flex items-center gap-1">
              <Button variant="ghost" size="icon" onClick={prevMonth} className="h-8 w-8">
                <ChevronLeft size={16} />
              </Button>
              <span className="text-sm font-semibold min-w-[100px] text-center">
                {MONTH_NAMES[currentMonth]} {currentYear}
              </span>
              <Button variant="ghost" size="icon" onClick={nextMonth} className="h-8 w-8">
                <ChevronRight size={16} />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Weekdays */}
            <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-mm-muted mb-2">
              {WEEK_DAYS.map((d) => (
                <div key={d} className="py-1">
                  {d}
                </div>
              ))}
            </div>

            {/* Days Grid */}
            <div className="grid grid-cols-7 gap-1">
              {calendarDays.map((day, idx) => {
                if (!day) {
                  return <div key={`empty-${idx}`} className="aspect-square bg-muted/10 rounded-md" />;
                }

                const dayEvents = getEventsForDay(day);
                const isSelected = selectedDay && day.toDateString() === selectedDay.toDateString();
                const isToday = day.toDateString() === new Date().toDateString();

                return (
                  <button
                    key={day.toISOString()}
                    onClick={() => {
                      if (isSelected) {
                        setSelectedDay(null);
                      } else {
                        setSelectedDay(day);
                      }
                    }}
                    className={`relative aspect-square flex flex-col items-center justify-between p-1.5 rounded-md border text-sm transition-all hover:bg-muted/50 ${
                      isSelected
                        ? "border-primary bg-primary/10 font-semibold text-primary"
                        : isToday
                        ? "border-amber-500 font-semibold"
                        : "border-transparent bg-muted/20"
                    }`}
                  >
                    <span>{day.getDate()}</span>
                    {dayEvents.length > 0 && (
                      <div className="flex gap-0.5 justify-center w-full mt-1 overflow-hidden">
                        {dayEvents.slice(0, 3).map((ev) => (
                          <span
                            key={ev.id}
                            className={`h-1.5 w-1.5 rounded-full ${
                              ev.status === "EM_ANDAMENTO"
                                ? "bg-green-500"
                                : ev.status === "PLANEJADO"
                                ? "bg-blue-500"
                                : "bg-gray-400"
                            }`}
                            title={ev.nome}
                          />
                        ))}
                        {dayEvents.length > 3 && (
                          <span className="text-[9px] leading-none font-bold text-mm-muted">+</span>
                        )}
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Right Col: List (lg:span-7) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Filters Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-wrap items-center gap-3">
                <div className="relative flex-1 min-w-[200px]">
                  <Search
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-mm-muted"
                    size={16}
                  />
                  <Input
                    placeholder="Buscar evento por nome..."
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <select
                  className="flex h-10 w-full sm:w-[180px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  value={statusFiltro}
                  onChange={(e) => setStatusFiltro(e.target.value)}
                >
                  <option value="">Todos os status</option>
                  <option value="PLANEJADO">Planejados</option>
                  <option value="EM_ANDAMENTO">Em andamento</option>
                  <option value="ENCERRADO">Encerrados</option>
                </select>
              </div>

              {/* Selected Day filter banner */}
              {selectedDay && (
                <div className="mt-3 flex items-center justify-between bg-primary/10 border border-primary/20 px-3 py-1.5 rounded-md text-sm text-primary">
                  <span>Filtrando eventos ativos em {formatDate(selectedDay)}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedDay(null)}
                    className="h-6 w-6 p-0 text-primary hover:bg-primary/20"
                  >
                    <X size={14} />
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Events Table/List Card */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg font-medium">Lista de Ciclos</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-xs uppercase text-mm-muted">
                    <tr>
                      <th className="px-4 py-3">Nome</th>
                      <th className="px-4 py-3">Período</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Fechado</th>
                      <th className="px-4 py-3">Responsável</th>
                      <th className="px-4 py-3 text-center">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {isLoading ? (
                      <tr>
                        <td colSpan={6} className="px-4 py-8 text-center text-mm-muted">
                          Carregando eventos...
                        </td>
                      </tr>
                    ) : filteredEvents.length > 0 ? (
                      filteredEvents.map((ev) => (
                        <tr key={ev.id} className="border-t hover:bg-muted/30">
                          <td className="px-4 py-3">
                            <span className="font-medium text-foreground">{ev.nome}</span>
                            {ev.centro_custo && (
                              <p className="text-[11px] text-mm-muted">
                                CC: {ev.centro_custo.codigo} - {ev.centro_custo.nome}
                              </p>
                            )}
                          </td>
                          <td className="px-4 py-3 text-xs text-mm-muted space-y-0.5">
                            <div>Início: {formatDateTime(ev.data_inicio)}</div>
                            <div>Fim: {formatDateTime(ev.data_fim)}</div>
                          </td>
                          <td className="px-4 py-3">
                            {ev.status === "EM_ANDAMENTO" ? (
                              <Badge variant="success">Em andamento</Badge>
                            ) : ev.status === "PLANEJADO" ? (
                              <Badge variant="outline">Planejado</Badge>
                            ) : (
                              <Badge variant="secondary">Encerrado</Badge>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {ev.fechado ? (
                              <Badge variant="destructive">Sim</Badge>
                            ) : (
                              <Badge variant="success">Não</Badge>
                            )}
                          </td>
                          <td className="px-4 py-3 text-xs">
                            {ev.responsavel_geral
                              ? `${ev.responsavel_geral.first_name} ${ev.responsavel_geral.last_name}`.trim() ||
                                ev.responsavel_geral.username
                              : "—"}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {ev.fechado ? (
                              <div className="flex items-center justify-center text-mm-muted gap-1 text-xs">
                                <Lock size={12} /> Bloqueado
                              </div>
                            ) : (
                              <Button asChild variant="ghost" size="sm">
                                <Link to={`/core/eventos/${ev.id}/editar`}>
                                  <Edit2 size={12} className="mr-1.5" /> Editar
                                </Link>
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-12 text-center text-mm-muted">
                          Nenhum ciclo de evento encontrado para os filtros selecionados.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

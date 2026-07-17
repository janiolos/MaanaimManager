import { Accessibility, Plus, Wrench } from "lucide-react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useChales } from "@/routes/lodging/hooks";
import { CHALE_STATUS_LABELS } from "@/routes/lodging/types";
import { cn } from "@/lib/utils";

export function ChalesListPage() {
  const { data, isLoading } = useChales();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold font-display">Chalés</h1>
          <p className="text-sm text-mm-muted">{data?.length ?? 0} cadastrado(s)</p>
        </div>
        <Button asChild>
          <Link to="/lodging/chales/novo">
            <Plus className="mr-2" size={16} /> Novo chalé
          </Link>
        </Button>
      </div>

      {isLoading ? (
        <p className="text-mm-muted">Carregando...</p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {data?.map((c) => {
            const variant =
              c.status === "ATIVO" ? "success" : c.status === "MANUTENCAO" ? "warning" : "secondary";
            return (
              <Card key={c.id} className={cn(
                "border-l-4",
                c.status === "ATIVO" && "border-l-mm-accent",
                c.status === "MANUTENCAO" && "border-l-mm-warning",
                c.status === "INATIVO" && "border-l-mm-muted",
              )}>
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-bold font-display">{c.codigo}</h3>
                      <p className="text-xs text-mm-muted">capacidade: {c.capacidade}</p>
                    </div>
                    <Badge variant={variant}>{CHALE_STATUS_LABELS[c.status]}</Badge>
                  </div>
                  <div className="mt-2 flex gap-3 text-xs text-mm-muted">
                    {c.acessivel_cadeirante && (
                      <span className="flex items-center gap-1">
                        <Accessibility size={12} /> acessível
                      </span>
                    )}
                    {c.status === "MANUTENCAO" && (
                      <span className="flex items-center gap-1 text-mm-warning">
                        <Wrench size={12} /> manutenção
                      </span>
                    )}
                  </div>
                  {c.observacoes && (
                    <p className="mt-3 text-xs text-mm-muted line-clamp-3">{c.observacoes}</p>
                  )}
                  <Button asChild variant="outline" size="sm" className="mt-4 w-full">
                    <Link to={`/lodging/chales/${c.id}/editar`}>Editar</Link>
                  </Button>
                </CardContent>
              </Card>
            );
          })}
          {data?.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center text-mm-muted">
                Nenhum chalé cadastrado.
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
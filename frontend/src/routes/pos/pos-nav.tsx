import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { usePosLocalAtual } from "@/routes/pos/hooks";

export function POSNav() {
  const location = useLocation();
  const { localId, setLocalId, localAtual, locais } = usePosLocalAtual();
  const tabs = [
    { to: "/pos/locais", label: "Locais", enabled: true },
    { to: "/pos/dashboard", label: "Dashboard", enabled: true },
    { to: "/pos", label: "PDV (Caixa)", enabled: localAtual?.modulo_pdv ?? false },
    { to: "/pos/vendas", label: "Vendas", enabled: localAtual?.modulo_vendas ?? false },
    {
      to: localId ? `/pos/locais/${localId}/produtos` : "/pos/locais",
      label: "Produtos",
      enabled: localAtual?.modulo_produtos ?? false,
    },
    {
      to: "/pos/entradas/novo",
      label: "Estoque",
      enabled: localAtual?.modulo_estoque ?? false,
    },
  ];

  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-mm-muted">Local atual do PDV</p>
          <select
            className="flex h-10 min-w-64 rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={localId ?? ""}
            onChange={(e) => setLocalId(e.target.value ? Number(e.target.value) : null)}
          >
            <option value="">Selecione um local...</option>
            {locais
              .filter((local) => !local.is_deposito_interno && local.ativo)
              .map((local) => (
                <option key={local.id} value={local.id}>
                  {local.nome}
                </option>
              ))}
          </select>
        </div>
        {localAtual && (
          <p className="text-xs text-mm-muted">
            Módulos ativos:{" "}
            {[
              localAtual.modulo_dashboard && "dashboard",
              localAtual.modulo_pdv && "caixa",
              localAtual.modulo_vendas && "vendas",
              localAtual.modulo_produtos && "produtos",
              localAtual.modulo_estoque && "estoque",
            ]
              .filter(Boolean)
              .join(" · ")}
          </p>
        )}
      </div>

      <div className="flex gap-1 border-b border-border pb-1 overflow-x-auto">
        {tabs.map((t) => (
          <Link
            key={t.label}
            to={t.enabled ? t.to : "/pos/locais"}
            className={cn(
              "px-4 py-2 text-sm font-medium rounded-t-md transition-colors whitespace-nowrap",
              (t.label === "Locais" && location.pathname === "/pos/locais") ||
                (t.enabled && location.pathname === t.to) ||
                (t.enabled && t.label === "Produtos" && location.pathname.startsWith("/pos/locais/") && location.pathname.endsWith("/produtos"))
                ? "bg-mm-accent text-white"
                : t.enabled
                  ? "text-mm-muted hover:text-mm-foreground hover:bg-muted"
                  : "text-mm-muted/60 bg-muted/30"
            )}
          >
            {t.label}
          </Link>
        ))}
      </div>
    </div>
  );
}

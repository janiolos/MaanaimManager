import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { AppShell } from "@/components/app-shell";
import { useAuthStore } from "@/stores/auth-store";
import { useEventoStore } from "@/stores/evento-store";
import { HomePage } from "@/routes/home";
import { LoginPage } from "@/routes/login";
import { SelecionarEventoPage } from "@/routes/selecionar-evento";
import { EventosListPage } from "@/routes/core/eventos-list";
import { EventoFormPage } from "@/routes/core/evento-form";
import { FinanceDashboardPage } from "@/routes/finance/dashboard";
import { FinanceFormPage } from "@/routes/finance/form";
import { FinanceListPage } from "@/routes/finance/list";
import { ReportsIndexPage } from "@/routes/finance/reports-index";
import { DREPage } from "@/routes/finance/dre";
import { FluxoCaixaPage } from "@/routes/finance/fluxo-caixa";
import { ConciliacaoPage } from "@/routes/finance/conciliacao";
import { OficialPage } from "@/routes/finance/oficial";
import { InventoryDashboardPage } from "@/routes/inventory/dashboard";
import { ProdutosListPage } from "@/routes/inventory/produtos-list";
import { ProdutoFormPage } from "@/routes/inventory/produto-form";
import { EntradaFormPage } from "@/routes/inventory/entrada-form";
import { FornecedoresListPage } from "@/routes/inventory/fornecedores-list";
import { RequisicoesListPage } from "@/routes/inventory/requisicoes-list";
import { RequisicaoFormPage } from "@/routes/inventory/requisicao-form";
import { CotacoesListPage } from "@/routes/inventory/cotacoes-list";
import { CotacaoFormPage } from "@/routes/inventory/cotacao-form";
import { LodgingDashboardPage } from "@/routes/lodging/dashboard";
import { ChalesListPage } from "@/routes/lodging/chales-list";
import { ChaleFormPage } from "@/routes/lodging/chale-form";
import { ReservasListPage } from "@/routes/lodging/reservas-list";
import { ReservaFormPage } from "@/routes/lodging/reserva-form";
import { AcoesListPage } from "@/routes/lodging/acoes-list";
import { AcaoFormPage } from "@/routes/lodging/acao-form";
import { MapaPage } from "@/routes/lodging/mapa";
import { PDVPage } from "@/routes/pos/pdv";
import { PDVDashboardPage } from "@/routes/pos/dashboard";
import { VendasListPage } from "@/routes/pos/vendas";
import { LocaisListPage } from "@/routes/pos/locais-list";
import { FamiliasListPage } from "@/routes/pos/familias-list";
import { ProdutosLocalListPage } from "@/routes/pos/produtos-local-list";
import { EntradaFormPage as PosEntradaFormPage } from "@/routes/pos/entrada-form";
import { ConfiguracoesPage } from "@/routes/core/configuracoes";
import { AdminPage } from "@/routes/core/admin";
import { VoluntariosPage } from "@/routes/voluntarios";

interface ProtectedProps {
  children: React.ReactNode;
  requireEvento?: boolean;
}

function Protected({ children, requireEvento }: ProtectedProps) {
  const { user } = useAuthStore();
  const { eventoId } = useEventoStore();
  const location = useLocation();

  if (!user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;

  if (requireEvento && eventoId === null && location.pathname !== "/selecionar-evento") {
    return <Navigate to="/selecionar-evento" replace />;
  }

  return <AppShell>{children}</AppShell>;
}



function App() {
  const queryClient = useQueryClient();
  const { eventoId } = useEventoStore();

  useEffect(() => {
    if (eventoId !== null) {
      queryClient.invalidateQueries();
    }
  }, [eventoId, queryClient]);

  // sincroniza access token entre abas via lógica simples no auth-store persist.
  // Em produção, refresh automático via cookie httponly. (placeholder)
  const { user, accessToken } = useAuthStore();
  useEffect(() => {
    if (user && !accessToken) {
      // tente refresh passivo; falha silenciosa = usuário precisa logar.
      fetch("/api/v1/auth/refresh", { method: "POST", credentials: "include" })
        .then((r) => (r.ok ? r.json() : Promise.reject(r)))
        .then((data: { access_token: string }) => useAuthStore.getState().setAccessToken(data.access_token))
        .catch(() => {
          /* ignore */
        });
    }
  }, [user, accessToken]);

  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <Protected requireEvento>
              <HomePage />
            </Protected>
          }
        />

        <Route
          path="/selecionar-evento"
          element={
            <Protected>
              <SelecionarEventoPage />
            </Protected>
          }
        />

        <Route
          path="/core/eventos"
          element={
            <Protected requireEvento>
              <EventosListPage />
            </Protected>
          }
        />
        <Route
          path="/core/eventos/novo"
          element={
            <Protected requireEvento>
              <EventoFormPage />
            </Protected>
          }
        />
        <Route
          path="/core/eventos/:id/editar"
          element={
            <Protected requireEvento>
              <EventoFormPage />
            </Protected>
          }
        />
        <Route
          path="/finance"
          element={
            <Protected requireEvento>
              <FinanceListPage />
            </Protected>
          }
        />
        <Route
          path="/finance/dashboard"
          element={
            <Protected requireEvento>
              <FinanceDashboardPage />
            </Protected>
          }
        />
        <Route
          path="/finance/novo"
          element={
            <Protected requireEvento>
              <FinanceFormPage />
            </Protected>
          }
        />
        <Route
          path="/finance/:id/editar"
          element={
            <Protected requireEvento>
              <FinanceFormPage />
            </Protected>
          }
        />
        <Route
          path="/finance/relatorios"
          element={
            <Protected requireEvento>
              <ReportsIndexPage />
            </Protected>
          }
        />
        <Route
          path="/finance/relatorios/dre"
          element={
            <Protected requireEvento>
              <DREPage />
            </Protected>
          }
        />
        <Route
          path="/finance/relatorios/fluxo-caixa"
          element={
            <Protected requireEvento>
              <FluxoCaixaPage />
            </Protected>
          }
        />
        <Route
          path="/finance/relatorios/conciliacao"
          element={
            <Protected requireEvento>
              <ConciliacaoPage />
            </Protected>
          }
        />
        <Route
          path="/finance/relatorios/oficial"
          element={
            <Protected requireEvento>
              <OficialPage />
            </Protected>
          }
        />
        <Route
          path="/inventory"
          element={
            <Protected requireEvento>
              <InventoryDashboardPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/produtos"
          element={
            <Protected requireEvento>
              <ProdutosListPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/produtos/novo"
          element={
            <Protected requireEvento>
              <ProdutoFormPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/produtos/:id/editar"
          element={
            <Protected requireEvento>
              <ProdutoFormPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/entradas/novo"
          element={
            <Protected requireEvento>
              <EntradaFormPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/fornecedores"
          element={
            <Protected requireEvento>
              <FornecedoresListPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/requisicoes"
          element={
            <Protected requireEvento>
              <RequisicoesListPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/requisicoes/novo"
          element={
            <Protected requireEvento>
              <RequisicaoFormPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/requisicoes/:id/editar"
          element={
            <Protected requireEvento>
              <RequisicaoFormPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/cotacoes"
          element={
            <Protected requireEvento>
              <CotacoesListPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/cotacoes/novo"
          element={
            <Protected requireEvento>
              <CotacaoFormPage />
            </Protected>
          }
        />
        <Route
          path="/inventory/cotacoes/:id/editar"
          element={
            <Protected requireEvento>
              <CotacaoFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging"
          element={
            <Protected requireEvento>
              <LodgingDashboardPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/chales"
          element={
            <Protected requireEvento>
              <ChalesListPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/chales/novo"
          element={
            <Protected requireEvento>
              <ChaleFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/chales/:id/editar"
          element={
            <Protected requireEvento>
              <ChaleFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/reservas"
          element={
            <Protected requireEvento>
              <ReservasListPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/reservas/novo"
          element={
            <Protected requireEvento>
              <ReservaFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/reservas/:id/editar"
          element={
            <Protected requireEvento>
              <ReservaFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/acoes"
          element={
            <Protected requireEvento>
              <AcoesListPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/acoes/novo"
          element={
            <Protected requireEvento>
              <AcaoFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/acoes/:id/editar"
          element={
            <Protected requireEvento>
              <AcaoFormPage />
            </Protected>
          }
        />
        <Route
          path="/lodging/mapa"
          element={
            <Protected requireEvento>
              <MapaPage />
            </Protected>
          }
        />
        <Route
          path="/pos"
          element={
            <Protected requireEvento>
              <PDVPage />
            </Protected>
          }
        />
        <Route
          path="/pos/dashboard"
          element={
            <Protected requireEvento>
              <PDVDashboardPage />
            </Protected>
          }
        />
        <Route
          path="/pos/vendas"
          element={
            <Protected requireEvento>
              <VendasListPage />
            </Protected>
          }
        />
        <Route
          path="/pos/locais"
          element={
            <Protected requireEvento>
              <LocaisListPage />
            </Protected>
          }
        />
        <Route
          path="/pos/locais/:id/familias"
          element={
            <Protected requireEvento>
              <FamiliasListPage />
            </Protected>
          }
        />
        <Route
          path="/pos/locais/:id/produtos"
          element={
            <Protected requireEvento>
              <ProdutosLocalListPage />
            </Protected>
          }
        />
        <Route
          path="/pos/entradas/novo"
          element={
            <Protected requireEvento>
              <PosEntradaFormPage />
            </Protected>
          }
        />
        <Route
          path="/configuracoes"
          element={
            <Protected requireEvento>
              <ConfiguracoesPage />
            </Protected>
          }
        />
        <Route
          path="/admin"
          element={
            <Protected requireEvento>
              <AdminPage />
            </Protected>
          }
        />
        <Route
          path="/voluntarios"
          element={
            <Protected requireEvento>
              <VoluntariosPage />
            </Protected>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <Toaster richColors position="top-right" />
    </>
  );
}

export default App;
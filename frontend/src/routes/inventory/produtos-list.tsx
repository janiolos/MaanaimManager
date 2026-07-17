import { AlertTriangle, ArrowUp, Boxes, Package, Plus, RefreshCw, Search } from "lucide-react";
import { useState, useEffect } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useProdutos } from "@/routes/inventory/hooks";
import { CATEGORIA_LABELS } from "@/routes/inventory/types";
import { formatBRL } from "@/lib/utils";

export function ProdutosListPage() {
  const [busca, setBusca] = useState("");
  const [debouncedBusca, setDebouncedBusca] = useState("");
  const [categoria, setCategoria] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  // Debounce search input using useEffect
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedBusca(busca);
    }, 350);
    return () => clearTimeout(timer);
  }, [busca]);

  // Fetch all products matching search/category filters (max 200)
  const { data, isLoading } = useProdutos({
    busca: debouncedBusca || undefined,
    categoria: categoria || undefined,
    page_size: 200,
  });

  const allItems = data?.items ?? [];
  const totalCount = allItems.length;

  // Calculate counts client-side for the summary cards
  const baixoCount = allItems.filter(
    (p) => Number(p.estoque_atual) < Number(p.estoque_minimo)
  ).length;

  const reabastCount = allItems.filter(
    (p) =>
      Number(p.estoque_atual) < Number(p.estoque_reabastecimento) &&
      Number(p.estoque_atual) >= Number(p.estoque_minimo)
  ).length;

  const acimaCount = allItems.filter(
    (p) =>
      Number(p.estoque_maximo) > 0 &&
      Number(p.estoque_atual) > Number(p.estoque_maximo)
  ).length;

  // Filter by status client-side
  const filteredItems = allItems.filter((p) => {
    if (!status) return true;
    const baixo = Number(p.estoque_atual) < Number(p.estoque_minimo);
    const reabast =
      Number(p.estoque_atual) < Number(p.estoque_reabastecimento) && !baixo;
    const acima =
      Number(p.estoque_maximo) > 0 && Number(p.estoque_atual) > Number(p.estoque_maximo);

    if (status === "baixo") return baixo;
    if (status === "reabastecer") return reabast;
    if (status === "acima") return acima;
    return true;
  });

  // Client-side pagination
  const pageSize = 12;
  const totalFiltered = filteredItems.length;
  const totalPages = Math.ceil(totalFiltered / pageSize);
  const activePage = Math.min(page, Math.max(1, totalPages));
  const startIndex = (activePage - 1) * pageSize;
  const paginatedItems = filteredItems.slice(startIndex, startIndex + pageSize);

  const handleBuscaChange = (val: string) => {
    setBusca(val);
    setPage(1);
  };

  const handleCategoriaChange = (val: string) => {
    setCategoria(val);
    setPage(1);
  };

  const handleStatusChange = (val: string) => {
    setStatus(val);
    setPage(1);
  };

  const clearFilters = () => {
    setBusca("");
    setDebouncedBusca("");
    setCategoria("");
    setStatus("");
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display">Estoque</h1>
          <p className="text-sm text-mm-muted">
            Gestão de produtos, entradas e alertas de mínimo/máximo
          </p>
        </div>
        <div className="flex gap-2">
          <Button asChild variant="outline">
            <Link to="/inventory/entradas/novo">
              <Boxes className="mr-2" size={16} /> Registrar entrada
            </Link>
          </Button>
          <Button asChild>
            <Link to="/inventory/produtos/novo">
              <Plus className="mr-2" size={16} /> Novo produto
            </Link>
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card Total */}
        <Card
          className={`cursor-pointer transition-all hover:scale-[1.01] ${
            status === "" ? "ring-2 ring-primary" : ""
          }`}
          onClick={() => handleStatusChange("")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-blue-500/10 p-2.5 text-blue-500">
                <Package size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-mm-muted">Produtos</p>
                <h3 className="text-2xl font-bold font-display mt-0.5">{totalCount}</h3>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Estoque Baixo */}
        <Card
          className={`cursor-pointer transition-all hover:scale-[1.01] ${
            status === "baixo" ? "ring-2 ring-destructive" : ""
          }`}
          onClick={() => handleStatusChange("baixo")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-red-500/10 p-2.5 text-red-500">
                <AlertTriangle size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-mm-muted">Estoque Baixo</p>
                <h3 className="text-2xl font-bold font-display text-destructive mt-0.5">
                  {baixoCount}
                </h3>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Reabastecimento */}
        <Card
          className={`cursor-pointer transition-all hover:scale-[1.01] ${
            status === "reabastecer" ? "ring-2 ring-orange-500" : ""
          }`}
          onClick={() => handleStatusChange("reabastecer")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-orange-500/10 p-2.5 text-orange-500">
                <RefreshCw size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-mm-muted">Reabastecimento</p>
                <h3 className="text-2xl font-bold font-display text-orange-500 mt-0.5">
                  {reabastCount}
                </h3>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card Acima do Máximo */}
        <Card
          className={`cursor-pointer transition-all hover:scale-[1.01] ${
            status === "acima" ? "ring-2 ring-amber-500" : ""
          }`}
          onClick={() => handleStatusChange("acima")}
        >
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-amber-500/10 p-2.5 text-amber-500">
                <ArrowUp size={20} />
              </div>
              <div>
                <p className="text-xs font-medium text-mm-muted">Acima do Máximo</p>
                <h3 className="text-2xl font-bold font-display text-amber-500 mt-0.5">
                  {acimaCount}
                </h3>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters Card */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4 items-end">
            {/* Search */}
            <div className="space-y-1.5 md:col-span-2">
              <div className="relative">
                <Search
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-mm-muted"
                  size={16}
                />
                <Input
                  placeholder="Buscar por nome ou SKU..."
                  value={busca}
                  onChange={(e) => handleBuscaChange(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            {/* Category Filter */}
            <div className="space-y-1.5">
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={categoria}
                onChange={(e) => handleCategoriaChange(e.target.value)}
              >
                <option value="">Todas as categorias</option>
                <option value="MATERIA_PRIMA">Matéria-prima</option>
                <option value="PRODUTO_ACABADO">Produto acabado</option>
                <option value="COMPONENTE">Componente</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="space-y-1.5">
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                value={status}
                onChange={(e) => handleStatusChange(e.target.value)}
              >
                <option value="">Todos os status</option>
                <option value="baixo">Estoque Baixo</option>
                <option value="reabastecer">Reabastecer</option>
                <option value="acima">Acima do Máximo</option>
              </select>
            </div>
          </div>

          {(busca || categoria || status) && (
            <div className="mt-3 flex justify-end">
              <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs">
                Limpar filtros
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Table Card */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase text-mm-muted">
                <tr>
                  <th className="px-4 py-3">SKU</th>
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Categoria</th>
                  <th className="px-4 py-3 text-right">Estoque</th>
                  <th className="px-4 py-3 text-right">Mínimo</th>
                  <th className="px-4 py-3 text-right">Custo médio</th>
                  <th className="px-4 py-3 text-right">Valor total</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-mm-muted">
                      Carregando...
                    </td>
                  </tr>
                ) : paginatedItems.length > 0 ? (
                  paginatedItems.map((p) => {
                    const baixo = Number(p.estoque_atual) < Number(p.estoque_minimo);
                    const reabast =
                      Number(p.estoque_atual) < Number(p.estoque_reabastecimento) && !baixo;
                    return (
                      <tr key={p.id} className="border-t hover:bg-muted/30">
                        <td className="px-4 py-3 font-mono text-xs">{p.sku}</td>
                        <td className="px-4 py-3">
                          <span className={p.ativo ? "font-medium" : "text-mm-muted line-through"}>
                            {p.nome}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs">
                          {CATEGORIA_LABELS[p.categoria] ?? p.categoria}
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {p.estoque_atual} {p.unidade}
                        </td>
                        <td className="px-4 py-3 text-right font-mono text-mm-muted">
                          {p.estoque_minimo}
                        </td>
                        <td className="px-4 py-3 text-right font-mono">
                          {formatBRL(p.custo_medio_atual)}
                        </td>
                        <td className="px-4 py-3 text-right font-mono font-medium">
                          {formatBRL(p.valor_estoque_atual)}
                        </td>
                        <td className="px-4 py-3">
                          {baixo ? (
                            <Badge variant="destructive">baixo</Badge>
                          ) : reabast ? (
                            <Badge variant="warning">reabastecer</Badge>
                          ) : p.ativo ? (
                            <Badge variant="success">OK</Badge>
                          ) : (
                            <Badge variant="secondary">inativo</Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Button asChild variant="ghost" size="sm">
                            <Link to={`/inventory/produtos/${p.id}/editar`}>Editar</Link>
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={9} className="px-4 py-12 text-center text-mm-muted">
                      Nenhum produto encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3">
              <span className="text-xs text-mm-muted">
                Exibindo {startIndex + 1} a {Math.min(startIndex + pageSize, totalFiltered)} de{" "}
                {totalFiltered} produto(s)
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={activePage === 1}
                  onClick={() => setPage(activePage - 1)}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={activePage === totalPages}
                  onClick={() => setPage(activePage + 1)}
                >
                  Próximo
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
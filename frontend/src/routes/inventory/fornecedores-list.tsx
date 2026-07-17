import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { Fornecedor } from "@/routes/inventory/types";
import { useFornecedores } from "@/routes/inventory/hooks";

export function FornecedoresListPage() {
  const { data, refetch } = useFornecedores();
  const [novoNome, setNovoNome] = useState("");
  const [criando, setCriando] = useState(false);

  async function criarRapido() {
    if (!novoNome.trim()) return;
    setCriando(true);
    try {
      await api.post("/inventory/fornecedores", { nome: novoNome });
      toast.success("Fornecedor criado");
      setNovoNome("");
      refetch();
    } catch {
      toast.error("Falha ao criar");
    } finally {
      setCriando(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold font-display">Fornecedores</h1>
        <p className="text-sm text-mm-muted">{data?.length ?? 0} cadastrado(s)</p>
      </div>

      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-2 max-w-md">
            <Input
              placeholder="Criar fornecedor rápido..."
              value={novoNome}
              onChange={(e) => setNovoNome(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && criarRapido()}
            />
            <Button onClick={criarRapido} disabled={criando}>
              <Plus className="mr-2" size={16} /> Criar
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase text-mm-muted">
                <tr>
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Documento</th>
                  <th className="px-4 py-3">Contato</th>
                  <th className="px-4 py-3">Telefone</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {data?.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-mm-muted">
                      Nenhum fornecedor.
                    </td>
                  </tr>
                )}
                {data?.map((f: Fornecedor) => (
                  <tr key={f.id} className="border-t hover:bg-muted/30">
                    <td className="px-4 py-3 font-medium">{f.nome}</td>
                    <td className="px-4 py-3 text-mm-muted">{f.documento || "—"}</td>
                    <td className="px-4 py-3">{f.contato || "—"}</td>
                    <td className="px-4 py-3">{f.telefone || "—"}</td>
                    <td className="px-4 py-3 text-xs">{f.email || "—"}</td>
                    <td className="px-4 py-3">
                      {f.ativo ? (
                        <Badge variant="success">ativo</Badge>
                      ) : (
                        <Badge variant="secondary">inativo</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
import { zodResolver } from "@hookform/resolvers/zod";
import { Edit2, Plus, Search, Trash2, X, Users, AlertTriangle } from "lucide-react";
import { useState, useMemo } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useVoluntarios,
  useCriarVoluntario,
  useAtualizarVoluntario,
  useDeletarVoluntario,
} from "./hooks";
import type { Voluntario } from "./types";

const voluntarioSchema = z.object({
  nome: z.string().min(1, "O nome é obrigatório"),
  igreja: z.string().default(""),
  area: z.string().default(""),
  regiao: z.string().default(""),
  especialidade: z.string().default(""),
});

type FormValues = z.infer<typeof voluntarioSchema>;

export function VoluntariosPage() {
  const { data: voluntarios = [], isLoading } = useVoluntarios();
  const criarMutation = useCriarVoluntario();
  const atualizarMutation = useAtualizarVoluntario();
  const deletarMutation = useDeletarVoluntario();

  const [busca, setBusca] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingVoluntario, setEditingVoluntario] = useState<Voluntario | null>(null);
  const [deletingVoluntario, setDeletingVoluntario] = useState<Voluntario | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(voluntarioSchema),
    defaultValues: {
      nome: "",
      igreja: "",
      area: "",
      regiao: "",
      especialidade: "",
    },
  });

  const filteredVoluntarios = useMemo(() => {
    return voluntarios.filter((v) => {
      const term = busca.toLowerCase();
      return (
        v.nome.toLowerCase().includes(term) ||
        v.igreja.toLowerCase().includes(term) ||
        v.area.toLowerCase().includes(term) ||
        v.regiao.toLowerCase().includes(term) ||
        v.especialidade.toLowerCase().includes(term)
      );
    });
  }, [voluntarios, busca]);

  function handleOpenCreate() {
    setEditingVoluntario(null);
    form.reset({
      nome: "",
      igreja: "",
      area: "",
      regiao: "",
      especialidade: "",
    });
    setModalOpen(true);
  }

  function handleOpenEdit(v: Voluntario) {
    setEditingVoluntario(v);
    form.reset({
      nome: v.nome,
      igreja: v.igreja,
      area: v.area,
      regiao: v.regiao,
      especialidade: v.especialidade,
    });
    setModalOpen(true);
  }

  async function onSubmit(values: FormValues) {
    try {
      if (editingVoluntario) {
        await atualizarMutation.mutateAsync({
          id: editingVoluntario.id,
          payload: values,
        });
        toast.success("Voluntário atualizado com sucesso!");
      } else {
        await criarMutation.mutateAsync(values);
        toast.success("Voluntário cadastrado com sucesso!");
      }
      setModalOpen(false);
    } catch {
      toast.error("Falha ao salvar voluntário. Tente novamente.");
    }
  }

  async function handleDeleteConfirm() {
    if (!deletingVoluntario) return;
    try {
      await deletarMutation.mutateAsync(deletingVoluntario.id);
      toast.success("Voluntário removido com sucesso!");
      setDeletingVoluntario(null);
    } catch {
      toast.error("Falha ao remover voluntário.");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold font-display flex items-center gap-2">
            <Users className="text-mm-primary" />
            <span>Voluntários</span>
          </h1>
          <p className="text-sm text-mm-muted">
            Cadastre e gerencie a equipe de voluntários e colaboradores
          </p>
        </div>
        <Button onClick={handleOpenCreate}>
          <Plus className="mr-2" size={16} /> Novo Voluntário
        </Button>
      </div>

      {/* Search & Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-mm-muted" size={16} />
            <Input
              placeholder="Buscar por nome, igreja, área, região, especialidade..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              className="pl-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Volunteers List */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg font-medium">Voluntários Cadastrados</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-xs uppercase text-mm-muted">
                <tr>
                  <th className="px-4 py-3">Nome</th>
                  <th className="px-4 py-3">Igreja</th>
                  <th className="px-4 py-3">Área de Atuação</th>
                  <th className="px-4 py-3">Região</th>
                  <th className="px-4 py-3">Especialidade</th>
                  <th className="px-4 py-3 text-center">Ações</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-mm-muted">
                      Carregando voluntários...
                    </td>
                  </tr>
                ) : filteredVoluntarios.length > 0 ? (
                  filteredVoluntarios.map((v) => (
                    <tr key={v.id} className="border-t hover:bg-muted/30">
                      <td className="px-4 py-3 font-medium text-foreground">{v.nome}</td>
                      <td className="px-4 py-3 text-mm-muted">{v.igreja || "—"}</td>
                      <td className="px-4 py-3 text-mm-muted">{v.area || "—"}</td>
                      <td className="px-4 py-3 text-mm-muted">{v.regiao || "—"}</td>
                      <td className="px-4 py-3 text-mm-muted">{v.especialidade || "—"}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2"
                            onClick={() => handleOpenEdit(v)}
                          >
                            <Edit2 size={12} className="mr-1" /> Editar
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 px-2 text-destructive hover:bg-destructive/10"
                            onClick={() => setDeletingVoluntario(v)}
                          >
                            <Trash2 size={12} className="mr-1" /> Excluir
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-mm-muted">
                      Nenhum voluntário encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative flex flex-col w-full max-w-lg bg-white rounded-lg shadow-mm-lg overflow-hidden border border-mm-borderc">
            <div className="flex items-center justify-between px-6 py-4 bg-mm-primary text-white">
              <h2 className="text-lg font-semibold font-display">
                {editingVoluntario ? "Editar Voluntário" : "Cadastrar Voluntário"}
              </h2>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 text-white/80 hover:text-white rounded hover:bg-white/10 transition-colors"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={form.handleSubmit(onSubmit)} className="p-6 space-y-4">
              {/* Nome */}
              <div className="space-y-1.5">
                <Label htmlFor="nome">Nome Completo</Label>
                <Input
                  id="nome"
                  placeholder="Nome do voluntário"
                  {...form.register("nome")}
                />
                {form.formState.errors.nome && (
                  <p className="text-xs text-destructive">{form.formState.errors.nome.message}</p>
                )}
              </div>

              {/* Igreja */}
              <div className="space-y-1.5">
                <Label htmlFor="igreja">Igreja</Label>
                <Input
                  id="igreja"
                  placeholder="Nome da igreja/comunidade"
                  {...form.register("igreja")}
                />
              </div>

              {/* Area */}
              <div className="space-y-1.5">
                <Label htmlFor="area">Área de Atuação</Label>
                <Input
                  id="area"
                  placeholder="Ex: Cantina, Alojamentos, Som, Louvor"
                  {...form.register("area")}
                />
              </div>

              {/* Regiao */}
              <div className="space-y-1.5">
                <Label htmlFor="regiao">Região</Label>
                <Input
                  id="regiao"
                  placeholder="Ex: Região Central, Zona Sul, Cidade"
                  {...form.register("regiao")}
                />
              </div>

              {/* Especialidade */}
              <div className="space-y-1.5">
                <Label htmlFor="especialidade">Especialidade / Habilidade</Label>
                <Input
                  id="especialidade"
                  placeholder="Ex: Cozinheiro, Eletricista, Motorista"
                  {...form.register("especialidade")}
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-mm-borderc">
                <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting ? "Salvando..." : "Salvar"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingVoluntario && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative flex flex-col w-full max-w-md bg-white rounded-lg shadow-mm-lg overflow-hidden border border-mm-borderc">
            <div className="flex items-center gap-3 px-6 py-4 bg-destructive text-white">
              <AlertTriangle size={20} />
              <h2 className="text-lg font-semibold font-display">Confirmar Exclusão</h2>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-sm text-mm-ink">
                Tem certeza que deseja excluir o voluntário{" "}
                <span className="font-bold">{deletingVoluntario.nome}</span>? Esta ação não pode ser
                desfeita.
              </p>

              <div className="flex justify-end gap-3 pt-4 border-t border-mm-borderc">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDeletingVoluntario(null)}
                >
                  Cancelar
                </Button>
                <Button variant="destructive" onClick={handleDeleteConfirm}>
                  Excluir
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

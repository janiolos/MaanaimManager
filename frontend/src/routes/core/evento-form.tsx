import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, Save } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useCentrosCusto, useUsers } from "@/routes/core/hooks";
import type { Evento } from "@/routes/core/types";

const schema = z.object({
  nome: z.string().min(1, "Informe o nome"),
  data_inicio: z.string().min(1, "Informe a data de início"),
  data_fim: z.string().min(1, "Informe a data de término"),
  status: z.enum(["PLANEJADO", "EM_ANDAMENTO", "ENCERRADO"]),
  ativo: z.boolean().default(true),
  fechado: z.boolean().default(false),
  taxa_base: z.string().default("50.00"),
  taxa_trabalhador: z.string().default("25.00"),
  adicional_chale: z.string().default("100.00"),
  prev_participantes: z.string().nullable().optional(),
  prev_trabalhadores: z.string().nullable().optional(),
  observacoes: z.string().default(""),
  centro_custo_id: z.string().nullable().optional(),
  responsavel_geral_id: z.string().nullable().optional(),
});

type FormValues = z.input<typeof schema>;

function toLocalDatetimeString(isoString: string): string {
  if (!isoString) return "";
  const d = new Date(isoString);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => n.toString().padStart(2, "0");
  const year = d.getFullYear();
  const month = pad(d.getMonth() + 1);
  const day = pad(d.getDate());
  const hours = pad(d.getHours());
  const minutes = pad(d.getMinutes());
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function EventoFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const { data: centrosCusto = [] } = useCentrosCusto();
  const { data: users = [] } = useUsers();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      nome: "",
      data_inicio: "",
      data_fim: "",
      status: "PLANEJADO",
      ativo: true,
      fechado: false,
      taxa_base: "50.00",
      taxa_trabalhador: "25.00",
      adicional_chale: "100.00",
      prev_participantes: "",
      prev_trabalhadores: "",
      observacoes: "",
      centro_custo_id: "",
      responsavel_geral_id: "",
    },
  });

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Evento>(`/core/eventos/${id}`)
      .then((res) => {
        const e = res.data;
        form.reset({
          nome: e.nome,
          data_inicio: toLocalDatetimeString(e.data_inicio),
          data_fim: toLocalDatetimeString(e.data_fim),
          status: e.status,
          ativo: e.ativo,
          fechado: e.fechado,
          taxa_base: String(e.taxa_base),
          taxa_trabalhador: String(e.taxa_trabalhador),
          adicional_chale: String(e.adicional_chale),
          prev_participantes: e.prev_participantes !== null ? String(e.prev_participantes) : "",
          prev_trabalhadores: e.prev_trabalhadores !== null ? String(e.prev_trabalhadores) : "",
          observacoes: e.observacoes || "",
          centro_custo_id: e.centro_custo_id !== null ? String(e.centro_custo_id) : "",
          responsavel_geral_id: e.responsavel_geral_id !== null ? String(e.responsavel_geral_id) : "",
        });
      })
      .catch(() => toast.error("Evento não encontrado"));
  }, [id, isEdit, form]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = {
      nome: values.nome,
      data_inicio: new Date(values.data_inicio).toISOString(),
      data_fim: new Date(values.data_fim).toISOString(),
      status: values.status,
      ativo: values.ativo,
      fechado: values.fechado,
      taxa_base: Number(values.taxa_base),
      taxa_trabalhador: Number(values.taxa_trabalhador),
      adicional_chale: Number(values.adicional_chale),
      prev_participantes: values.prev_participantes ? Number(values.prev_participantes) : null,
      prev_trabalhadores: values.prev_trabalhadores ? Number(values.prev_trabalhadores) : null,
      observacoes: values.observacoes,
      centro_custo_id: values.centro_custo_id ? Number(values.centro_custo_id) : null,
      responsavel_geral_id: values.responsavel_geral_id ? Number(values.responsavel_geral_id) : null,
    };

    try {
      if (isEdit) {
        await api.patch(`/core/eventos/${id}`, payload);
        toast.success("Evento atualizado com sucesso!");
      } else {
        await api.post(`/core/eventos`, payload);
        toast.success("Evento criado com sucesso!");
      }
      navigate("/core/eventos");
    } catch {
      toast.error("Falha ao salvar evento. Verifique os campos.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/core/eventos")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar Ciclo de Evento" : "Novo Ciclo de Evento"}
        </h1>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-medium">Informações Gerais</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              {/* Nome */}
              <div className="space-y-1.5 md:col-span-3">
                <Label htmlFor="nome">Nome do Ciclo</Label>
                <Input id="nome" placeholder="Ex: 50º Seminário Maanaim" {...form.register("nome")} />
                {form.formState.errors.nome && (
                  <p className="text-xs text-destructive">{form.formState.errors.nome.message}</p>
                )}
              </div>

              {/* Data Início */}
              <div className="space-y-1.5">
                <Label htmlFor="data_inicio">Data de Início</Label>
                <Input id="data_inicio" type="datetime-local" {...form.register("data_inicio")} />
                {form.formState.errors.data_inicio && (
                  <p className="text-xs text-destructive">{form.formState.errors.data_inicio.message}</p>
                )}
              </div>

              {/* Data Fim */}
              <div className="space-y-1.5">
                <Label htmlFor="data_fim">Data de Término</Label>
                <Input id="data_fim" type="datetime-local" {...form.register("data_fim")} />
                {form.formState.errors.data_fim && (
                  <p className="text-xs text-destructive">{form.formState.errors.data_fim.message}</p>
                )}
              </div>

              {/* Status */}
              <div className="space-y-1.5">
                <Label htmlFor="status">Status</Label>
                <select
                  id="status"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("status")}
                >
                  <option value="PLANEJADO">Planejado</option>
                  <option value="EM_ANDAMENTO">Em andamento</option>
                  <option value="ENCERRADO">Encerrado</option>
                </select>
              </div>

              {/* Centro de Custo */}
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="centro_custo_id">Centro de Custo</Label>
                <select
                  id="centro_custo_id"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("centro_custo_id")}
                >
                  <option value="">Nenhum</option>
                  {centrosCusto.map((cc) => (
                    <option key={cc.id} value={cc.id}>
                      {cc.codigo} - {cc.nome}
                    </option>
                  ))}
                </select>
              </div>

              {/* Responsável Geral */}
              <div className="space-y-1.5">
                <Label htmlFor="responsavel_geral_id">Responsável Geral</Label>
                <select
                  id="responsavel_geral_id"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("responsavel_geral_id")}
                >
                  <option value="">Nenhum</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {`${u.first_name} ${u.last_name}`.trim() || u.username}
                    </option>
                  ))}
                </select>
              </div>

              {/* Ativo */}
              <div className="flex items-center gap-2 pt-6">
                <input
                  id="ativo"
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  {...form.register("ativo")}
                />
                <Label htmlFor="ativo" className="cursor-pointer">Ciclo Ativo</Label>
              </div>

              {/* Fechado */}
              <div className="flex items-center gap-2 pt-6">
                <input
                  id="fechado"
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                  {...form.register("fechado")}
                />
                <Label htmlFor="fechado" className="cursor-pointer">Ciclo Fechado (Bloquear Edições)</Label>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-medium">Taxas e Previsões Financeiras</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-3">
              {/* Taxa Base */}
              <div className="space-y-1.5">
                <Label htmlFor="taxa_base">Taxa Base (R$)</Label>
                <Input id="taxa_base" type="number" step="0.01" {...form.register("taxa_base")} />
              </div>

              {/* Taxa Trabalhador */}
              <div className="space-y-1.5">
                <Label htmlFor="taxa_trabalhador">Taxa Trabalhador (R$)</Label>
                <Input id="taxa_trabalhador" type="number" step="0.01" {...form.register("taxa_trabalhador")} />
              </div>

              {/* Adicional Chalé */}
              <div className="space-y-1.5">
                <Label htmlFor="adicional_chale">Adicional Chalé (R$)</Label>
                <Input id="adicional_chale" type="number" step="0.01" {...form.register("adicional_chale")} />
              </div>

              {/* Previsão Participantes */}
              <div className="space-y-1.5">
                <Label htmlFor="prev_participantes">Previsão de Participantes</Label>
                <Input id="prev_participantes" type="number" {...form.register("prev_participantes")} />
              </div>

              {/* Previsão Trabalhadores */}
              <div className="space-y-1.5">
                <Label htmlFor="prev_trabalhadores">Previsão de Trabalhadores</Label>
                <Input id="prev_trabalhadores" type="number" {...form.register("prev_trabalhadores")} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-medium">Observações</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              <textarea
                id="observacoes"
                rows={4}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Notas, detalhes adicionais ou informações importantes sobre o ciclo..."
                {...form.register("observacoes")}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate("/core/eventos")}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saving}>
            <Save className="mr-2" size={16} />
            {saving ? "Salvando..." : "Salvar Ciclo"}
          </Button>
        </div>
      </form>
    </div>
  );
}

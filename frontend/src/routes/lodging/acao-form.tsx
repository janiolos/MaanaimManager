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
import { useChales } from "@/routes/lodging/hooks";
import { ACAO_TIPO_LABELS } from "@/routes/lodging/types";
import type { Acao } from "@/routes/lodging/types";

const schema = z.object({
  chale_id: z.coerce.number().int().positive("Selecione chalé"),
  tipo: z.enum(["BLOQUEIO", "MANUTENCAO"]),
  titulo: z.string().min(1, "Título obrigatório"),
  data_inicio: z.string().min(1, "Data início"),
  data_fim: z.string().min(1, "Data fim"),
  descricao: z.string().default(""),
  ativo: z.boolean().default(true),
});

type FormValues = z.input<typeof schema>;

export function AcaoFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const { data: chales } = useChales();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { tipo: "BLOQUEIO", ativo: true, descricao: "" },
  });

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Acao>(`/lodging/acoes/${id}`)
      .then((res) => {
        const a = res.data;
        form.reset({
          chale_id: String(a.chale_id) as unknown as number,
          tipo: a.tipo as FormValues["tipo"],
          titulo: a.titulo,
          data_inicio: a.data_inicio,
          data_fim: a.data_fim,
          descricao: a.descricao,
          ativo: a.ativo,
        });
      })
      .catch(() => toast.error("Ação não encontrada"));
  }, [id, isEdit, form]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    try {
      if (isEdit) {
        await api.patch(`/lodging/acoes/${id}`, values);
        toast.success("Ação atualizada");
      } else {
        await api.post(`/lodging/acoes`, values);
        toast.success("Ação criada");
      }
      navigate("/lodging/acoes");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/lodging/acoes")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar ação" : "Nova ação de chalé"}
        </h1>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Dados da ação</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Chalé</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("chale_id")}
                >
                  <option value="0">Selecione...</option>
                  {chales?.map((c) => (
                    <option key={c.id} value={c.id}>{c.codigo}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label>Tipo</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("tipo")}
                >
                  {Object.entries(ACAO_TIPO_LABELS).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="titulo">Título</Label>
                <Input id="titulo" {...form.register("titulo")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="data_inicio">Data início</Label>
                <Input id="data_inicio" type="date" {...form.register("data_inicio")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="data_fim">Data fim</Label>
                <Input id="data_fim" type="date" {...form.register("data_fim")} />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="descricao">Descrição</Label>
                <textarea
                  id="descricao"
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("descricao")}
                />
              </div>
              <div className="space-y-1.5 flex items-center gap-2 pt-6">
                <Input id="ativo" type="checkbox" {...form.register("ativo")} className="h-4 w-4" />
                <Label htmlFor="ativo">Ativa</Label>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" type="button" onClick={() => navigate("/lodging/acoes")}>Cancelar</Button>
              <Button type="submit" disabled={saving}>
                <Save className="mr-2" size={16} /> {saving ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
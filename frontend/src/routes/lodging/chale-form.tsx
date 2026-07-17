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
import type { Chale } from "@/routes/lodging/types";

const schema = z.object({
  codigo: z.string().min(1, "Informe o código"),
  capacidade: z.coerce.number().int().positive("Capacidade > 0"),
  status: z.enum(["ATIVO", "MANUTENCAO", "INATIVO"]),
  acessivel_cadeirante: z.boolean().default(false),
  observacoes: z.string().default(""),
});

type FormValues = z.input<typeof schema>;

export function ChaleFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { status: "ATIVO", acessivel_cadeirante: false, observacoes: "" },
  });

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Chale>(`/lodging/chales/${id}`)
      .then((res) => {
        const c = res.data;
        form.reset({
          codigo: c.codigo,
          capacidade: c.capacidade as unknown as number,
          status: c.status as FormValues["status"],
          acessivel_cadeirante: c.acessivel_cadeirante,
          observacoes: c.observacoes,
        });
      })
      .catch(() => toast.error("Chalé não encontrado"));
  }, [id, isEdit, form]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    try {
      if (isEdit) {
        await api.patch(`/lodging/chales/${id}`, values);
        toast.success("Chalé atualizado");
      } else {
        await api.post(`/lodging/chales`, values);
        toast.success("Chalé criado");
      }
      navigate("/lodging/chales");
    } catch {
      toast.error("Falha ao salvar - código duplicado?");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/lodging/chales")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar chalé" : "Novo chalé"}
        </h1>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Dados do chalé</CardTitle></CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="codigo">Código</Label>
                <Input id="codigo" placeholder="ex: CHA-01" {...form.register("codigo")} />
                {form.formState.errors.codigo && (
                  <p className="text-xs text-destructive">{form.formState.errors.codigo.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="capacidade">Capacidade</Label>
                <Input id="capacidade" type="number" min={1} {...form.register("capacidade")} />
                {form.formState.errors.capacidade && (
                  <p className="text-xs text-destructive">{form.formState.errors.capacidade.message}</p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label>Status</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("status")}
                >
                  <option value="ATIVO">Ativo</option>
                  <option value="MANUTENCAO">Manutenção</option>
                  <option value="INATIVO">Inativo</option>
                </select>
              </div>
              <div className="space-y-1.5 flex items-center gap-2 pt-6">
                <Input id="acessivel" type="checkbox" {...form.register("acessivel_cadeirante")} className="h-4 w-4" />
                <Label htmlFor="acessivel">Acessível cadeirante</Label>
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="observacoes">Observações</Label>
                <textarea
                  id="observacoes"
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("observacoes")}
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" type="button" onClick={() => navigate("/lodging/chales")}>Cancelar</Button>
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
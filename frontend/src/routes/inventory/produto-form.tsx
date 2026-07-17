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
import type { Produto } from "@/routes/inventory/types";

const schema = z.object({
  nome: z.string().min(1, "Informe o nome"),
  sku: z.string().min(1, "Informe o SKU"),
  categoria: z.enum(["MATERIA_PRIMA", "PRODUTO_ACABADO", "COMPONENTE"]),
  unidade: z.string().min(1, "UN, KG, L, ..."),
  estoque_minimo: z.string().default("0"),
  estoque_reabastecimento: z.string().default("0"),
  estoque_maximo: z.string().default("0"),
  ativo: z.boolean().default(true),
});

type FormValues = z.input<typeof schema>;

export function ProdutoFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      categoria: "MATERIA_PRIMA",
      unidade: "UN",
      estoque_minimo: "0",
      estoque_reabastecimento: "0",
      estoque_maximo: "0",
      ativo: true,
    },
  });

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Produto>(`/inventory/produtos/${id}`)
      .then((res) => {
        const p = res.data;
        form.reset({
          nome: p.nome,
          sku: p.sku,
          categoria: p.categoria as FormValues["categoria"],
          unidade: p.unidade,
          estoque_minimo: p.estoque_minimo,
          estoque_reabastecimento: p.estoque_reabastecimento,
          estoque_maximo: p.estoque_maximo,
          ativo: p.ativo,
        });
      })
      .catch(() => toast.error("Produto não encontrado"));
  }, [id, isEdit, form]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = {
      ...values,
      estoque_minimo: Number(values.estoque_minimo),
      estoque_reabastecimento: Number(values.estoque_reabastecimento),
      estoque_maximo: Number(values.estoque_maximo),
    };
    try {
      if (isEdit) {
        await api.patch(`/inventory/produtos/${id}`, payload);
        toast.success("Produto atualizado");
      } else {
        await api.post(`/inventory/produtos`, payload);
        toast.success("Produto criado");
      }
      navigate("/inventory/produtos");
    } catch {
      toast.error("Falha ao salvar - SKU duplicado?");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/inventory/produtos")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar produto" : "Novo produto"}
        </h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Dados do produto</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="nome">Nome</Label>
                <Input id="nome" {...form.register("nome")} />
                {form.formState.errors.nome && (
                  <p className="text-xs text-destructive">{form.formState.errors.nome.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="sku">SKU</Label>
                <Input id="sku" {...form.register("sku")} placeholder="ex: PROD-001" />
                {form.formState.errors.sku && (
                  <p className="text-xs text-destructive">{form.formState.errors.sku.message}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <Label>Categoria</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("categoria")}
                >
                  <option value="MATERIA_PRIMA">Matéria-prima</option>
                  <option value="PRODUTO_ACABADO">Produto acabado</option>
                  <option value="COMPONENTE">Componente</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="unidade">Unidade</Label>
                <Input id="unidade" placeholder="UN, KG, L" {...form.register("unidade")} />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="estoque_minimo">Estoque mínimo</Label>
                <Input
                  id="estoque_minimo"
                  type="number"
                  step="0.01"
                  {...form.register("estoque_minimo")}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="estoque_reabastecimento">Ponto de reabastecimento</Label>
                <Input
                  id="estoque_reabastecimento"
                  type="number"
                  step="0.01"
                  {...form.register("estoque_reabastecimento")}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="estoque_maximo">Estoque máximo</Label>
                <Input
                  id="estoque_maximo"
                  type="number"
                  step="0.01"
                  {...form.register("estoque_maximo")}
                />
              </div>

              <div className="space-y-1.5 flex items-center gap-2 pt-6">
                <Input
                  id="ativo"
                  type="checkbox"
                  {...form.register("ativo")}
                  className="h-4 w-4"
                />
                <Label htmlFor="ativo">Ativo</Label>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" type="button" onClick={() => navigate("/inventory/produtos")}>
                Cancelar
              </Button>
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
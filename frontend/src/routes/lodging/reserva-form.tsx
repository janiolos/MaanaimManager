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
import { useContas } from "@/routes/finance/hooks";
import { FORMA_PAGAMENTO_LABELS } from "@/routes/lodging/types";
import type { Reserva } from "@/routes/lodging/types";

const schema = z.object({
  chale_id: z.coerce.number().int().positive("Selecione o chalé"),
  data_entrada: z.string().min(1, "Data obrigatória"),
  data_saida: z.string().min(1, "Data obrigatória"),
  responsavel_nome: z.string().min(1, "Responsável obrigatório"),
  qtd_pessoas: z.coerce.number().int().positive(">= 1"),
  qtd_criancas: z.coerce.number().int().min(0).default(0),
  idades_criancas: z.string().default(""),
  possui_necessidade_especial: z.boolean().default(false),
  detalhes_necessidade_especial: z.string().default(""),
  valor_adicional: z.string().default("0"),
  pago: z.boolean().default(false),
  forma_pagamento: z.string().default(""),
  conta_id: z.string().default(""),
  observacoes: z.string().default(""),
});

type FormValues = z.input<typeof schema>;

export function ReservaFormPage() {
  const { id } = useParams<{ id?: string }>();
  const isEdit = Boolean(id);
  const navigate = useNavigate();
  const [saving, setSaving] = useState(false);
  const { data: chales } = useChales("ATIVO");
  const { data: contas } = useContas();

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      qtd_pessoas: 1 as unknown as number,
      qtd_criancas: 0 as unknown as number,
      possui_necessidade_especial: false,
      detalhes_necessidade_especial: "",
      valor_adicional: "0",
      pago: false,
      forma_pagamento: "",
      conta_id: "",
      observacoes: "",
    },
  });

  const possuiNecessidade = form.watch("possui_necessidade_especial");
  const pago = form.watch("pago");

  useEffect(() => {
    if (!isEdit) return;
    api
      .get<Reserva>(`/lodging/reservas/${id}`)
      .then((res) => {
        const r = res.data;
        if (r.status === "CANCELADA") {
          toast.error("Reserva cancelada não pode ser editada");
          navigate("/lodging/reservas");
          return;
        }
        form.reset({
          chale_id: String(r.chale_id) as unknown as number,
          data_entrada: r.data_entrada ?? "",
          data_saida: r.data_saida ?? "",
          responsavel_nome: r.responsavel_nome,
          qtd_pessoas: r.qtd_pessoas as unknown as number,
          qtd_criancas: r.qtd_criancas as unknown as number,
          idades_criancas: r.idades_criancas,
          possui_necessidade_especial: r.possui_necessidade_especial,
          detalhes_necessidade_especial: r.detalhes_necessidade_especial,
          valor_adicional: r.valor_adicional,
          pago: r.pago,
          forma_pagamento: r.forma_pagamento,
          conta_id: r.conta_id ? String(r.conta_id) : "",
          observacoes: r.observacoes,
        });
      })
      .catch(() => toast.error("Reserva não encontrada"));
  }, [id, isEdit, form, navigate]);

  async function onSubmit(values: FormValues) {
    setSaving(true);
    const payload = {
      ...values,
      valor_adicional: Number(values.valor_adicional),
      conta_id: values.conta_id ? Number(values.conta_id) : null,
    };
    try {
      if (isEdit) {
        await api.patch(`/lodging/reservas/${id}`, payload);
        toast.success("Reserva atualizada");
      } else {
        await api.post(`/lodging/reservas`, payload);
        toast.success("Reserva criada");
      }
      navigate("/lodging/reservas");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Falha ao salvar");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate("/lodging/reservas")}>
          <ArrowLeft size={18} />
        </Button>
        <h1 className="text-2xl font-semibold font-display">
          {isEdit ? "Editar reserva" : "Nova reserva"}
        </h1>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">Dados da reserva</CardTitle></CardHeader>
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
                    <option key={c.id} value={c.id}>
                      {c.codigo} (cap: {c.capacidade})
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="responsavel_nome">Responsável</Label>
                <Input id="responsavel_nome" {...form.register("responsavel_nome")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="data_entrada">Data entrada</Label>
                <Input id="data_entrada" type="date" {...form.register("data_entrada")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="data_saida">Data saída</Label>
                <Input id="data_saida" type="date" {...form.register("data_saida")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="qtd_pessoas">Adultos</Label>
                <Input id="qtd_pessoas" type="number" min={1} {...form.register("qtd_pessoas")} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="qtd_criancas">Crianças</Label>
                <Input id="qtd_criancas" type="number" min={0} {...form.register("qtd_criancas")} />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="idades_criancas">Idades das crianças (CSV)</Label>
                <Input id="idades_criancas" placeholder="ex: 5,8,12" {...form.register("idades_criancas")} />
              </div>

              <div className="space-y-1.5 flex items-center gap-2 pt-6">
                <Input id="necessidade" type="checkbox" {...form.register("possui_necessidade_especial")} className="h-4 w-4" />
                <Label htmlFor="necessidade">Possui necessidade especial</Label>
              </div>
              {possuiNecessidade && (
                <div className="space-y-1.5 md:col-span-2">
                  <Label htmlFor="detalhes">Detalhes das necessidades *</Label>
                  <textarea
                    id="detalhes"
                    className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    {...form.register("detalhes_necessidade_especial")}
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="valor_adicional">Valor adicional (R$)</Label>
                <Input id="valor_adicional" type="number" step="0.01" {...form.register("valor_adicional")} />
              </div>
              <div className="space-y-1.5 flex items-center gap-2 pt-6">
                <Input id="pago" type="checkbox" {...form.register("pago")} className="h-4 w-4" />
                <Label htmlFor="pago">Pago (gera lançamento receita)</Label>
              </div>
              {pago && (
                <>
                  <div className="space-y-1.5">
                    <Label>Forma de pagamento</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...form.register("forma_pagamento")}
                    >
                      <option value="">Selecione...</option>
                      {Object.entries(FORMA_PAGAMENTO_LABELS).map(([v, l]) => (
                        <option key={v} value={v}>{l}</option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <Label>Conta</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                      {...form.register("conta_id")}
                    >
                      <option value="">Selecione...</option>
                      {contas?.map((c) => (
                        <option key={c.id} value={c.id}>{c.nome}</option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="observacoes">Observações</Label>
                <textarea
                  id="observacoes"
                  className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  {...form.register("observacoes")}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" type="button" onClick={() => navigate("/lodging/reservas")}>
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
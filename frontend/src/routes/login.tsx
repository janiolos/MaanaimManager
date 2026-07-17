import { zodResolver } from "@hookform/resolvers/zod";
import { LockKeyhole, User } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { useAuthStore, type User as AuthUser } from "@/stores/auth-store";

const schema = z.object({
  username: z.string().min(1, "Informe o usuário"),
  password: z.string().min(1, "Informe a senha"),
});

type FormValues = z.infer<typeof schema>;

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export function LoginPage() {
  const { user, login } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitting, setSubmitting] = useState(false);

  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { username: "", password: "" },
  });

  async function onSubmit(values: FormValues) {
    setSubmitting(true);
    try {
      const { data } = await api.post<LoginResponse>("/auth/login", values);
      login(data.access_token, data.user);
      toast.success(`Bem-vindo, ${data.user.first_name || data.user.username}`);
      navigate(from, { replace: true });
    } catch (err) {
      toast.error("Usuário ou senha inválidos");
    } finally {
      setSubmitting(false);
    }
  }

  if (user) return <Navigate to={from} replace />;

  return (
    <div className="min-h-screen grid place-items-center bg-mm-bg px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto mb-2 grid place-items-center h-12 w-12 rounded bg-mm-accent text-white font-bold text-lg">
            M
          </div>
          <CardTitle className="text-xl">Maanaim Manager</CardTitle>
          <CardDescription>Acesse sua conta para continuar</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Usuário</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-mm-muted" size={16} />
                <Input
                  id="username"
                  placeholder="usuário"
                  className="pl-9"
                  autoComplete="username"
                  {...form.register("username")}
                />
              </div>
              {form.formState.errors.username && (
                <p className="text-xs text-destructive">{form.formState.errors.username.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <LockKeyhole className="absolute left-3 top-1/2 -translate-y-1/2 text-mm-muted" size={16} />
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  className="pl-9"
                  autoComplete="current-password"
                  {...form.register("password")}
                />
              </div>
              {form.formState.errors.password && (
                <p className="text-xs text-destructive">{form.formState.errors.password.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
import { zodResolver } from "@hookform/resolvers/zod";
import { ChevronDown, CircleAlert, Eye, EyeOff, LoaderCircle } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useDemoAccounts } from "@/features/auth/api";
import { destinationAfterSignIn } from "@/features/auth/redirects";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

const schema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "Enter your email address.")
    .pipe(z.email("Enter a valid email address.")),
  password: z.string().min(1, "Enter your password."),
});

type LoginForm = z.infer<typeof schema>;

export function LoginPage() {
  const { status, user, signIn } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const next = searchParams.get("next");
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [demoOpen, setDemoOpen] = useState(false);
  const demo = useDemoAccounts();

  const {
    register,
    handleSubmit,
    setError,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  if (status === "signed-in" && user) {
    return <Navigate to={destinationAfterSignIn(user, next)} replace />;
  }

  async function submit(values: LoginForm) {
    setFormError(null);
    try {
      const signedIn = await signIn(values.email, values.password);
      navigate(destinationAfterSignIn(signedIn, next), { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        for (const [field, messages] of Object.entries(error.fields)) {
          if (field === "email" || field === "password") {
            setError(field, { message: messages[0] });
          }
        }
        setFormError(error.message);
      } else {
        setFormError("Something went wrong. Please try again.");
      }
    }
  }

  function signInAs(email: string, password: string) {
    setValue("email", email);
    setValue("password", password);
    void handleSubmit(submit)();
  }

  return (
    <div>
      <h1 className="text-2xl text-foreground">Sign in</h1>
      <p className="mt-1 text-muted-foreground">Use the email address of your FabriSee account.</p>

      <form onSubmit={handleSubmit(submit)} noValidate className="mt-8 flex flex-col gap-5">
        {formError && (
          <p
            role="alert"
            className="flex items-start gap-2 rounded-md border border-status-changes-border bg-status-changes-bg px-3 py-2 text-status-changes"
          >
            <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <span>{formError}</span>
          </p>
        )}

        <div className="flex flex-col gap-2">
          <Label htmlFor="email">Email address</Label>
          <Input
            id="email"
            type="email"
            autoComplete="username"
            autoFocus
            inputMode="email"
            aria-invalid={errors.email ? true : undefined}
            aria-describedby={errors.email ? "email-error" : undefined}
            {...register("email")}
          />
          {errors.email && (
            <p id="email-error" className="text-sm text-destructive">
              {errors.email.message}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between gap-2">
            <Label htmlFor="password">Password</Label>
            <Link
              to="/forgot-password"
              className="rounded-sm text-sm font-medium text-link underline-offset-2 hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              className="pr-11"
              aria-invalid={errors.password ? true : undefined}
              aria-describedby={errors.password ? "password-error" : undefined}
              {...register("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((value) => !value)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              aria-pressed={showPassword}
              className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-md text-muted-foreground -outline-offset-2 hover:text-foreground"
            >
              {showPassword ? (
                <EyeOff className="size-4" aria-hidden="true" />
              ) : (
                <Eye className="size-4" aria-hidden="true" />
              )}
            </button>
          </div>
          {errors.password && (
            <p id="password-error" className="text-sm text-destructive">
              {errors.password.message}
            </p>
          )}
        </div>

        <Button type="submit" size="lg" disabled={isSubmitting} className="mt-1 w-full">
          {isSubmitting && <LoaderCircle className="animate-spin" aria-hidden="true" />}
          Sign in
        </Button>
      </form>

      {demo.data && (
        <section className="mt-8 rounded-lg border bg-background">
          <h2>
            <button
              type="button"
              aria-expanded={demoOpen}
              aria-controls="demo-accounts"
              onClick={() => setDemoOpen((value) => !value)}
              className="flex w-full items-center justify-between gap-2 rounded-lg px-4 py-3 text-left text-sm font-medium text-foreground -outline-offset-2"
            >
              Demo accounts
              <ChevronDown
                className={cn(
                  "size-4 text-muted-foreground transition-transform duration-150",
                  demoOpen && "rotate-180",
                )}
                aria-hidden="true"
              />
            </button>
          </h2>
          {demoOpen && (
            <div id="demo-accounts" className="border-t px-2 pt-2 pb-3">
              <p className="px-2 pb-2 text-xs text-muted-foreground">
                Fictitious accounts for trying FabriSee. Choose one to sign in.
              </p>
              <ul className="flex flex-col">
                {demo.data.accounts.map((account) => (
                  <li key={account.email}>
                    <button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => signInAs(account.email, demo.data!.password)}
                      className="flex w-full items-center justify-between gap-3 rounded-md px-2 py-2 text-left transition-colors duration-150 -outline-offset-2 hover:bg-accent"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium text-foreground">
                          {account.full_name}
                        </span>
                        <span className="block truncate text-xs text-muted-foreground">
                          {account.email}
                        </span>
                      </span>
                      <span className="shrink-0 text-right text-xs text-muted-foreground">
                        <span className="block">{account.company ?? account.role_label}</span>
                        {account.company && <span className="block">{account.role_label}</span>}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}

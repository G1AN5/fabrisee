import { ArrowLeft, KeyRound } from "lucide-react";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";

/**
 * Password reset by email arrives with the invitation flow (Milestone 7). Until then the
 * administrator resets passwords, and this page says so plainly.
 */
export function ForgotPasswordPage() {
  return (
    <div>
      <span className="flex size-11 items-center justify-center rounded-full bg-muted text-slate-600">
        <KeyRound className="size-5" aria-hidden="true" />
      </span>
      <h1 className="mt-4 text-2xl text-foreground">Forgot your password?</h1>
      <p className="mt-2 text-muted-foreground">
        Resetting a password by email is not available yet. For now, ask your project manager or the
        FabriSee administrator to set a new password for your account.
      </p>
      <Button asChild variant="outline" className="mt-6">
        <Link to="/login">
          <ArrowLeft aria-hidden="true" />
          Back to sign in
        </Link>
      </Button>
    </div>
  );
}

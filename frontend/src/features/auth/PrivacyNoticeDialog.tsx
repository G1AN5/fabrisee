import { LoaderCircle } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { usePrivacyNotice } from "@/features/auth/api";
import { useAuth } from "@/lib/auth";
import { errorMessage } from "@/lib/errors";

interface PrivacyNoticeDialogProps {
  open: boolean;
  /**
   * `acknowledge`: the first sign-in. The notice cannot be dismissed; the user
   * acknowledges it once or signs out. `read`: opened later from the user menu.
   */
  mode: "acknowledge" | "read";
  onOpenChange?: (open: boolean) => void;
}

/** What personal data FabriSee keeps and why (Data Privacy Act of 2012). */
export function PrivacyNoticeDialog({ open, mode, onOpenChange }: PrivacyNoticeDialogProps) {
  const { acknowledgePrivacy, signOut } = useAuth();
  const notice = usePrivacyNotice(open);
  const [saving, setSaving] = useState(false);
  const mustAcknowledge = mode === "acknowledge";

  async function acknowledge() {
    setSaving(true);
    try {
      await acknowledgePrivacy();
    } catch (error) {
      toast.error(errorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={mustAcknowledge ? undefined : onOpenChange}>
      <DialogContent
        showCloseButton={!mustAcknowledge}
        className="max-w-xl"
        onEscapeKeyDown={(event) => mustAcknowledge && event.preventDefault()}
        onInteractOutside={(event) => mustAcknowledge && event.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{notice.data?.title ?? "Privacy notice"}</DialogTitle>
          <DialogDescription>
            {mustAcknowledge
              ? "Please read this once before you continue."
              : "How FabriSee handles your personal data."}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3 text-foreground">
          {notice.isPending && (
            <>
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </>
          )}
          {notice.isError && (
            <p role="alert" className="text-destructive">
              The privacy notice could not be loaded. {errorMessage(notice.error)}
            </p>
          )}
          {notice.data?.blocks.map((block, index) => {
            if (block.type === "heading") {
              return (
                <h3 key={index} className="mt-2 text-sm font-semibold">
                  {block.text}
                </h3>
              );
            }
            if (block.type === "list") {
              return (
                <ul key={index} className="flex list-disc flex-col gap-1 pl-5">
                  {block.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              );
            }
            return <p key={index}>{block.text}</p>;
          })}
        </div>

        <DialogFooter>
          {mustAcknowledge ? (
            <>
              <Button variant="ghost" disabled={saving} onClick={() => void signOut()}>
                Sign out
              </Button>
              <Button disabled={saving || !notice.data} onClick={() => void acknowledge()}>
                {saving && <LoaderCircle className="animate-spin" aria-hidden="true" />}I have read
                and understood this
              </Button>
            </>
          ) : (
            <Button variant="outline" onClick={() => onOpenChange?.(false)}>
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

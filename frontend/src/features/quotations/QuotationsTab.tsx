import { FileText } from "lucide-react";

import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useProjectQuotations } from "@/features/projects/api";
import { QuotationCard } from "@/features/quotations/QuotationCard";

/** The quotation versions of a project, newest first (staff workspace, read-only). */
export function QuotationsTab({ projectId }: { projectId: number }) {
  const quotations = useProjectQuotations(projectId);

  if (quotations.isPending) {
    return (
      <div aria-hidden="true" className="flex flex-col gap-4">
        <Skeleton className="h-56 rounded-lg" />
        <Skeleton className="h-56 rounded-lg" />
      </div>
    );
  }
  if (quotations.isError) {
    return (
      <Card>
        <ErrorState
          error={quotations.error}
          what="the quotations"
          onRetry={() => void quotations.refetch()}
        />
      </Card>
    );
  }
  if (quotations.data.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={FileText}
          title="No quotation yet"
          description="The project manager uploads the quotation. Accepting it moves the project to Design."
        />
      </Card>
    );
  }
  return (
    <div className="flex flex-col gap-4">
      {quotations.data.map((quotation) => (
        <QuotationCard key={quotation.id} quotation={quotation} />
      ))}
    </div>
  );
}

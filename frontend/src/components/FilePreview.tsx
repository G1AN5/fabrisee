import { Download, ExternalLink, FileText, Maximize2, ZoomIn, ZoomOut } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { inlineUrl } from "@/lib/files";
import { formatFileSize } from "@/lib/format";
import type { FileRef } from "@/lib/types";
import { cn } from "@/lib/utils";

interface FileLinksProps {
  file: FileRef;
  /** Smaller buttons for use inside lists. */
  compact?: boolean;
}

/** "Open" (in a new tab) and "Download" for a file. */
export function FileLinks({ file, compact = false }: FileLinksProps) {
  const size = compact ? "sm" : "default";
  return (
    <span className="flex shrink-0 flex-wrap items-center gap-2">
      <Button asChild variant="outline" size={size}>
        <a href={inlineUrl(file)} target="_blank" rel="noreferrer">
          <ExternalLink aria-hidden="true" />
          Open
          <span className="sr-only"> {file.name} in a new tab</span>
        </a>
      </Button>
      <Button asChild variant="outline" size={size}>
        <a href={file.url} download={file.name}>
          <Download aria-hidden="true" />
          Download
          <span className="sr-only"> {file.name}</span>
        </a>
      </Button>
    </span>
  );
}

/** A file as a row: icon, name, size, and the links to open or download it. */
export function FileRow({ file, label }: { file: FileRef; label?: string }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border bg-card p-3 sm:flex-row sm:items-center">
      <span className="flex min-w-0 flex-1 items-center gap-3">
        <span
          className={cn(
            "flex size-10 shrink-0 items-center justify-center rounded-md",
            file.is_pdf ? "bg-status-changes-bg text-status-changes" : "bg-muted text-slate-600",
          )}
        >
          <FileText className="size-5" aria-hidden="true" />
        </span>
        <span className="min-w-0">
          <span className="block truncate font-medium text-foreground" title={file.name}>
            {label ?? file.name}
          </span>
          <span className="block truncate text-xs text-muted-foreground">
            {label ? `${file.name} · ` : ""}
            {file.is_pdf ? "PDF" : "Image"}
            {file.size_bytes ? ` · ${formatFileSize(file.size_bytes)}` : ""}
          </span>
        </span>
      </span>
      <FileLinks file={file} compact />
    </div>
  );
}

/**
 * Desktop browsers show PDFs with a built-in viewer. Where there is none (most phones, some
 * embedded browsers), the file is offered as a row to open or download.
 */
const PDF_VIEWER_AVAILABLE =
  typeof navigator === "undefined" || navigator.pdfViewerEnabled !== false;

interface FilePreviewProps {
  file: FileRef;
  /** Describes the image, for example "Design R2 of FS-2026-0007". */
  alt: string;
  className?: string;
}

/**
 * Shows a design file large on a neutral canvas. Images can be zoomed and opened full
 * screen. PDFs are shown inline where the browser can do that (desktop); on phones a
 * card offers to open or download the file.
 */
export function FilePreview({ file, alt, className }: FilePreviewProps) {
  const [zoomed, setZoomed] = useState(false);
  const [fullScreen, setFullScreen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const wide = useMediaQuery("(min-width: 768px)");

  if (!file.is_image) {
    if (file.is_pdf && wide && PDF_VIEWER_AVAILABLE) {
      return (
        <div className={cn("flex flex-col gap-3", className)}>
          <object
            data={`${inlineUrl(file)}#view=FitH`}
            type="application/pdf"
            aria-label={alt}
            className="h-[70vh] min-h-96 w-full rounded-lg border bg-slate-100"
          >
            <p className="p-4 text-muted-foreground">
              This PDF could not be shown here. Open or download it below.
            </p>
          </object>
          <FileRow file={file} />
        </div>
      );
    }
    return <FileRow file={file} />;
  }

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div
        className={cn(
          "design-canvas relative overflow-auto rounded-lg border",
          zoomed ? "max-h-[75vh]" : "",
        )}
      >
        {!loaded && !failed && <Skeleton className="aspect-[16/10] w-full rounded-none" />}
        {failed ? (
          <p role="alert" className="px-4 py-14 text-center text-muted-foreground">
            This image could not be shown. Try to download it instead.
          </p>
        ) : (
          <img
            src={inlineUrl(file)}
            alt={alt}
            onLoad={() => setLoaded(true)}
            onError={() => setFailed(true)}
            className={cn(
              "mx-auto block",
              zoomed ? "w-[200%] max-w-none" : "max-h-[70vh] w-full object-contain",
              !loaded && "hidden",
            )}
          />
        )}
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setZoomed((value) => !value)}
            aria-pressed={zoomed}
            disabled={failed}
          >
            {zoomed ? <ZoomOut aria-hidden="true" /> : <ZoomIn aria-hidden="true" />}
            {zoomed ? "Fit to width" : "Zoom in"}
          </Button>
          <Button variant="outline" size="sm" onClick={() => setFullScreen(true)} disabled={failed}>
            <Maximize2 aria-hidden="true" />
            Full screen
          </Button>
        </span>
        <Button asChild variant="outline" size="sm">
          <a href={file.url} download={file.name}>
            <Download aria-hidden="true" />
            Download
            <span className="sr-only"> {file.name}</span>
          </a>
        </Button>
      </div>

      <Dialog open={fullScreen} onOpenChange={setFullScreen}>
        <DialogContent className="h-[calc(100dvh-2rem)] max-w-[calc(100vw-2rem)] grid-rows-[auto_1fr] p-4 sm:max-w-[calc(100vw-2rem)]">
          <DialogHeader>
            <DialogTitle>{alt}</DialogTitle>
            <DialogDescription className="sr-only">
              The design file at full size. Scroll to see all of it.
            </DialogDescription>
          </DialogHeader>
          <div className="design-canvas min-h-0 overflow-auto rounded-md border">
            <img src={inlineUrl(file)} alt={alt} className="mx-auto block h-auto max-w-none" />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

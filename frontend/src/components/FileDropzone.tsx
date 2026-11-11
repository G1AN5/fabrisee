import { CloudUpload, FileText, X } from "lucide-react";
import { type DragEvent, useId, useRef, useState } from "react";

import { MAX_UPLOAD_MB } from "@/lib/constants";
import {
  describeAccepted,
  EXTENSIONS,
  type FileKind,
  type FileRejection,
  kindOf,
  splitFiles,
} from "@/lib/files";
import { formatFileSize } from "@/lib/format";
import { cn } from "@/lib/utils";

// One preview address per selected file. It is released when the file is removed from
// the list; files still listed when the page closes are released by the browser.
const previewUrls = new WeakMap<File, string>();

function previewUrl(file: File): string {
  let url = previewUrls.get(file);
  if (!url) {
    url = URL.createObjectURL(file);
    previewUrls.set(file, url);
  }
  return url;
}

function releasePreview(file: File) {
  const url = previewUrls.get(file);
  if (url) {
    URL.revokeObjectURL(url);
    previewUrls.delete(file);
  }
}

interface FileDropzoneProps {
  files: File[];
  onFilesChange: (files: File[]) => void;
  /** Kinds of files allowed. Default: images and PDF. */
  accept?: FileKind[];
  maxSizeMb?: number;
  /** Allow more than one file. Default: true. */
  multiple?: boolean;
  /** The visible label of the field. */
  label: string;
  disabled?: boolean;
}

/**
 * Choose files by drag and drop or with the file picker. Checks the type and the size
 * before anything is uploaded, says clearly why a file was not added, and previews the
 * files that were.
 */
export function FileDropzone({
  files,
  onFilesChange,
  accept = ["image", "pdf"],
  maxSizeMb = MAX_UPLOAD_MB,
  multiple = true,
  label,
  disabled = false,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const hintId = useId();
  const [dragging, setDragging] = useState(false);
  const [rejections, setRejections] = useState<FileRejection[]>([]);

  const acceptAttribute = accept.flatMap((kind) => EXTENSIONS[kind]).join(",");
  const hint = `${describeAccepted(accept).replace(/^an? /, "")}, up to ${maxSizeMb} MB${multiple ? " each" : ""}`;

  function addFiles(incoming: File[]) {
    if (disabled || incoming.length === 0) return;
    const { accepted, rejected } = splitFiles(incoming, accept, maxSizeMb);
    setRejections(rejected);
    if (accepted.length === 0) return;
    if (!multiple) {
      files.forEach(releasePreview);
      onFilesChange([accepted[0]!]);
      return;
    }
    const known = new Set(files.map((file) => `${file.name}:${file.size}`));
    const fresh = accepted.filter((file) => !known.has(`${file.name}:${file.size}`));
    onFilesChange([...files, ...fresh]);
  }

  function removeFile(file: File) {
    releasePreview(file);
    onFilesChange(files.filter((item) => item !== file));
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    addFiles(Array.from(event.dataTransfer.files));
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center gap-2 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors duration-150 ease-out",
          dragging ? "border-primary bg-status-sent-bg" : "border-input bg-card",
          disabled && "opacity-60",
        )}
      >
        <span className="flex size-10 items-center justify-center rounded-full bg-muted text-slate-600">
          <CloudUpload className="size-5" aria-hidden="true" />
        </span>
        <p className="text-foreground">
          <label htmlFor={inputId} className="font-medium">
            {label}
          </label>
          <span className="block text-muted-foreground">
            Drag files here, or{" "}
            <button
              type="button"
              disabled={disabled}
              onClick={() => inputRef.current?.click()}
              className="rounded-sm font-medium text-link underline underline-offset-2"
            >
              choose {multiple ? "files" : "a file"}
            </button>
          </span>
        </p>
        <p id={hintId} className="text-xs text-muted-foreground first-letter:uppercase">
          {hint}
        </p>
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          className="sr-only"
          tabIndex={-1}
          multiple={multiple}
          accept={acceptAttribute}
          disabled={disabled}
          aria-describedby={hintId}
          onChange={(event) => {
            addFiles(Array.from(event.target.files ?? []));
            // Let the same file be chosen again after it was removed.
            event.target.value = "";
          }}
        />
      </div>

      {rejections.length > 0 && (
        <ul role="alert" className="flex flex-col gap-1 text-sm text-destructive">
          {rejections.map((rejection) => (
            <li key={`${rejection.file.name}:${rejection.file.size}`}>{rejection.reason}</li>
          ))}
        </ul>
      )}

      {files.length > 0 && (
        <ul aria-label="Selected files" className="flex flex-col gap-2">
          {files.map((file) => (
            <li
              key={`${file.name}:${file.size}`}
              className="flex items-center gap-3 rounded-md border bg-card p-2"
            >
              {kindOf(file) === "image" ? (
                <img
                  src={previewUrl(file)}
                  alt=""
                  className="size-12 shrink-0 rounded-sm border object-cover"
                />
              ) : (
                <span className="flex size-12 shrink-0 items-center justify-center rounded-sm bg-status-changes-bg text-status-changes">
                  <FileText className="size-5" aria-hidden="true" />
                </span>
              )}
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium text-foreground" title={file.name}>
                  {file.name}
                </span>
                <span className="block text-xs text-muted-foreground tabular-nums">
                  {formatFileSize(file.size)}
                </span>
              </span>
              <button
                type="button"
                onClick={() => removeFile(file)}
                disabled={disabled}
                aria-label={`Remove ${file.name}`}
                className="flex size-10 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors duration-150 hover:bg-accent hover:text-foreground"
              >
                <X className="size-4" aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

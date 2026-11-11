import { IMAGE_TYPES, PDF_TYPE } from "@/lib/constants";
import type { FileRef } from "@/lib/types";

/** The address that shows a file in the browser instead of downloading it. */
export function inlineUrl(file: Pick<FileRef, "url">): string {
  return `${file.url}?inline=1`;
}

export type FileKind = "image" | "pdf";

export interface FileRejection {
  file: File;
  reason: string;
}

export const EXTENSIONS: Record<FileKind, string[]> = {
  image: [".jpg", ".jpeg", ".png", ".webp"],
  pdf: [".pdf"],
};

export function kindOf(file: File): FileKind | null {
  if (IMAGE_TYPES.includes(file.type)) return "image";
  if (file.type === PDF_TYPE) return "pdf";
  if (file.type !== "") return null;
  // Some browsers give no type: fall back to the extension. The server checks the content.
  const name = file.name.toLowerCase();
  if (EXTENSIONS.image.some((extension) => name.endsWith(extension))) return "image";
  if (EXTENSIONS.pdf.some((extension) => name.endsWith(extension))) return "pdf";
  return null;
}

export function describeAccepted(accept: FileKind[]): string {
  const image = accept.includes("image");
  const pdf = accept.includes("pdf");
  if (image && pdf) return "an image (JPG, PNG, WebP) or a PDF file";
  if (pdf) return "a PDF file";
  return "an image (JPG, PNG, WebP)";
}

/** Why a file cannot be uploaded, or null if it can. Mirrors the checks of the server. */
export function checkFile(file: File, accept: FileKind[], maxSizeMb: number): string | null {
  const kind = kindOf(file);
  if (kind === null || !accept.includes(kind)) {
    return `${file.name} cannot be uploaded. Choose ${describeAccepted(accept)}.`;
  }
  if (file.size > maxSizeMb * 1024 * 1024) {
    return `${file.name} is larger than the ${maxSizeMb} MB limit. Choose a smaller file.`;
  }
  return null;
}

export function splitFiles(
  files: File[],
  accept: FileKind[],
  maxSizeMb: number,
): { accepted: File[]; rejected: FileRejection[] } {
  const accepted: File[] = [];
  const rejected: FileRejection[] = [];
  for (const file of files) {
    const reason = checkFile(file, accept, maxSizeMb);
    if (reason) rejected.push({ file, reason });
    else accepted.push(file);
  }
  return { accepted, rejected };
}

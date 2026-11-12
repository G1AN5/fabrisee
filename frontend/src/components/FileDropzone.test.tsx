import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { FileDropzone } from "@/components/FileDropzone";
import type { FileKind } from "@/lib/files";

function file(name: string, type: string, sizeBytes = 2048): File {
  const made = new File(["x"], name, { type });
  Object.defineProperty(made, "size", { value: sizeBytes });
  return made;
}

interface HarnessProps {
  accept?: FileKind[];
  multiple?: boolean;
  onChange?: (files: File[]) => void;
}

/** The dropzone with the state a form would hold. */
function Harness({ accept, multiple, onChange }: HarnessProps) {
  const [files, setFiles] = useState<File[]>([]);
  return (
    <FileDropzone
      label="Reference files"
      files={files}
      accept={accept}
      multiple={multiple}
      maxSizeMb={20}
      onFilesChange={(next) => {
        setFiles(next);
        onChange?.(next);
      }}
    />
  );
}

function selectedNames(): string[] {
  const list = screen.queryByRole("list", { name: "Selected files" });
  if (!list) return [];
  return within(list)
    .getAllByRole("listitem")
    .map((item) => item.querySelector("[title]")?.getAttribute("title") ?? "");
}

beforeAll(() => {
  // jsdom has no object URLs; the previews only need a string.
  URL.createObjectURL = vi.fn(() => "blob:preview");
  URL.revokeObjectURL = vi.fn();
});

describe("FileDropzone", () => {
  it("says which files are accepted", () => {
    render(<Harness />);

    expect(screen.getByLabelText("Reference files")).toHaveAttribute(
      "accept",
      ".jpg,.jpeg,.png,.webp,.pdf",
    );
    expect(
      screen.getByText(/image \(JPG, PNG, WebP\) or a PDF file, up to 20 MB each/),
    ).toBeInTheDocument();
  });

  it("adds chosen files and lists them with their size", async () => {
    const onChange = vi.fn();
    render(<Harness onChange={onChange} />);

    await userEvent.upload(screen.getByLabelText("Reference files"), [
      file("storefront.png", "image/png"),
      file("brief.pdf", "application/pdf"),
    ]);

    expect(selectedNames()).toEqual(["storefront.png", "brief.pdf"]);
    expect(screen.getAllByText("2 KB")).toHaveLength(2);
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("refuses a file of the wrong type and says why", () => {
    render(<Harness />);

    // A drop is not filtered by the file picker, so the component has to check.
    fireEvent.drop(screen.getByText(/Drag files here/).closest("div")!, {
      dataTransfer: { files: [file("notes.docx", "application/msword")] },
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "notes.docx cannot be uploaded. Choose an image (JPG, PNG, WebP) or a PDF file.",
    );
    expect(selectedNames()).toEqual([]);
  });

  it("refuses a file above the size limit and keeps the good ones", () => {
    render(<Harness />);

    fireEvent.drop(screen.getByText(/Drag files here/).closest("div")!, {
      dataTransfer: {
        files: [
          file("huge.pdf", "application/pdf", 21 * 1024 * 1024),
          file("render.png", "image/png"),
        ],
      },
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "huge.pdf is larger than the 20 MB limit. Choose a smaller file.",
    );
    expect(selectedNames()).toEqual(["render.png"]);
  });

  it("does not add the same file twice", async () => {
    render(<Harness />);
    const input = screen.getByLabelText("Reference files");

    await userEvent.upload(input, file("render.png", "image/png"));
    await userEvent.upload(input, file("render.png", "image/png"));

    expect(selectedNames()).toEqual(["render.png"]);
  });

  it("removes a file with its remove button", async () => {
    render(<Harness />);
    await userEvent.upload(screen.getByLabelText("Reference files"), [
      file("a.png", "image/png"),
      file("b.png", "image/png"),
    ]);

    await userEvent.click(screen.getByRole("button", { name: "Remove a.png" }));

    expect(selectedNames()).toEqual(["b.png"]);
  });

  it("keeps only the newest file when one file is allowed", async () => {
    render(<Harness accept={["pdf"]} multiple={false} />);
    const input = screen.getByLabelText("Reference files");

    expect(input).toHaveAttribute("accept", ".pdf");
    await userEvent.upload(input, file("quotation-v1.pdf", "application/pdf"));
    await userEvent.upload(input, file("quotation-v2.pdf", "application/pdf"));

    expect(selectedNames()).toEqual(["quotation-v2.pdf"]);
  });
});

import { describe, expect, it } from "vitest";

import { checkFile, describeAccepted, inlineUrl, kindOf, splitFiles } from "@/lib/files";

function file(name: string, type: string, sizeBytes = 1024): File {
  const made = new File(["x"], name, { type });
  Object.defineProperty(made, "size", { value: sizeBytes });
  return made;
}

describe("kindOf", () => {
  it("recognizes images and PDF by their type", () => {
    expect(kindOf(file("render.png", "image/png"))).toBe("image");
    expect(kindOf(file("photo.jpg", "image/jpeg"))).toBe("image");
    expect(kindOf(file("render.webp", "image/webp"))).toBe("image");
    expect(kindOf(file("quotation.pdf", "application/pdf"))).toBe("pdf");
  });

  it("falls back to the extension only when the browser gives no type", () => {
    expect(kindOf(file("SCAN.PDF", ""))).toBe("pdf");
    expect(kindOf(file("photo.JPEG", ""))).toBe("image");
    expect(kindOf(file("notes", ""))).toBeNull();
  });

  it("does not trust the extension over a different type", () => {
    expect(kindOf(file("virus.pdf", "application/x-msdownload"))).toBeNull();
    expect(kindOf(file("drawing.dwg", "image/vnd.dwg"))).toBeNull();
    expect(kindOf(file("animation.gif", "image/gif"))).toBeNull();
  });
});

describe("checkFile", () => {
  it("accepts an allowed file within the size limit", () => {
    expect(checkFile(file("render.png", "image/png"), ["image", "pdf"], 20)).toBeNull();
    expect(checkFile(file("big.pdf", "application/pdf", 20 * 1024 * 1024), ["pdf"], 20)).toBeNull();
  });

  it("says which kinds are allowed when the type is wrong", () => {
    expect(checkFile(file("plan.docx", "application/msword"), ["image", "pdf"], 20)).toBe(
      "plan.docx cannot be uploaded. Choose an image (JPG, PNG, WebP) or a PDF file.",
    );
    expect(checkFile(file("render.png", "image/png"), ["pdf"], 20)).toBe(
      "render.png cannot be uploaded. Choose a PDF file.",
    );
    expect(checkFile(file("quote.pdf", "application/pdf"), ["image"], 20)).toBe(
      "quote.pdf cannot be uploaded. Choose an image (JPG, PNG, WebP).",
    );
  });

  it("names the limit when the file is too large", () => {
    const tooLarge = file("render.png", "image/png", 20 * 1024 * 1024 + 1);
    expect(checkFile(tooLarge, ["image"], 20)).toBe(
      "render.png is larger than the 20 MB limit. Choose a smaller file.",
    );
  });
});

describe("splitFiles", () => {
  it("separates the files that can be uploaded from those that cannot, with reasons", () => {
    const good = file("render.png", "image/png");
    const wrongType = file("notes.txt", "text/plain");
    const tooLarge = file("scan.pdf", "application/pdf", 30 * 1024 * 1024);

    const { accepted, rejected } = splitFiles([good, wrongType, tooLarge], ["image", "pdf"], 20);

    expect(accepted).toEqual([good]);
    expect(rejected.map((item) => item.file)).toEqual([wrongType, tooLarge]);
    expect(rejected[0]!.reason).toContain("cannot be uploaded");
    expect(rejected[1]!.reason).toContain("larger than the 20 MB limit");
  });
});

describe("describeAccepted and inlineUrl", () => {
  it("describe the accepted kinds in words", () => {
    expect(describeAccepted(["image", "pdf"])).toBe("an image (JPG, PNG, WebP) or a PDF file");
    expect(describeAccepted(["pdf"])).toBe("a PDF file");
    expect(describeAccepted(["image"])).toBe("an image (JPG, PNG, WebP)");
  });

  it("asks the server to show a file instead of downloading it", () => {
    expect(inlineUrl({ url: "/api/files/render/7/" })).toBe("/api/files/render/7/?inline=1");
  });
});

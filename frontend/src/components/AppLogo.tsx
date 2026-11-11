import { cn } from "@/lib/utils";

interface AppLogoProps {
  /** `inverse` is for dark surfaces (the staff sidebar and the sign-in panel). */
  variant?: "default" | "inverse";
  size?: "sm" | "md" | "lg";
  className?: string;
}

const SIZES = {
  sm: { text: "text-[1.0625rem]", mark: "size-[1.125rem]" },
  md: { text: "text-[1.25rem]", mark: "size-5" },
  lg: { text: "text-[1.75rem]", mark: "size-7" },
} as const;

/**
 * The FabriSee wordmark: "Fabri" in the text color, "See" in blueprint blue, and a small
 * workshop-orange square mark with one cut corner.
 */
export function AppLogo({ variant = "default", size = "md", className }: AppLogoProps) {
  const inverse = variant === "inverse";
  return (
    <span
      role="img"
      aria-label="FabriSee"
      className={cn(
        "inline-flex items-center gap-2 leading-none font-bold tracking-tight select-none",
        SIZES[size].text,
        className,
      )}
    >
      <svg
        viewBox="0 0 32 32"
        aria-hidden="true"
        className={cn("shrink-0", SIZES[size].mark, inverse ? "text-brand-inverse" : "text-brand")}
      >
        <path d="M3 3h18l8 8v18H3z" fill="currentColor" />
      </svg>
      <span aria-hidden="true">
        <span className={inverse ? "text-white" : "text-foreground"}>Fabri</span>
        <span className={inverse ? "text-blue-300" : "text-primary"}>See</span>
      </span>
    </span>
  );
}

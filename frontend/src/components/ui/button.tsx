import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import type * as React from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  [
    "inline-flex shrink-0 items-center justify-center gap-2 rounded-md text-sm font-medium whitespace-nowrap",
    "transition-colors duration-150 ease-out select-none",
    "disabled:pointer-events-none disabled:opacity-50",
    "aria-disabled:pointer-events-none aria-disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  ],
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow-xs hover:bg-primary-hover",
        destructive: "bg-destructive text-destructive-foreground shadow-xs hover:bg-destructive/90",
        outline: "border border-input bg-card text-foreground shadow-xs hover:bg-accent",
        secondary: "bg-secondary text-secondary-foreground hover:bg-slate-200",
        ghost: "text-foreground hover:bg-accent",
        link: "text-link underline-offset-4 hover:underline",
      },
      size: {
        default: "h-(--control-h) px-4",
        sm: "h-(--control-h-sm) gap-1.5 px-3",
        lg: "h-12 px-6 text-base",
        icon: "size-(--control-h)",
        "icon-sm": "size-(--control-h-sm)",
      },
    },
    compoundVariants: [{ variant: "link", className: "h-auto px-0" }],
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

type ButtonProps = React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    /** Render the child element (for example a router link) with button styles. */
    asChild?: boolean;
  };

function Button({ className, variant, size, asChild = false, type, ...props }: ButtonProps) {
  const classes = cn(buttonVariants({ variant, size }), className);
  if (asChild) {
    return <Slot.Root data-slot="button" className={classes} {...props} />;
  }
  // Default to type="button" so a button inside a form never submits it by accident.
  return <button data-slot="button" type={type ?? "button"} className={classes} {...props} />;
}

export { Button, buttonVariants };

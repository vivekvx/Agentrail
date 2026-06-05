import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md border text-sm font-medium tracking-tight transition focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-white disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "border-[#d4d4d8] bg-white text-black hover:bg-[#ebebeb]",
        accent:
          "border-transparent bg-[var(--accent)] text-black hover:bg-emerald-400 font-semibold",
        secondary:
          "border-[#282828] bg-[#111111] text-zinc-200 hover:bg-[#181818] hover:text-white hover:border-[#333]",
        ghost:
          "border-transparent bg-transparent text-zinc-400 hover:border-[var(--border)] hover:bg-[#111111] hover:text-zinc-100",
        danger:
          "border-[var(--danger-border)] bg-[var(--danger-bg)] text-[var(--danger-text)] hover:bg-[rgba(248,113,113,0.12)]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-5 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      {...props}
    />
  ),
);
Button.displayName = "Button";

export { Button, buttonVariants };

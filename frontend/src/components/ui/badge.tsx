import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10.5px] uppercase tracking-[0.14em]",
  {
    variants: {
      variant: {
        neutral:
          "border-[var(--neutral-border)] bg-[var(--neutral-bg)] text-[var(--neutral-text)]",
        success:
          "border-[var(--success-border)] bg-[var(--success-bg)] text-[var(--success-text)]",
        warning:
          "border-[var(--warning-border)] bg-[var(--warning-bg)] text-[var(--warning-text)]",
        danger:
          "border-[var(--danger-border)] bg-[var(--danger-bg)] text-[var(--danger-text)]",
        accent:
          "border-[var(--accent-border)] bg-[var(--accent-dim)] text-[var(--accent)]",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  },
);

export function Badge({
  className,
  variant,
  children,
  dot,
}: React.HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof badgeVariants> & { dot?: boolean }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)}>
      {dot && (
        <span className="size-1.5 rounded-full bg-current opacity-80 shrink-0" />
      )}
      {children}
    </div>
  );
}

import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.16em]",
  {
    variants: {
      variant: {
        neutral: "border-[#2c2c2c] bg-[#101010] text-zinc-300",
        success: "border-[#2f2f2f] bg-[#131313] text-white",
        warning: "border-[#2c2c2c] bg-[#121212] text-zinc-200",
        danger: "border-[#343434] bg-[#151515] text-zinc-100",
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
}: React.HTMLAttributes<HTMLDivElement> & VariantProps<typeof badgeVariants>) {
  return (
    <div className={cn(badgeVariants({ variant }), className)}>{children}</div>
  );
}

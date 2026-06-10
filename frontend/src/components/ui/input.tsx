import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-11 w-full rounded-md border border-[var(--border)] bg-[#0b0b0b] px-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-500 focus:border-[rgba(16,185,129,0.4)] focus:ring-1 focus:ring-[rgba(16,185,129,0.12)] transition",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

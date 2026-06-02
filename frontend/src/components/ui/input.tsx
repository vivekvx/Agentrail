import * as React from "react";

import { cn } from "@/lib/utils";

export const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "h-11 w-full rounded-md border border-border bg-[#0d0d0d] px-3 text-sm text-white outline-none placeholder:text-zinc-600 focus:border-zinc-500",
      className,
    )}
    {...props}
  />
));
Input.displayName = "Input";

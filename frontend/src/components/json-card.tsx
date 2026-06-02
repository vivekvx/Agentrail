import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { JsonObject } from "@/lib/types";

export function JsonCard({
  title,
  description,
  value,
}: {
  title: string;
  description: string;
  value: JsonObject | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        {value ? (
          <pre className="scrollbar-thin max-h-80 overflow-auto rounded-md border border-border bg-[#0d0d0d] p-4 font-mono text-xs leading-6 text-zinc-300">
            <code>{JSON.stringify(value, null, 2)}</code>
          </pre>
        ) : (
          <div className="rounded-md border border-dashed border-border bg-[#0d0d0d] px-4 py-8 text-sm text-zinc-500">
            No data available yet.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

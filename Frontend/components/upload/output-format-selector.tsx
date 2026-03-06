"use client";

import { FileArchive } from "lucide-react";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import type { OutputFormat } from "@/lib/types";

const OUTPUT_FORMATS: { value: OutputFormat; label: string }[] = [
  { value: "cbz", label: "CBZ" },
  { value: "pdf", label: "PDF" },
  { value: "zip", label: "ZIP" },
];

interface OutputFormatSelectorProps {
  value: OutputFormat;
  onChange: (format: OutputFormat) => void;
}

export function OutputFormatSelector({ value, onChange }: OutputFormatSelectorProps) {
  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2 text-sm font-medium">
        <FileArchive className="h-4 w-4 text-primary" />
        Format de sortie
      </Label>

      <div className="flex gap-2">
        {OUTPUT_FORMATS.map((format) => (
          <button
            key={format.value}
            type="button"
            onClick={() => onChange(format.value)}
            className={cn(
              "flex-1 rounded-lg border px-4 py-2 text-sm font-medium transition-all",
              value === format.value
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-secondary/50 text-foreground hover:border-primary/50 hover:bg-secondary"
            )}
          >
            {format.label}
          </button>
        ))}
      </div>
    </div>
  );
}

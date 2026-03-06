"use client";

import { Progress } from "@/components/ui/progress";

interface GlobalProgressBarProps {
  progress: number;
  processedPages: number;
  totalPages: number;
}

export function GlobalProgressBar({
  progress,
  processedPages,
  totalPages,
}: GlobalProgressBarProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Progression</span>
        <span className="font-medium text-foreground">
          {processedPages} / {totalPages} pages traitées
        </span>
      </div>
      <Progress value={progress} className="h-3" />
      <div className="text-right text-sm font-medium text-primary">{progress}%</div>
    </div>
  );
}

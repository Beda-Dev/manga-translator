"use client";

import { cn } from "@/lib/utils";
import type { JobStatus } from "@/lib/types";

const STATUS_CONFIG: Record<
  JobStatus,
  { label: string; className: string }
> = {
  pending: {
    label: "En attente",
    className: "bg-muted text-muted-foreground",
  },
  extracting: {
    label: "Extraction",
    className: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
  processing: {
    label: "Traitement",
    className: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  },
  packaging: {
    label: "Packaging",
    className: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  },
  completed: {
    label: "Terminé",
    className: "bg-green-500/20 text-green-400 border-green-500/30",
  },
  failed: {
    label: "Erreur",
    className: "bg-destructive/20 text-destructive border-destructive/30",
  },
};

interface StatusBadgeProps {
  status: JobStatus;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  );
}

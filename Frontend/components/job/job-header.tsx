"use client";

import { ArrowRight, Calendar } from "lucide-react";
import { StatusBadge } from "./status-badge";
import type { JobStatus, SourceLanguage, TargetLanguage } from "@/lib/types";

const LANGUAGE_LABELS: Record<string, string> = {
  auto: "Auto",
  en: "EN",
  ja: "JA",
  ko: "KO",
  zh: "ZH",
  fr: "FR",
};

interface JobHeaderProps {
  filename: string;
  status: JobStatus;
  sourceLang: SourceLanguage;
  targetLang: TargetLanguage;
  createdAt: string;
}

export function JobHeader({
  filename,
  status,
  sourceLang,
  targetLang,
  createdAt,
}: JobHeaderProps) {
  const formattedDate = new Date(createdAt).toLocaleString("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="mb-2 font-[var(--font-display)] text-2xl tracking-wide text-foreground sm:text-3xl">
          {filename}
        </h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <span className="font-medium">{LANGUAGE_LABELS[sourceLang]}</span>
            <ArrowRight className="h-4 w-4" />
            <span className="font-medium">{LANGUAGE_LABELS[targetLang]}</span>
          </div>
          <span className="text-border">|</span>
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span>{formattedDate}</span>
          </div>
        </div>
      </div>
      <StatusBadge status={status} />
    </div>
  );
}

"use client";

import { PageCard } from "./page-card";
import type { PageInfo } from "@/lib/types";

interface PagesGridProps {
  pages: PageInfo[];
  jobId: string;
}

export function PagesGrid({ pages, jobId }: PagesGridProps) {
  if (pages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-secondary/20 py-16">
        <p className="text-muted-foreground">En attente des pages...</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {pages.map((page) => (
        <PageCard key={page.page_index} page={page} jobId={jobId} />
      ))}
    </div>
  );
}

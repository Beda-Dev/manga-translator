"use client";

import { useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { AlertCircle, RefreshCw, ArrowLeft, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { JobHeader } from "./job-header";
import { StepIndicator } from "./step-indicator";
import { GlobalProgressBar } from "./global-progress-bar";
import { PagesGrid } from "./pages-grid";
import { DownloadPanel } from "./download-panel";
import { getJobStatus } from "@/lib/api";
import { updateHistoryStatus, getJobHistory } from "@/lib/settings";
import type { SourceLanguage } from "@/lib/types";

interface JobContentProps {
  jobId: string;
}

export function JobContent({ jobId }: JobContentProps) {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => getJobStatus(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") {
        return false;
      }
      return 2000;
    },
    retry: 3,
    retryDelay: 1000,
  });

  // Update history when status changes
  useEffect(() => {
    if (data?.status) {
      updateHistoryStatus(jobId, data.status);
    }
  }, [data?.status, jobId]);

  // Get job info from history for display
  const historyItem = useMemo(() => {
    return getJobHistory().find((item) => item.job_id === jobId);
  }, [jobId]);

  // Calculate estimated time remaining
  const estimatedTimeRemaining = useMemo(() => {
    if (!data || data.processed_pages === 0) return null;
    
    const elapsedMs = data.pages
      .filter((p) => p.processing_time_ms > 0)
      .reduce((sum, p) => sum + p.processing_time_ms, 0);
    
    const avgTimePerPage = elapsedMs / data.processed_pages;
    const remainingPages = data.total_pages - data.processed_pages;
    const remainingMs = avgTimePerPage * remainingPages;
    
    if (remainingMs < 60000) {
      return `~${Math.ceil(remainingMs / 1000)}s restant`;
    }
    return `~${Math.ceil(remainingMs / 60000)}min restant`;
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card className="border-destructive/50 bg-destructive/5">
        <CardContent className="flex flex-col items-center gap-4 py-12">
          <AlertCircle className="h-12 w-12 text-destructive" />
          <div className="text-center">
            <h2 className="mb-2 text-xl font-semibold text-foreground">Erreur</h2>
            <p className="mb-4 text-muted-foreground">
              {error instanceof Error ? error.message : "Impossible de charger le travail"}
            </p>
          </div>
          <div className="flex gap-3">
            <Button onClick={() => refetch()} variant="outline">
              <RefreshCw className="mr-2 h-4 w-4" />
              Réessayer
            </Button>
            <Button asChild>
              <Link href="/">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Retour
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const isFailed = data.status === "failed";
  const isCompleted = data.status === "completed";

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" asChild className="mb-4">
        <Link href="/">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Retour
        </Link>
      </Button>

      <JobHeader
        filename={historyItem?.filename || `Job ${jobId.slice(0, 8)}`}
        status={data.status}
        sourceLang={(historyItem?.source_lang as SourceLanguage) || "auto"}
        targetLang="fr"
        createdAt={data.created_at}
      />

      {isFailed ? (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="py-8">
            <div className="flex flex-col items-center gap-4 text-center">
              <AlertCircle className="h-12 w-12 text-destructive" />
              <div>
                <h2 className="mb-2 text-xl font-semibold text-foreground">Échec de la traduction</h2>
                <p className="text-muted-foreground">{data.error_message || "Une erreur inconnue s'est produite"}</p>
              </div>
              <Button asChild>
                <Link href="/">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Réessayer
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card className="border-border bg-card">
            <CardContent className="py-6">
              <StepIndicator status={data.status} />
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardContent className="py-6">
              <GlobalProgressBar
                progress={data.progress}
                processedPages={data.processed_pages}
                totalPages={data.total_pages}
              />
              {estimatedTimeRemaining && !isCompleted && (
                <p className="mt-2 text-center text-sm text-muted-foreground">
                  {estimatedTimeRemaining}
                </p>
              )}
            </CardContent>
          </Card>

          {isCompleted && (
            <DownloadPanel
              jobId={jobId}
              outputUrl={data.output_url}
            />
          )}

          <div>
            <h2 className="mb-4 font-[var(--font-display)] text-xl text-foreground">
              Pages ({data.processed_pages}/{data.total_pages})
            </h2>
            <PagesGrid pages={data.pages} jobId={jobId} />
          </div>
        </>
      )}
    </div>
  );
}

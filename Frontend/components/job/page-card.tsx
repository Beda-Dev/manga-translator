"use client";

import { useState } from "react";
import { Download, Check, X, Loader2, ArrowRight, MessageSquare, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { getImageUrl, downloadPage } from "@/lib/api";
import type { PageInfo } from "@/lib/types";
import { toast } from "sonner";

interface PageCardProps {
  page: PageInfo;
  jobId: string;
}

const STATUS_ICONS = {
  success: Check,
  error: X,
  skipped: ArrowRight,
  processing: Loader2,
};

const STATUS_COLORS = {
  success: "text-green-400 bg-green-500/20",
  error: "text-destructive bg-destructive/20",
  skipped: "text-muted-foreground bg-muted",
  processing: "text-yellow-400 bg-yellow-500/20",
};

export function PageCard({ page, jobId }: PageCardProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const StatusIcon = STATUS_ICONS[page.status];
  const imageUrl = getImageUrl(page.image_url, jobId, page.page_index);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      await downloadPage(jobId, page.page_index);
      toast.success(`Page ${page.page_index + 1} téléchargée`);
    } catch {
      toast.error("Échec du téléchargement");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <TooltipProvider>
      <div className="group relative overflow-hidden rounded-lg border border-border bg-secondary/30 transition-all hover:border-primary/50">
        {/* Image Area */}
        <div className="relative aspect-[3/4] overflow-hidden bg-secondary">
          {imageUrl && !imageError ? (
            <>
              {!imageLoaded && (
                <Skeleton className="absolute inset-0" />
              )}
              <img
                src={imageUrl}
                alt={`Page ${page.page_index + 1}`}
                className={cn(
                  "h-full w-full object-cover transition-opacity",
                  imageLoaded ? "opacity-100" : "opacity-0"
                )}
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageError(true)}
                crossOrigin="anonymous"
              />
            </>
          ) : page.status === "processing" ? (
            <div className="flex h-full items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="flex h-full items-center justify-center">
              <AlertCircle className="h-8 w-8 text-muted-foreground" />
            </div>
          )}

          {/* Page Number Badge */}
          <div className="absolute left-2 top-2 rounded-md bg-background/90 px-2 py-1 text-xs font-medium text-foreground">
            #{page.page_index + 1}
          </div>

          {/* Status Badge */}
          <div
            className={cn(
              "absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full",
              STATUS_COLORS[page.status]
            )}
          >
            <StatusIcon
              className={cn(
                "h-3.5 w-3.5",
                page.status === "processing" && "animate-spin"
              )}
            />
          </div>
        </div>

        {/* Info Area */}
        <div className="p-3">
          <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  <span>{page.text_regions_count}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{page.text_regions_count} zones de texte</p>
              </TooltipContent>
            </Tooltip>

            {page.processing_time_ms > 0 && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{(page.processing_time_ms / 1000).toFixed(1)}s</span>
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Temps de traitement</p>
                </TooltipContent>
              </Tooltip>
            )}
          </div>

          {page.status === "success" && (
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={handleDownload}
              disabled={isDownloading}
            >
              {isDownloading ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <Download className="mr-1 h-3 w-3" />
              )}
              Télécharger
            </Button>
          )}

          {page.error && (
            <Tooltip>
              <TooltipTrigger asChild>
                <p className="truncate text-xs text-destructive">{page.error}</p>
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{page.error}</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}

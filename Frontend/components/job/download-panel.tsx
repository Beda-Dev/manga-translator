"use client";

import { useState } from "react";
import Link from "next/link";
import { Download, Loader2, Plus, FileArchive } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { downloadPackage } from "@/lib/api";
import { toast } from "sonner";
import type { OutputFormat } from "@/lib/types";

interface DownloadPanelProps {
  jobId: string;
  outputUrl: string | null;
  outputFormat?: OutputFormat;
}

const FORMAT_LABELS: Record<string, string> = {
  cbz: "CBZ",
  pdf: "PDF",
  zip: "ZIP",
};

export function DownloadPanel({ jobId, outputUrl, outputFormat = "cbz" }: DownloadPanelProps) {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);
    try {
      // If we have a direct Supabase URL, open it
      if (outputUrl && (outputUrl.startsWith("http://") || outputUrl.startsWith("https://"))) {
        window.open(outputUrl, "_blank");
      } else {
        await downloadPackage(jobId);
      }
      toast.success("Téléchargement démarré");
    } catch {
      toast.error("Échec du téléchargement");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Card className="border-primary/50 bg-primary/5">
      <CardContent className="flex flex-col items-center gap-4 p-6 sm:flex-row sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
            <FileArchive className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Traduction terminée!</h3>
            <p className="text-sm text-muted-foreground">
              Format: <span className="font-medium text-foreground">{FORMAT_LABELS[outputFormat]}</span>
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <Button onClick={handleDownload} disabled={isDownloading} size="lg">
            {isDownloading ? (
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            ) : (
              <Download className="mr-2 h-5 w-5" />
            )}
            Télécharger tout
          </Button>
          <Button variant="outline" size="lg" asChild>
            <Link href="/">
              <Plus className="mr-2 h-5 w-5" />
              Nouvelle traduction
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

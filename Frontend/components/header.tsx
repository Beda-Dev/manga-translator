"use client";

import Link from "next/link";
import { Settings, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getJobHistory } from "@/lib/settings";
import { useState, useEffect } from "react";
import type { JobHistoryItem } from "@/lib/types";

interface HeaderProps {
  onOpenSettings: () => void;
}

export function Header({ onOpenSettings }: HeaderProps) {
  const [history, setHistory] = useState<JobHistoryItem[]>([]);

  useEffect(() => {
    setHistory(getJobHistory());
  }, []);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <span className="font-[var(--font-display)] text-xl text-primary-foreground">M</span>
          </div>
          <span className="font-[var(--font-display)] text-2xl tracking-wide text-foreground">
            MangaTranslate
          </span>
        </Link>

        <div className="flex items-center gap-2">
          {history.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
                  <History className="h-5 w-5" />
                  <span className="sr-only">Historique</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-64">
                {history.slice(0, 5).map((item) => (
                  <DropdownMenuItem key={item.job_id} asChild>
                    <Link href={`/job/${item.job_id}`} className="flex flex-col items-start">
                      <span className="truncate font-medium">{item.filename}</span>
                      <span className="text-xs text-muted-foreground">
                        {item.total_pages} pages - {item.status}
                      </span>
                    </Link>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          <Button
            variant="ghost"
            size="icon"
            onClick={onOpenSettings}
            className="text-muted-foreground hover:text-foreground"
          >
            <Settings className="h-5 w-5" />
            <span className="sr-only">Paramètres</span>
          </Button>
        </div>
      </div>
    </header>
  );
}

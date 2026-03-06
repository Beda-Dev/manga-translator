"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/header";
import { SettingsModal } from "@/components/settings-modal";
import { JobContent } from "@/components/job/job-content";

export default function JobPage() {
  const params = useParams();
  const jobId = params.jobId as string;
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col">
      <Header onOpenSettings={() => setSettingsOpen(true)} />

      <main className="container mx-auto flex-1 px-4 py-8">
        <JobContent jobId={jobId} />
      </main>

      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}

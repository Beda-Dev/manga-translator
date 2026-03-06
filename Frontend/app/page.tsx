"use client";

import { useState } from "react";
import { Header } from "@/components/header";
import { SettingsModal } from "@/components/settings-modal";
import { UploadForm } from "@/components/upload/upload-form";

export default function HomePage() {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="flex min-h-screen flex-col">
      <Header onOpenSettings={() => setSettingsOpen(true)} />

      <main className="flex flex-1 flex-col items-center justify-center px-4 py-8 sm:py-12">
        <div className="mb-8 text-center">
          <h1 className="mb-3 font-[var(--font-display)] text-4xl tracking-wide text-foreground sm:text-5xl">
            Traduisez vos mangas
          </h1>
          <p className="text-lg text-muted-foreground">
            Traduction automatique par IA en quelques secondes
          </p>
        </div>

        <div className="w-full max-w-2xl">
          <UploadForm />
        </div>

        <p className="mt-8 text-center text-sm text-muted-foreground">
          Supporte CBZ, CBR, PDF, ZIP et images individuelles
        </p>
      </main>

      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
    </div>
  );
}

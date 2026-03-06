"use client";

import { Globe, Key, Link } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";
import type { TranslationEngine } from "@/lib/types";

const TRANSLATION_ENGINES: {
  value: TranslationEngine;
  label: string;
  description: string;
  requiresKey: boolean;
  requiresUrl: boolean;
}[] = [
  {
    value: "marian",
    label: "MarianMT",
    description: "Gratuit, hors ligne, HuggingFace",
    requiresKey: false,
    requiresUrl: false,
  },
  {
    value: "libretranslate",
    label: "LibreTranslate",
    description: "Open source",
    requiresKey: false,
    requiresUrl: true,
  },
  {
    value: "google_translate",
    label: "Google Translate",
    description: "Premium",
    requiresKey: true,
    requiresUrl: false,
  },
  {
    value: "deepl",
    label: "DeepL",
    description: "Meilleure qualité",
    requiresKey: true,
    requiresUrl: false,
  },
];

interface TranslationEngineSelectorProps {
  value: TranslationEngine;
  onChange: (engine: TranslationEngine) => void;
  googleTranslateKey: string;
  onGoogleTranslateKeyChange: (key: string) => void;
  deeplKey: string;
  onDeeplKeyChange: (key: string) => void;
  libretranslateUrl: string;
  onLibretranslateUrlChange: (url: string) => void;
}

export function TranslationEngineSelector({
  value,
  onChange,
  googleTranslateKey,
  onGoogleTranslateKeyChange,
  deeplKey,
  onDeeplKeyChange,
  libretranslateUrl,
  onLibretranslateUrlChange,
}: TranslationEngineSelectorProps) {
  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2 text-sm font-medium">
        <Globe className="h-4 w-4 text-primary" />
        Moteur de traduction
      </Label>

      <RadioGroup value={value} onValueChange={onChange} className="grid gap-3 sm:grid-cols-2">
        {TRANSLATION_ENGINES.map((engine) => (
          <label
            key={engine.value}
            className={cn(
              "flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-all",
              value === engine.value
                ? "border-primary bg-primary/5"
                : "border-border bg-secondary/30 hover:border-primary/50"
            )}
          >
            <RadioGroupItem value={engine.value} id={`trans-${engine.value}`} className="mt-0.5" />
            <div className="flex-1">
              <div className="font-medium text-foreground">{engine.label}</div>
              <div className="text-sm text-muted-foreground">{engine.description}</div>
              {engine.requiresKey && (
                <div className="mt-1 flex items-center gap-1 text-xs text-primary">
                  <Key className="h-3 w-3" />
                  Clé API requise
                </div>
              )}
              {engine.requiresUrl && (
                <div className="mt-1 flex items-center gap-1 text-xs text-primary">
                  <Link className="h-3 w-3" />
                  URL requise
                </div>
              )}
            </div>
          </label>
        ))}
      </RadioGroup>

      {value === "google_translate" && (
        <div className="mt-4 space-y-2">
          <Label htmlFor="google-translate-key" className="text-sm text-muted-foreground">
            Clé API Google Translate
          </Label>
          <Input
            id="google-translate-key"
            type="password"
            placeholder="Entrez votre clé API"
            value={googleTranslateKey}
            onChange={(e) => onGoogleTranslateKeyChange(e.target.value)}
            className="bg-secondary border-border"
          />
        </div>
      )}

      {value === "deepl" && (
        <div className="mt-4 space-y-2">
          <Label htmlFor="deepl-key" className="text-sm text-muted-foreground">
            Clé API DeepL
          </Label>
          <Input
            id="deepl-key"
            type="password"
            placeholder="Entrez votre clé API"
            value={deeplKey}
            onChange={(e) => onDeeplKeyChange(e.target.value)}
            className="bg-secondary border-border"
          />
        </div>
      )}

      {value === "libretranslate" && (
        <div className="mt-4 space-y-2">
          <Label htmlFor="libretranslate-url" className="text-sm text-muted-foreground">
            URL LibreTranslate
          </Label>
          <Input
            id="libretranslate-url"
            type="url"
            placeholder="https://libretranslate.example.com"
            value={libretranslateUrl}
            onChange={(e) => onLibretranslateUrlChange(e.target.value)}
            className="bg-secondary border-border"
          />
        </div>
      )}
    </div>
  );
}

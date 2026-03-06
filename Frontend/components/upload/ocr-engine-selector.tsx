"use client";

import { ScanText, Key } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";
import type { OCREngine } from "@/lib/types";

const OCR_ENGINES: {
  value: OCREngine;
  label: string;
  description: string;
  requiresKey: boolean;
}[] = [
  {
    value: "easyocr",
    label: "EasyOCR",
    description: "Open source, recommandé",
    requiresKey: false,
  },
  {
    value: "paddleocr",
    label: "PaddleOCR",
    description: "Haute performance BD",
    requiresKey: false,
  },
  {
    value: "tesseract",
    label: "Tesseract",
    description: "Rapide, open source",
    requiresKey: false,
  },
  {
    value: "google_vision",
    label: "Google Vision",
    description: "Précision maximale",
    requiresKey: true,
  },
];

interface OCREngineSelectorProps {
  value: OCREngine;
  onChange: (engine: OCREngine) => void;
  googleVisionKey: string;
  onGoogleVisionKeyChange: (key: string) => void;
}

export function OCREngineSelector({
  value,
  onChange,
  googleVisionKey,
  onGoogleVisionKeyChange,
}: OCREngineSelectorProps) {
  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2 text-sm font-medium">
        <ScanText className="h-4 w-4 text-primary" />
        Moteur OCR
      </Label>

      <RadioGroup value={value} onValueChange={onChange} className="grid gap-3 sm:grid-cols-2">
        {OCR_ENGINES.map((engine) => (
          <label
            key={engine.value}
            className={cn(
              "flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-all",
              value === engine.value
                ? "border-primary bg-primary/5"
                : "border-border bg-secondary/30 hover:border-primary/50"
            )}
          >
            <RadioGroupItem value={engine.value} id={engine.value} className="mt-0.5" />
            <div className="flex-1">
              <div className="font-medium text-foreground">{engine.label}</div>
              <div className="text-sm text-muted-foreground">{engine.description}</div>
              {engine.requiresKey && (
                <div className="mt-1 flex items-center gap-1 text-xs text-primary">
                  <Key className="h-3 w-3" />
                  Clé API requise
                </div>
              )}
            </div>
          </label>
        ))}
      </RadioGroup>

      {value === "google_vision" && (
        <div className="mt-4 space-y-2">
          <Label htmlFor="google-vision-key" className="text-sm text-muted-foreground">
            Clé API Google Vision
          </Label>
          <Input
            id="google-vision-key"
            type="password"
            placeholder="Entrez votre clé API"
            value={googleVisionKey}
            onChange={(e) => onGoogleVisionKeyChange(e.target.value)}
            className="bg-secondary border-border"
          />
        </div>
      )}
    </div>
  );
}

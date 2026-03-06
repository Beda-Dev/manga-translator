"use client";

import { Languages, ArrowRight } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import type { SourceLanguage } from "@/lib/types";

const SOURCE_LANGUAGES: { value: SourceLanguage; label: string }[] = [
  { value: "auto", label: "Auto-détection" },
  { value: "ja", label: "Japonais" },
  { value: "ko", label: "Coréen" },
  { value: "zh", label: "Chinois" },
  { value: "en", label: "Anglais" },
];

interface LanguageSelectorProps {
  sourceLanguage: SourceLanguage;
  onSourceLanguageChange: (lang: SourceLanguage) => void;
}

export function LanguageSelector({
  sourceLanguage,
  onSourceLanguageChange,
}: LanguageSelectorProps) {
  return (
    <div className="space-y-3">
      <Label className="flex items-center gap-2 text-sm font-medium">
        <Languages className="h-4 w-4 text-primary" />
        Langues
      </Label>
      
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <Select value={sourceLanguage} onValueChange={onSourceLanguageChange}>
            <SelectTrigger className="bg-secondary border-border">
              <SelectValue placeholder="Langue source" />
            </SelectTrigger>
            <SelectContent>
              {SOURCE_LANGUAGES.map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  {lang.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <ArrowRight className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
        
        <div className="flex-1">
          <div className="flex h-9 items-center rounded-md border border-border bg-secondary px-3 text-sm text-muted-foreground">
            Français
          </div>
        </div>
      </div>
    </div>
  );
}

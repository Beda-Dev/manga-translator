"use client";

import { useEffect, useState } from "react";
import { Save, RotateCcw } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FontOptionsPanel } from "@/components/upload/font-options-panel";
import { getSettings, saveSettings, DEFAULT_SETTINGS, DEFAULT_FONT_OPTIONS } from "@/lib/settings";
import type { AppSettings, OCREngine, TranslationEngine, OutputFormat } from "@/lib/types";
import { toast } from "sonner";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);

  useEffect(() => {
    if (open) {
      setSettings(getSettings());
    }
  }, [open]);

  const handleSave = () => {
    saveSettings(settings);
    toast.success("Paramètres enregistrés");
    onOpenChange(false);
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    saveSettings(DEFAULT_SETTINGS);
    toast.success("Paramètres réinitialisés");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-[var(--font-display)] text-xl">Paramètres</DialogTitle>
          <DialogDescription>
            Configurez vos préférences par défaut pour les traductions.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="defaults" className="mt-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="defaults">Défauts</TabsTrigger>
            <TabsTrigger value="api-keys">Clés API</TabsTrigger>
            <TabsTrigger value="fonts">Polices</TabsTrigger>
          </TabsList>

          <TabsContent value="defaults" className="mt-4 space-y-4">
            <div className="space-y-2">
              <Label>Moteur OCR par défaut</Label>
              <Select
                value={settings.default_ocr_engine}
                onValueChange={(value: OCREngine) =>
                  setSettings({ ...settings, default_ocr_engine: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easyocr">EasyOCR</SelectItem>
                  <SelectItem value="paddleocr">PaddleOCR</SelectItem>
                  <SelectItem value="tesseract">Tesseract</SelectItem>
                  <SelectItem value="google_vision">Google Vision</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Moteur de traduction par défaut</Label>
              <Select
                value={settings.default_translation_engine}
                onValueChange={(value: TranslationEngine) =>
                  setSettings({ ...settings, default_translation_engine: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="marian">MarianMT</SelectItem>
                  <SelectItem value="libretranslate">LibreTranslate</SelectItem>
                  <SelectItem value="google_translate">Google Translate</SelectItem>
                  <SelectItem value="deepl">DeepL</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Format de sortie par défaut</Label>
              <Select
                value={settings.default_output_format}
                onValueChange={(value: OutputFormat) =>
                  setSettings({ ...settings, default_output_format: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cbz">CBZ</SelectItem>
                  <SelectItem value="pdf">PDF</SelectItem>
                  <SelectItem value="zip">ZIP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>URL du backend (optionnel)</Label>
              <Input
                type="url"
                placeholder="https://your-backend.onrender.com"
                value={settings.backend_url || ""}
                onChange={(e) => setSettings({ ...settings, backend_url: e.target.value || undefined })}
              />
              <p className="text-xs text-muted-foreground">
                Laissez vide pour utiliser l&apos;URL par défaut.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="api-keys" className="mt-4 space-y-4">
            <div className="space-y-2">
              <Label>Clé API Google Vision</Label>
              <Input
                type="password"
                placeholder="Entrez votre clé API"
                value={settings.google_vision_key || ""}
                onChange={(e) =>
                  setSettings({ ...settings, google_vision_key: e.target.value || undefined })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>Clé API Google Translate</Label>
              <Input
                type="password"
                placeholder="Entrez votre clé API"
                value={settings.google_translate_key || ""}
                onChange={(e) =>
                  setSettings({ ...settings, google_translate_key: e.target.value || undefined })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>Clé API DeepL</Label>
              <Input
                type="password"
                placeholder="Entrez votre clé API"
                value={settings.deepl_key || ""}
                onChange={(e) =>
                  setSettings({ ...settings, deepl_key: e.target.value || undefined })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>URL LibreTranslate</Label>
              <Input
                type="url"
                placeholder="https://libretranslate.example.com"
                value={settings.libretranslate_url || ""}
                onChange={(e) =>
                  setSettings({ ...settings, libretranslate_url: e.target.value || undefined })
                }
              />
            </div>
          </TabsContent>

          <TabsContent value="fonts" className="mt-4">
            <FontOptionsPanel
              value={settings.default_font_options || DEFAULT_FONT_OPTIONS}
              onChange={(fontOptions) =>
                setSettings({ ...settings, default_font_options: fontOptions })
              }
            />
          </TabsContent>
        </Tabs>

        <div className="mt-6 flex justify-between">
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Réinitialiser
          </Button>
          <Button onClick={handleSave}>
            <Save className="mr-2 h-4 w-4" />
            Enregistrer
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

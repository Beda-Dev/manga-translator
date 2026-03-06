"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Zap, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { FileDropzone } from "./file-dropzone";
import { LanguageSelector } from "./language-selector";
import { OCREngineSelector } from "./ocr-engine-selector";
import { TranslationEngineSelector } from "./translation-engine-selector";
import { FontOptionsPanel } from "./font-options-panel";
import { OutputFormatSelector } from "./output-format-selector";
import { startTranslation, checkHealth, APIClientError } from "@/lib/api";
import { getSettings, addToHistory, DEFAULT_FONT_OPTIONS } from "@/lib/settings";
import type {
  SourceLanguage,
  OCREngine,
  TranslationEngine,
  OutputFormat,
  FontOptions,
} from "@/lib/types";

export function UploadForm() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Form state
  const [sourceLanguage, setSourceLanguage] = useState<SourceLanguage>("auto");
  const [ocrEngine, setOcrEngine] = useState<OCREngine>("easyocr");
  const [translationEngine, setTranslationEngine] = useState<TranslationEngine>("marian");
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("cbz");
  const [fontOptions, setFontOptions] = useState<FontOptions>(DEFAULT_FONT_OPTIONS);

  // API Keys
  const [googleVisionKey, setGoogleVisionKey] = useState("");
  const [googleTranslateKey, setGoogleTranslateKey] = useState("");
  const [deeplKey, setDeeplKey] = useState("");
  const [libretranslateUrl, setLibretranslateUrl] = useState("");

  // Load saved settings
  useEffect(() => {
    const settings = getSettings();
    setOcrEngine(settings.default_ocr_engine);
    setTranslationEngine(settings.default_translation_engine);
    setOutputFormat(settings.default_output_format);
    setFontOptions(settings.default_font_options || DEFAULT_FONT_OPTIONS);
    if (settings.google_vision_key) setGoogleVisionKey(settings.google_vision_key);
    if (settings.google_translate_key) setGoogleTranslateKey(settings.google_translate_key);
    if (settings.deepl_key) setDeeplKey(settings.deepl_key);
    if (settings.libretranslate_url) setLibretranslateUrl(settings.libretranslate_url);
  }, []);

  // Check backend health
  useEffect(() => {
    checkHealth()
      .then(() => setBackendOnline(true))
      .catch(() => setBackendOnline(false));
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!file) return;

    // Validate required keys
    if (ocrEngine === "google_vision" && !googleVisionKey) {
      toast.error("Clé API Google Vision requise");
      return;
    }
    if (translationEngine === "google_translate" && !googleTranslateKey) {
      toast.error("Clé API Google Translate requise");
      return;
    }
    if (translationEngine === "deepl" && !deeplKey) {
      toast.error("Clé API DeepL requise");
      return;
    }
    if (translationEngine === "libretranslate" && !libretranslateUrl) {
      toast.error("URL LibreTranslate requise");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await startTranslation(file, {
        ocr_engine: ocrEngine,
        translation_engine: translationEngine,
        source_lang: sourceLanguage,
        target_lang: "fr",
        output_format: outputFormat,
        font_options: fontOptions,
        google_vision_key: googleVisionKey || undefined,
        google_translate_key: googleTranslateKey || undefined,
        deepl_key: deeplKey || undefined,
        libretranslate_url: libretranslateUrl || undefined,
      });

      // Add to history
      addToHistory({
        job_id: response.job_id,
        filename: file.name,
        source_lang: sourceLanguage,
        target_lang: "fr",
        status: "pending",
        created_at: new Date().toISOString(),
        total_pages: response.total_pages,
      });

      toast.success("Traduction démarrée!");
      router.push(`/job/${response.job_id}`);
    } catch (error) {
      if (error instanceof APIClientError) {
        toast.error(error.detail);
      } else {
        toast.error("Une erreur est survenue");
      }
      setIsSubmitting(false);
    }
  }, [
    file,
    ocrEngine,
    translationEngine,
    sourceLanguage,
    outputFormat,
    fontOptions,
    googleVisionKey,
    googleTranslateKey,
    deeplKey,
    libretranslateUrl,
    router,
  ]);

  return (
    <Card className="border-border bg-card">
      <CardContent className="p-6 sm:p-8">
        <div className="space-y-8">
          {/* Backend Status */}
          {backendOnline === false && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>
                Le serveur backend est hors ligne. Vérifiez votre connexion ou l&apos;URL du backend
                dans les paramètres.
              </span>
            </div>
          )}

          {/* File Upload */}
          <FileDropzone file={file} onFileSelect={setFile} />

          {/* Language Selection */}
          <LanguageSelector
            sourceLanguage={sourceLanguage}
            onSourceLanguageChange={setSourceLanguage}
          />

          {/* OCR Engine */}
          <OCREngineSelector
            value={ocrEngine}
            onChange={setOcrEngine}
            googleVisionKey={googleVisionKey}
            onGoogleVisionKeyChange={setGoogleVisionKey}
          />

          {/* Translation Engine */}
          <TranslationEngineSelector
            value={translationEngine}
            onChange={setTranslationEngine}
            googleTranslateKey={googleTranslateKey}
            onGoogleTranslateKeyChange={setGoogleTranslateKey}
            deeplKey={deeplKey}
            onDeeplKeyChange={setDeeplKey}
            libretranslateUrl={libretranslateUrl}
            onLibretranslateUrlChange={setLibretranslateUrl}
          />

          {/* Output Format */}
          <OutputFormatSelector value={outputFormat} onChange={setOutputFormat} />

          {/* Font Options */}
          <div className="border-t border-border pt-6">
            <FontOptionsPanel value={fontOptions} onChange={setFontOptions} />
          </div>

          {/* Submit Button */}
          <Button
            size="lg"
            className="w-full bg-primary text-lg font-semibold text-primary-foreground hover:bg-primary/90"
            disabled={!file || isSubmitting || backendOnline === false}
            onClick={handleSubmit}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Envoi en cours...
              </>
            ) : (
              <>
                <Zap className="mr-2 h-5 w-5" />
                Traduire maintenant
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// OCR Engine types
export type OCREngine = "easyocr" | "paddleocr" | "tesseract" | "google_vision";

// Translation Engine types
export type TranslationEngine = "marian" | "libretranslate" | "google_translate" | "deepl";

// Source Language types
export type SourceLanguage = "auto" | "en" | "ja" | "ko" | "zh";

// Target Language types
export type TargetLanguage = "fr";

// Output Format types
export type OutputFormat = "cbz" | "pdf" | "zip";

// Job Status types
export type JobStatus = "pending" | "extracting" | "processing" | "packaging" | "completed" | "failed";

// Page Status types
export type PageStatus = "success" | "error" | "skipped" | "processing";

// Storage Mode types
export type StorageMode = "supabase" | "local";

// Font Options
export interface FontOptions {
  size_max: number;
  size_min: number;
  color: string;
  outline_color: string;
  outline_width: number;
  bold: boolean;
}

// Translation Options for API call
export interface TranslationOptions {
  ocr_engine: OCREngine;
  translation_engine: TranslationEngine;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  output_format: OutputFormat;
  font_options: FontOptions;
  google_vision_key?: string;
  google_translate_key?: string;
  deepl_key?: string;
  libretranslate_url?: string;
}

// POST /translate Response
export interface TranslateResponse {
  job_id: string;
  message: string;
  total_pages: number;
  status_url: string;
  download_url: string;
}

// Page Info from status
export interface PageInfo {
  page_index: number;
  filename: string;
  status: PageStatus;
  image_url: string | null;
  download_url: string;
  text_regions_count: number;
  processing_time_ms: number;
  error: string | null;
}

// GET /status/{job_id} Response
export interface StatusResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  total_pages: number;
  processed_pages: number;
  pages: PageInfo[];
  output_url: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

// GET /download/{job_id}/pages Response
export interface PagesResponse {
  job_id: string;
  status: string;
  progress: number;
  total_pages: number;
  processed_pages: number;
  storage_mode: StorageMode;
  package_url: string;
  pages: PageInfo[];
}

// GET /health Response
export interface HealthResponse {
  status: "ok";
  version: string;
  ocr_engine: string;
  translation_engine: string;
}

// Settings stored in localStorage
export interface AppSettings {
  default_ocr_engine: OCREngine;
  default_translation_engine: TranslationEngine;
  default_output_format: OutputFormat;
  default_font_options: FontOptions;
  google_vision_key?: string;
  google_translate_key?: string;
  deepl_key?: string;
  libretranslate_url?: string;
  backend_url?: string;
}

// Job History Item
export interface JobHistoryItem {
  job_id: string;
  filename: string;
  source_lang: SourceLanguage;
  target_lang: TargetLanguage;
  status: JobStatus;
  created_at: string;
  total_pages: number;
}

// API Error
export interface APIError {
  detail: string;
  status: number;
}

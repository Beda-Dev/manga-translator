import type { AppSettings, FontOptions, JobHistoryItem } from "./types";

const SETTINGS_KEY = "manga-translator-settings";
const HISTORY_KEY = "manga-translator-history";
const MAX_HISTORY_ITEMS = 10;

export const DEFAULT_FONT_OPTIONS: FontOptions = {
  size_max: 24,
  size_min: 8,
  color: "#000000",
  outline_color: "#FFFFFF",
  outline_width: 1,
  bold: false,
};

export const DEFAULT_SETTINGS: AppSettings = {
  default_ocr_engine: "easyocr",
  default_translation_engine: "marian",
  default_output_format: "cbz",
  default_font_options: DEFAULT_FONT_OPTIONS,
};

export function getSettings(): AppSettings {
  if (typeof window === "undefined") {
    return DEFAULT_SETTINGS;
  }

  try {
    const stored = localStorage.getItem(SETTINGS_KEY);
    if (stored) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
    }
  } catch {
    // Ignore parse errors
  }

  return DEFAULT_SETTINGS;
}

export function saveSettings(settings: Partial<AppSettings>): void {
  if (typeof window === "undefined") return;

  const current = getSettings();
  const updated = { ...current, ...settings };
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(updated));
}

export function getJobHistory(): JobHistoryItem[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch {
    // Ignore parse errors
  }

  return [];
}

export function addToHistory(item: JobHistoryItem): void {
  if (typeof window === "undefined") return;

  const history = getJobHistory();
  
  // Remove if already exists (update)
  const filtered = history.filter((h) => h.job_id !== item.job_id);
  
  // Add to beginning
  filtered.unshift(item);
  
  // Keep only last MAX_HISTORY_ITEMS
  const trimmed = filtered.slice(0, MAX_HISTORY_ITEMS);
  
  localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));
}

export function updateHistoryStatus(jobId: string, status: JobHistoryItem["status"]): void {
  if (typeof window === "undefined") return;

  const history = getJobHistory();
  const updated = history.map((item) =>
    item.job_id === jobId ? { ...item, status } : item
  );
  localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
}

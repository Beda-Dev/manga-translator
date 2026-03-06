import type {
  TranslationOptions,
  TranslateResponse,
  StatusResponse,
  PagesResponse,
  HealthResponse,
} from "./types";

const getBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("manga-translator-settings");
    if (stored) {
      try {
        const settings = JSON.parse(stored);
        if (settings.backend_url) {
          return settings.backend_url;
        }
      } catch {
        // Ignore parse errors
      }
    }
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

class APIClientError extends Error {
  status: number;
  detail: string;

  constructor(message: string, status: number, detail: string) {
    super(message);
    this.name = "APIClientError";
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = "An error occurred";

    try {
      const errorData = await response.json();
      detail = errorData.detail || errorData.message || detail;
    } catch {
      // If we can't parse JSON, use status text
      detail = response.statusText;
    }

    if (response.status === 413) {
      throw new APIClientError("File too large", 413, "The file exceeds the maximum allowed size of 100MB");
    }
    if (response.status === 422) {
      throw new APIClientError("Processing error", 422, detail);
    }
    if (response.status === 404) {
      throw new APIClientError("Not found", 404, "The requested job was not found");
    }

    throw new APIClientError("Request failed", response.status, detail);
  }

  return response.json();
}

export async function startTranslation(
  file: File,
  options: TranslationOptions
): Promise<TranslateResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("ocr_engine", options.ocr_engine);
  formData.append("translation_engine", options.translation_engine);
  formData.append("source_lang", options.source_lang);
  formData.append("target_lang", options.target_lang);
  formData.append("output_format", options.output_format);
  formData.append("font_options", JSON.stringify(options.font_options));

  if (options.google_vision_key) {
    formData.append("google_vision_key", options.google_vision_key);
  }
  if (options.google_translate_key) {
    formData.append("google_translate_key", options.google_translate_key);
  }
  if (options.deepl_key) {
    formData.append("deepl_key", options.deepl_key);
  }
  if (options.libretranslate_url) {
    formData.append("libretranslate_url", options.libretranslate_url);
  }

  const response = await fetch(`${getBaseUrl()}/translate`, {
    method: "POST",
    body: formData,
  });

  return handleResponse<TranslateResponse>(response);
}

export async function getJobStatus(jobId: string): Promise<StatusResponse> {
  const response = await fetch(`${getBaseUrl()}/status/${jobId}`);
  return handleResponse<StatusResponse>(response);
}

export async function getJobPages(jobId: string): Promise<PagesResponse> {
  const response = await fetch(`${getBaseUrl()}/download/${jobId}/pages`);
  return handleResponse<PagesResponse>(response);
}

export async function downloadPackage(jobId: string): Promise<void> {
  const response = await fetch(`${getBaseUrl()}/download/${jobId}`, {
    redirect: "follow",
  });

  if (!response.ok) {
    throw new APIClientError("Download failed", response.status, "Failed to download the package");
  }

  // Get the blob from the response
  const blob = await response.blob();
  
  // Get filename from Content-Disposition header or use default
  const contentDisposition = response.headers.get("Content-Disposition");
  let filename = `translation-${jobId}.cbz`;
  
  if (contentDisposition) {
    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
    if (match && match[1]) {
      filename = match[1].replace(/['"]/g, "");
    }
  }

  // Create download link and trigger download
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export async function downloadPage(jobId: string, pageIndex: number): Promise<void> {
  const response = await fetch(`${getBaseUrl()}/download/${jobId}/page/${pageIndex}`, {
    redirect: "follow",
  });

  if (!response.ok) {
    throw new APIClientError("Download failed", response.status, "Failed to download the page");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `page-${pageIndex}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getBaseUrl()}/health`);
  return handleResponse<HealthResponse>(response);
}

export function getImageUrl(imageUrl: string | null, jobId: string, pageIndex: number): string {
  if (!imageUrl) {
    return "";
  }
  
  // If it's an absolute URL (Supabase), return as-is
  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }
  
  // Otherwise, it's a relative path - prepend the base URL
  return `${getBaseUrl()}/download/${jobId}/page/${pageIndex}`;
}

export { APIClientError };

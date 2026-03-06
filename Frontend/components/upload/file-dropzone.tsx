"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const ACCEPTED_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
  "application/zip",
  "application/x-cbz",
  "application/x-cbr",
  "application/vnd.comicbook+zip",
  "application/vnd.comicbook-rar",
];

const ACCEPTED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".cbz", ".cbr", ".pdf", ".zip"];
const MAX_SIZE_MB = 100;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

interface FileDropzoneProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileExtension(filename: string): string {
  return filename.slice(filename.lastIndexOf(".")).toLowerCase();
}

function estimatePages(file: File): string {
  const ext = getFileExtension(file.name);
  if ([".jpg", ".jpeg", ".png", ".webp"].includes(ext)) {
    return "1 page";
  }
  // Rough estimate based on file size
  const sizeInMB = file.size / (1024 * 1024);
  if (sizeInMB < 1) return "~1-5 pages";
  if (sizeInMB < 10) return "~5-20 pages";
  if (sizeInMB < 50) return "~20-100 pages";
  return "~100+ pages";
}

export function FileDropzone({ file, onFileSelect }: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): boolean => {
    setError(null);

    const ext = getFileExtension(file.name);
    const isValidExt = ACCEPTED_EXTENSIONS.includes(ext);
    const isValidType = ACCEPTED_TYPES.includes(file.type) || isValidExt;

    if (!isValidType) {
      setError(`Type de fichier non supporté. Formats acceptés: ${ACCEPTED_EXTENSIONS.join(", ")}`);
      return false;
    }

    if (file.size > MAX_SIZE_BYTES) {
      setError(`Fichier trop volumineux. Maximum: ${MAX_SIZE_MB}MB`);
      return false;
    }

    return true;
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile && validateFile(droppedFile)) {
        onFileSelect(droppedFile);
      }
    },
    [onFileSelect, validateFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile && validateFile(selectedFile)) {
        onFileSelect(selectedFile);
      }
      // Reset input so the same file can be selected again
      e.target.value = "";
    },
    [onFileSelect, validateFile]
  );

  const handleRemove = useCallback(() => {
    setError(null);
    onFileSelect(null);
  }, [onFileSelect]);

  if (file) {
    return (
      <div className="relative rounded-lg border-2 border-primary/50 bg-primary/5 p-6">
        <button
          type="button"
          onClick={handleRemove}
          className="absolute right-3 top-3 rounded-full p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          aria-label="Supprimer le fichier"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-lg bg-primary/10">
            <FileText className="h-7 w-7 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="truncate font-medium text-foreground">{file.name}</p>
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <span>{formatFileSize(file.size)}</span>
              <span className="text-primary">{estimatePages(file)}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-all",
          isDragging
            ? "border-primary bg-primary/10"
            : "border-border bg-secondary/30 hover:border-primary/50 hover:bg-secondary/50",
          error && "border-destructive"
        )}
      >
        <input
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          onChange={handleFileInput}
          className="sr-only"
        />
        <div
          className={cn(
            "mb-4 flex h-16 w-16 items-center justify-center rounded-full transition-colors",
            isDragging ? "bg-primary text-primary-foreground" : "bg-secondary"
          )}
        >
          <Upload className="h-8 w-8" />
        </div>
        <p className="mb-2 text-lg font-medium text-foreground">
          {isDragging ? "Déposez votre fichier ici" : "Glissez-déposez votre manga"}
        </p>
        <p className="text-sm text-muted-foreground">
          ou <span className="text-primary underline">parcourir</span>
        </p>
        <p className="mt-3 text-xs text-muted-foreground">
          JPG, PNG, WebP, CBZ, CBR, PDF, ZIP (max {MAX_SIZE_MB}MB)
        </p>
      </label>

      {error && (
        <div className="mt-3 flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="h-4 w-4" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

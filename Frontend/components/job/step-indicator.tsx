"use client";

import { Check, FileSearch, Languages, Package, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { JobStatus } from "@/lib/types";

const STEPS = [
  { key: "extracting", label: "Extraction", icon: FileSearch },
  { key: "processing", label: "OCR & Traduction", icon: Languages },
  { key: "packaging", label: "Packaging", icon: Package },
  { key: "completed", label: "Terminé", icon: CheckCircle2 },
] as const;

const STATUS_ORDER: Record<JobStatus, number> = {
  pending: -1,
  extracting: 0,
  processing: 1,
  packaging: 2,
  completed: 3,
  failed: -1,
};

interface StepIndicatorProps {
  status: JobStatus;
}

export function StepIndicator({ status }: StepIndicatorProps) {
  const currentStep = STATUS_ORDER[status];

  return (
    <div className="flex items-center justify-between">
      {STEPS.map((step, index) => {
        const Icon = step.icon;
        const isCompleted = currentStep > index;
        const isCurrent = currentStep === index;

        return (
          <div key={step.key} className="flex flex-1 items-center">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all",
                  isCompleted
                    ? "border-primary bg-primary text-primary-foreground"
                    : isCurrent
                    ? "border-primary bg-primary/20 text-primary"
                    : "border-border bg-secondary text-muted-foreground"
                )}
              >
                {isCompleted ? (
                  <Check className="h-5 w-5" />
                ) : (
                  <Icon className="h-5 w-5" />
                )}
              </div>
              <span
                className={cn(
                  "mt-2 text-xs font-medium",
                  isCurrent ? "text-primary" : isCompleted ? "text-foreground" : "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </div>
            {index < STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-2 h-0.5 flex-1",
                  currentStep > index ? "bg-primary" : "bg-border"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

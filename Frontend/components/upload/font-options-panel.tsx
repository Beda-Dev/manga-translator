"use client";

import { useState } from "react";
import { Type, ChevronDown, ChevronUp } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { FontOptions } from "@/lib/types";

interface FontOptionsPanelProps {
  value: FontOptions;
  onChange: (options: FontOptions) => void;
}

export function FontOptionsPanel({ value, onChange }: FontOptionsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const updateOption = <K extends keyof FontOptions>(key: K, val: FontOptions[K]) => {
    onChange({ ...value, [key]: val });
  };

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          className="flex w-full items-center justify-between px-0 hover:bg-transparent"
        >
          <span className="flex items-center gap-2 text-sm font-medium">
            <Type className="h-4 w-4 text-primary" />
            Options de police
          </span>
          {isOpen ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </Button>
      </CollapsibleTrigger>

      <CollapsibleContent className="mt-4 space-y-6">
        {/* Font Size Max */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm text-muted-foreground">Taille max</Label>
            <span className="text-sm font-medium text-foreground">{value.size_max}px</span>
          </div>
          <Slider
            value={[value.size_max]}
            onValueChange={([val]) => updateOption("size_max", val)}
            min={8}
            max={48}
            step={1}
            className="cursor-pointer"
          />
        </div>

        {/* Font Size Min */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm text-muted-foreground">Taille min</Label>
            <span className="text-sm font-medium text-foreground">{value.size_min}px</span>
          </div>
          <Slider
            value={[value.size_min]}
            onValueChange={([val]) => updateOption("size_min", val)}
            min={4}
            max={24}
            step={1}
            className="cursor-pointer"
          />
        </div>

        {/* Outline Width */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm text-muted-foreground">Épaisseur contour</Label>
            <span className="text-sm font-medium text-foreground">{value.outline_width}px</span>
          </div>
          <Slider
            value={[value.outline_width]}
            onValueChange={([val]) => updateOption("outline_width", val)}
            min={0}
            max={5}
            step={0.5}
            className="cursor-pointer"
          />
        </div>

        {/* Colors */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label className="text-sm text-muted-foreground">Couleur du texte</Label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={value.color}
                onChange={(e) => updateOption("color", e.target.value)}
                className="h-9 w-12 cursor-pointer rounded border border-border bg-transparent"
              />
              <span className="text-xs text-muted-foreground">{value.color}</span>
            </div>
          </div>
          <div className="space-y-2">
            <Label className="text-sm text-muted-foreground">Couleur du contour</Label>
            <div className="flex items-center gap-2">
              <input
                type="color"
                value={value.outline_color}
                onChange={(e) => updateOption("outline_color", e.target.value)}
                className="h-9 w-12 cursor-pointer rounded border border-border bg-transparent"
              />
              <span className="text-xs text-muted-foreground">{value.outline_color}</span>
            </div>
          </div>
        </div>

        {/* Bold Toggle */}
        <div className="flex items-center justify-between">
          <Label className="text-sm text-muted-foreground">Texte en gras</Label>
          <Switch
            checked={value.bold}
            onCheckedChange={(checked) => updateOption("bold", checked)}
          />
        </div>

        {/* Preview */}
        <div className="rounded-lg border border-border bg-secondary/50 p-4">
          <Label className="mb-2 block text-xs text-muted-foreground">Aperçu</Label>
          <p
            className="text-center"
            style={{
              fontSize: `${value.size_max}px`,
              fontWeight: value.bold ? "bold" : "normal",
              color: value.color,
              textShadow: `
                -${value.outline_width}px -${value.outline_width}px 0 ${value.outline_color},
                ${value.outline_width}px -${value.outline_width}px 0 ${value.outline_color},
                -${value.outline_width}px ${value.outline_width}px 0 ${value.outline_color},
                ${value.outline_width}px ${value.outline_width}px 0 ${value.outline_color}
              `,
            }}
          >
            Bonjour!
          </p>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

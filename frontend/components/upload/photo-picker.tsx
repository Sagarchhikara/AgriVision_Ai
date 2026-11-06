"use client";

import { Camera, ImageUp, Leaf, RefreshCw } from "lucide-react";
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";

import { useI18n } from "@/components/i18n-provider";
import { Button } from "@/components/ui/button";
import { MAX_INPUT_BYTES } from "@/lib/image";
import { cn } from "cn";

/**
 * Camera capture and file picking, plus drag-and-drop on devices with a mouse.
 *
 * "Take a photo" only appears on touch devices, where capture="environment"
 * opens the rear camera; elsewhere it would open the same dialog as "Choose a
 * photo". Once a photo is chosen, a single "use a different photo" button
 * opens the plain picker, which on phones offers both camera and gallery.
 */
export function PhotoPicker({
  onFile,
  disabled,
  compact,
}: {
  onFile: (file: File) => void;
  disabled: boolean;
  compact: boolean;
}) {
  const { t } = useI18n();
  const cameraInput = useRef<HTMLInputElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const onChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    // Clear, so choosing the same file again still fires a change.
    event.target.value = "";
    if (file) onFile(file);
  };

  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file && !disabled) onFile(file);
  };

  const inputs = (
    <>
      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        hidden
        disabled={disabled}
        onChange={onChange}
      />
      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        hidden
        disabled={disabled}
        onChange={onChange}
      />
    </>
  );

  if (compact) {
    return (
      <>
        {inputs}
        <Button variant="outline" disabled={disabled} onClick={() => fileInput.current?.click()}>
          <RefreshCw aria-hidden />
          {t.upload.changePhoto}
        </Button>
      </>
    );
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={cn(
        "flex min-h-80 flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed border-input bg-card p-6 text-center transition-colors lg:min-h-112",
        dragging && "border-primary bg-secondary/50",
      )}
    >
      {inputs}
      <span
        aria-hidden
        className="grid size-16 place-items-center rounded-2xl bg-secondary text-primary"
      >
        <Leaf className="size-8" />
      </span>
      <div className="flex w-full max-w-sm flex-col gap-3">
        <Button
          size="lg"
          className="hidden pointer-coarse:inline-flex"
          disabled={disabled}
          onClick={() => cameraInput.current?.click()}
        >
          <Camera aria-hidden />
          {t.upload.takePhoto}
        </Button>
        <Button
          size="lg"
          // Secondary to the camera on touch devices, primary everywhere else.
          className="pointer-coarse:border-input pointer-coarse:bg-card pointer-coarse:text-foreground pointer-coarse:hover:bg-muted"
          disabled={disabled}
          onClick={() => fileInput.current?.click()}
        >
          <ImageUp aria-hidden />
          {t.upload.choosePhoto}
        </Button>
      </div>
      <div className="flex flex-col gap-1 text-sm text-muted-foreground">
        <p aria-hidden className="pointer-coarse:hidden">
          {dragging ? t.upload.dropActive : t.upload.dropHint}
        </p>
        <p>{t.upload.formats.replace("{size}", String(MAX_INPUT_BYTES / (1024 * 1024)))}</p>
      </div>
    </div>
  );
}

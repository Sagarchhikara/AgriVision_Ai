/**
 * Client-side photo preparation, done before anything is uploaded.
 *
 * - Shrinks phone photos (often 5-10 MB) to at most 1024px on the longest side
 *   as JPEG, so uploads are small on slow connections. The model only sees
 *   224px, so nothing useful is lost.
 * - Re-encoding through a canvas also applies EXIF orientation (the backend
 *   does not, so an unrotated phone photo would reach the model sideways) and
 *   turns formats the backend can't decode, such as HEIC on iPhones, into JPEG.
 * - Produces a second image cropped to exactly the region the model analyses,
 *   so the Grad-CAM overlay can be shown pixel-aligned against it.
 */

export type PhotoErrorCode = "not_an_image" | "file_too_large" | "unreadable_image";

export class PhotoError extends Error {
  readonly code: PhotoErrorCode;

  constructor(code: PhotoErrorCode, message: string) {
    super(message);
    this.name = "PhotoError";
    this.code = code;
  }
}

export interface PreparedPhoto {
  /** Resized JPEG, ready to upload. */
  blob: Blob;
  /** Object URL of `blob`, for previews. */
  url: string;
  /** Object URL of the square region the model actually analyses. */
  modelViewUrl: string;
  width: number;
  height: number;
}

/** Refuse to even decode files above this: a low-end phone can run out of memory. */
export const MAX_INPUT_BYTES = 30 * 1024 * 1024;
const MAX_SIDE_PX = 1024;
const JPEG_QUALITY = 0.85;
const MODEL_VIEW_MAX_PX = 512;

/**
 * Mirrors the backend's eval transform (data/transforms.py get_val_transforms):
 * resize the short side to int(224 * 1.14) = 255, then centre-crop 224. The
 * model therefore sees a centred square 224/255 of the short side wide. If the
 * training image size or resize ratio changes, update this.
 */
export const MODEL_CROP_FRACTION = 224 / 255;

export interface Size {
  width: number;
  height: number;
}

export interface SquareRect {
  x: number;
  y: number;
  size: number;
}

/** Scales `size` down (never up) so its longest side is at most `maxSide`. */
export function fitWithin({ width, height }: Size, maxSide: number): Size {
  const scale = Math.min(1, maxSide / Math.max(width, height));
  return {
    width: Math.max(1, Math.round(width * scale)),
    height: Math.max(1, Math.round(height * scale)),
  };
}

/** The centred square, `fraction` of the short side wide. */
export function centerSquare({ width, height }: Size, fraction: number): SquareRect {
  const size = Math.min(width, height) * fraction;
  return { x: (width - size) / 2, y: (height - size) / 2, size };
}

interface Decoded {
  source: CanvasImageSource;
  width: number;
  height: number;
  release: () => void;
}

async function decode(file: Blob): Promise<Decoded> {
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    return {
      source: bitmap,
      width: bitmap.width,
      height: bitmap.height,
      release: () => bitmap.close(),
    };
  } catch {
    // Fall back to <img>, which some browsers can decode when createImageBitmap
    // can't (and which applies EXIF orientation by default).
  }

  const url = URL.createObjectURL(file);
  const image = new Image();
  try {
    image.src = url;
    await image.decode();
  } catch {
    URL.revokeObjectURL(url);
    throw new PhotoError("unreadable_image", "The browser could not decode this file.");
  }
  return {
    source: image,
    width: image.naturalWidth,
    height: image.naturalHeight,
    release: () => URL.revokeObjectURL(url),
  };
}

function toJpeg(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) =>
        blob
          ? resolve(blob)
          : reject(new PhotoError("unreadable_image", "Could not encode the photo.")),
      "image/jpeg",
      JPEG_QUALITY,
    );
  });
}

function drawToCanvas(
  source: CanvasImageSource,
  sourceRect: { x: number; y: number; width: number; height: number },
  output: Size,
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = output.width;
  canvas.height = output.height;
  const context = canvas.getContext("2d");
  if (!context) throw new PhotoError("unreadable_image", "Canvas 2D context unavailable.");
  // JPEG has no alpha: transparent PNG areas would otherwise turn black.
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, output.width, output.height);
  context.imageSmoothingQuality = "high";
  context.drawImage(
    source,
    sourceRect.x,
    sourceRect.y,
    sourceRect.width,
    sourceRect.height,
    0,
    0,
    output.width,
    output.height,
  );
  return canvas;
}

/**
 * Validates, orients, resizes, and re-encodes a user-chosen file.
 *
 * Throws PhotoError for anything the user can fix by choosing another photo.
 */
export async function preparePhoto(file: File): Promise<PreparedPhoto> {
  // Some Android pickers report an empty type; let decoding decide for those.
  if (file.type && !file.type.startsWith("image/")) {
    throw new PhotoError("not_an_image", `File type ${file.type} is not an image.`);
  }
  if (file.size > MAX_INPUT_BYTES) {
    throw new PhotoError("file_too_large", `File is ${file.size} bytes.`);
  }

  const decoded = await decode(file);
  try {
    const full = { x: 0, y: 0, width: decoded.width, height: decoded.height };
    const resized = fitWithin(decoded, MAX_SIDE_PX);
    const blob = await toJpeg(drawToCanvas(decoded.source, full, resized));

    const crop = centerSquare(decoded, MODEL_CROP_FRACTION);
    const viewSide = Math.max(1, Math.round(Math.min(crop.size, MODEL_VIEW_MAX_PX)));
    const modelView = await toJpeg(
      drawToCanvas(
        decoded.source,
        { x: crop.x, y: crop.y, width: crop.size, height: crop.size },
        { width: viewSide, height: viewSide },
      ),
    );

    return {
      blob,
      url: URL.createObjectURL(blob),
      modelViewUrl: URL.createObjectURL(modelView),
      width: resized.width,
      height: resized.height,
    };
  } finally {
    decoded.release();
  }
}

export function releasePhoto(photo: PreparedPhoto): void {
  URL.revokeObjectURL(photo.url);
  URL.revokeObjectURL(photo.modelViewUrl);
}

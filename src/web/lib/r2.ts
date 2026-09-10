import fs from "node:fs";
import path from "node:path";

import type {
  EffectiveContent,
  EntityData,
  EntityKind,
  IndexItem,
  SiteBundle,
  SiteEntityRecord,
  StoredImage,
} from "@/lib/types";

const publicUrl = (process.env.R2_PUBLIC_URL ?? "").replace(/\/+$/, "");
const siteDataFile = process.env.SITE_DATA_FILE
  ? path.resolve(process.env.SITE_DATA_FILE)
  : path.resolve(process.cwd(), ".generated", "site.json");

let cachedBundle: SiteBundle | null = null;

function validateBundle(value: unknown): SiteBundle {
  if (!value || typeof value !== "object") {
    throw new Error("Invalid site bundle: expected object");
  }

  const candidate = value as Partial<SiteBundle>;

  if (
    candidate.version !== 2 ||
    !candidate.categories ||
    !candidate.products ||
    !Array.isArray(candidate.routes) ||
    !Array.isArray(candidate.root_category_ids)
  ) {
    throw new Error(
      "Invalid site bundle. Run: python -m src.crawler.sync",
    );
  }

  return candidate as SiteBundle;
}

function loadBundle(): SiteBundle {
  if (cachedBundle) {
    return cachedBundle;
  }

  if (!fs.existsSync(siteDataFile)) {
    throw new Error(
      `Site data file is missing: ${siteDataFile}. ` +
        "Run npm run pull-data or npm run dev (predev pulls it automatically).",
    );
  }

  const raw = fs.readFileSync(siteDataFile, "utf-8");
  cachedBundle = validateBundle(JSON.parse(raw));

  return cachedBundle;
}

function entityRecords(
  kind: EntityKind,
): Record<string, SiteEntityRecord> {
  const bundle = loadBundle();
  return kind === "categories" ? bundle.categories : bundle.products;
}

export async function getSiteBundle(): Promise<SiteBundle> {
  return loadBundle();
}

export async function getIndex(kind: EntityKind): Promise<IndexItem[]> {
  return Object.values(entityRecords(kind))
    .map((record) => record.index)
    .sort((a, b) => a.source_id - b.source_id);
}

export async function getEntityData(
  kind: EntityKind,
  sourceId: number,
): Promise<EntityData | null> {
  return entityRecords(kind)[String(sourceId)]?.data ?? null;
}

export async function getEffectiveContent(
  kind: EntityKind,
  sourceId: number,
  language = "ru",
): Promise<EffectiveContent | null> {
  if (language !== "ru") {
    return null;
  }

  return entityRecords(kind)[String(sourceId)]?.content ?? null;
}

function isStoredPublicUrl(value: string): boolean {
  try {
    const url = new URL(value);

    if (
      publicUrl &&
      value.startsWith(`${publicUrl}/`)
    ) {
      return true;
    }

    // Development R2 public endpoints are safe to use even if the
    // process env was not injected into this module for some reason.
    return url.hostname.endsWith(".r2.dev");
  } catch {
    return false;
  }
}

export function storedImageUrl(image?: StoredImage | null): string | null {
  if (!image) return null;

  if (publicUrl && image.r2_key) {
    return `${publicUrl}/${image.r2_key.replace(/^\/+/, "")}`;
  }

  if (
    image.url &&
    /^https?:\/\//i.test(image.url) &&
    isStoredPublicUrl(image.url)
  ) {
    return image.url;
  }

  // Never fall back to image.source_url. If there is no confirmed
  // stored R2 copy, the image is intentionally hidden.
  return null;
}

export function publicObjectUrl(value?: string | null): string | null {
  if (!value) return null;

  if (/^https?:\/\//i.test(value)) {
    return isStoredPublicUrl(value)
      ? value
      : null;
  }

  if (!publicUrl) {
    return null;
  }

  return `${publicUrl}/${value.replace(/^\/+/, "")}`;
}

export function entityMainImage(
  data: EntityData | null,
  fallback?: string | null,
): string | null {
  const image = data?.images?.[0];

  if (image) {
    return storedImageUrl(image);
  }

  return publicObjectUrl(fallback);
}

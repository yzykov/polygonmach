import { cache } from "react";
import { GetObjectCommand, S3Client } from "@aws-sdk/client-s3";
import type {
  EffectiveContent,
  EntityData,
  EntityKind,
  IndexItem,
  SourceContent,
  StoredImage,
} from "@/lib/types";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Environment variable ${name} is not set`);
  return value;
}

const bucket = required("R2_BUCKET");
const publicUrl = (process.env.R2_PUBLIC_URL ?? "").replace(/\/+$/, "");

const client = new S3Client({
  region: "auto",
  endpoint: required("R2_ENDPOINT"),
  credentials: {
    accessKeyId: required("R2_ACCESS_KEY_ID"),
    secretAccessKey: required("R2_SECRET_ACCESS_KEY"),
  },
});

async function bodyToString(body: unknown): Promise<string> {
  if (
    body &&
    typeof body === "object" &&
    "transformToString" in body &&
    typeof (body as { transformToString?: unknown }).transformToString === "function"
  ) {
    return (body as {
      transformToString: (encoding?: string) => Promise<string>;
    }).transformToString("utf-8");
  }
  throw new Error("Unsupported R2 response body");
}

function isNotFound(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const candidate = error as {
    name?: string;
    $metadata?: { httpStatusCode?: number };
  };
  return (
    candidate.name === "NoSuchKey" ||
    candidate.name === "NotFound" ||
    candidate.$metadata?.httpStatusCode === 404
  );
}

export const getJson = cache(async <T,>(key: string): Promise<T | null> => {
  try {
    const response = await client.send(
      new GetObjectCommand({ Bucket: bucket, Key: key }),
    );
    return JSON.parse(await bodyToString(response.Body)) as T;
  } catch (error) {
    if (isNotFound(error)) return null;
    throw error;
  }
});

export const getIndex = cache(async (kind: EntityKind): Promise<IndexItem[]> => {
  return (await getJson<IndexItem[]>(`index/${kind}.json`)) ?? [];
});

export const getEntityData = cache(async (
  kind: EntityKind,
  sourceId: number,
): Promise<EntityData | null> => {
  return getJson<EntityData>(`${kind}/${sourceId}/data.json`);
});

export const getSourceContent = cache(async (
  kind: EntityKind,
  sourceId: number,
  language = "ru",
): Promise<SourceContent | null> => {
  return getJson<SourceContent>(`${kind}/${sourceId}/source/${language}.json`);
});

export const getLocalization = cache(async (
  kind: EntityKind,
  sourceId: number,
  language = "ru",
): Promise<SourceContent | null> => {
  return getJson<SourceContent>(
    `${kind}/${sourceId}/localization/${language}.json`,
  );
});

export const getEffectiveContent = cache(async (
  kind: EntityKind,
  sourceId: number,
  language = "ru",
): Promise<EffectiveContent | null> => {
  const source = await getSourceContent(kind, sourceId, language);
  if (!source) return null;

  const localization = await getLocalization(kind, sourceId, language);
  if (!localization) return { ...source, localized: false };

  return {
    ...source,
    ...localization,
    specifications: {
      ...(source.specifications ?? {}),
      ...(localization.specifications ?? {}),
    },
    localized: true,
  };
});

export function storedImageUrl(image?: StoredImage | null): string | null {
  if (!image) return null;

  // Production: use our public/custom R2 domain.
  if (publicUrl && image.r2_key) {
    return `${publicUrl}/${image.r2_key.replace(/^\/+/, "")}`;
  }

  // Local development: use the original Polygonmach image.
  // This also ignores stale placeholder image.url values like img.example.ru.
  return image.source_url || null;
}

export function publicObjectUrl(value?: string | null): string | null {
  if (!value) return null;
  if (/^https?:\/\//i.test(value)) return value;
  if (!publicUrl) return null;
  return `${publicUrl}/${value.replace(/^\/+/, "")}`;
}

export function entityMainImage(
  data: EntityData | null,
  fallback?: string | null,
): string | null {
  const image = data?.images?.[0];
  if (image) return storedImageUrl(image);

  if (!publicUrl) return null;
  return publicObjectUrl(fallback);
}

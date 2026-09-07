export type EntityKind = "categories" | "products";

export interface IndexItem {
  source_id: number;
  title: string;
  main_image?: string | null;
}

export interface StoredImage {
  source_url: string;
  r2_key: string;
  etag?: string | null;
  last_modified?: string | null;
  sha256?: string | null;
  content_type?: string | null;
  url?: string | null;
}

export interface EntityData {
  source_id: number;
  sources?: Record<string, {
    source_url: string;
    source_hash: string;
  }>;
  images?: StoredImage[];
  updated_at?: string;
}

export interface SourceContent {
  language?: string;
  source_id: number;
  source_url?: string;
  source_hash?: string;
  title?: string;
  text?: string;
  html?: string;

  // Category hierarchy.
  category_ids?: number[];
  product_ids?: number[];

  specifications?: Record<string, string>;
  updated_at?: string;
  [key: string]: unknown;
}

export interface EffectiveContent extends SourceContent {
  localized?: boolean;
}

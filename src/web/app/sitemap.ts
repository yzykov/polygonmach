import type { MetadataRoute } from "next";

import { getIndex } from "@/lib/r2";
import { site } from "@/lib/site";

export const dynamic = "force-static";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [categories, products] = await Promise.all([
    getIndex("categories"),
    getIndex("products"),
  ]);

  return [
    {
      url: `${site.url}/`,
      priority: 1,
    },
    {
      url: `${site.url}/catalog/`,
      priority: 0.9,
    },
    ...categories.map((item) => ({
      url: `${site.url}/catalog/${item.source_id}/`,
      priority: 0.8,
    })),
    ...products.map((item) => ({
      url: `${site.url}/product/${item.source_id}/`,
      priority: 0.7,
    })),
  ];
}
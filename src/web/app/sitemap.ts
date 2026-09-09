import type { MetadataRoute } from "next";

import { getCatalogRoutes } from "@/lib/catalog-url";
import { site } from "@/lib/site";

export const dynamic = "force-static";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const routes = await getCatalogRoutes();

  return [
    {
      url: `${site.url}/`,
      priority: 1,
    },
    {
      url: `${site.url}/catalog/`,
      priority: 0.9,
    },
    ...routes.map((route) => ({
      url: `${site.url}/catalog/${route.segments.join("/")}/`,
      priority:
        route.kind === "category"
          ? 0.8
          : 0.7,
    })),
  ];
}

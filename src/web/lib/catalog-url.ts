import { getSiteBundle } from "@/lib/r2";
import type { CatalogRoute } from "@/lib/types";

export type {
  CatalogRoute,
  CatalogRouteCrumb,
  CatalogRouteKind,
} from "@/lib/types";

function pathKey(path: string[]): string {
  return path.join("/");
}

export async function getCatalogRoutes(): Promise<CatalogRoute[]> {
  return (await getSiteBundle()).routes;
}

export async function catalogCategoryHref(
  sourceId: number,
): Promise<string> {
  const routes = await getCatalogRoutes();
  const route = routes.find(
    (item) => item.kind === "category" && item.source_id === sourceId,
  );

  return route
    ? `/catalog/${route.segments.join("/")}/`
    : `/catalog/category-${sourceId}/`;
}

export async function catalogProductHref(
  sourceId: number,
): Promise<string> {
  const routes = await getCatalogRoutes();
  const route = routes.find(
    (item) => item.kind === "product" && item.source_id === sourceId,
  );

  return route
    ? `/catalog/${route.segments.join("/")}/`
    : `/catalog/product-${sourceId}/`;
}

export async function getCatalogRouteByPath(
  path: string[],
): Promise<CatalogRoute | null> {
  const key = pathKey(path);
  const routes = await getCatalogRoutes();

  return routes.find((item) => pathKey(item.segments) === key) ?? null;
}

export async function childCategoryIds(sourceId: number): Promise<number[]> {
  const bundle = await getSiteBundle();
  return bundle.categories[String(sourceId)]?.content.category_ids ?? [];
}

export async function directProductIds(sourceId: number): Promise<number[]> {
  const bundle = await getSiteBundle();
  return bundle.categories[String(sourceId)]?.content.product_ids ?? [];
}

export async function rootCategoryIds(): Promise<number[]> {
  return (await getSiteBundle()).root_category_ids;
}

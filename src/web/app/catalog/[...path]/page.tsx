import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { CategoryCard } from "@/components/category-card";
import { Container } from "@/components/container";
import { Cta } from "@/components/cta";
import { Gallery, type GalleryImage } from "@/components/gallery";
import { ProductCard } from "@/components/product-card";
import {
  ProductTabs,
  type ProductDisplayTab,
  type ProductTabKind,
} from "@/components/product-tabs";
import {
  childCategoryIds,
  directProductIds,
  getCatalogRouteByPath,
  getCatalogRoutes,
  type CatalogRoute,
} from "@/lib/catalog-url";
import {
  cleanContentHtml,
  formatSectionHeadings,
} from "@/lib/content";
import {
  getEffectiveContent,
  getEntityData,
  getIndex,
  storedImageUrl,
} from "@/lib/r2";
import { site } from "@/lib/site";

export const dynamicParams = false;

export async function generateStaticParams() {
  const routes = await getCatalogRoutes();

  return routes.map((route) => ({
    path: route.segments,
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ path: string[] }>;
}): Promise<Metadata> {
  const { path } = await params;
  const route = await getCatalogRouteByPath(path);

  if (!route) {
    return {};
  }

  return {
    title: route.title,
    alternates: {
      canonical: `/catalog/${route.segments.join("/")}/`,
    },
  };
}

function breadcrumbItems(route: CatalogRoute) {
  return [
    {
      label: "Главная",
      href: "/",
    },
    {
      label: "Каталог",
      href: "/catalog/",
    },
    ...route.breadcrumbs.map((item, index) => ({
      label: item.title,
      href: `/catalog/${route.segments
        .slice(0, index + 1)
        .join("/")}/`,
    })),
    {
      label: route.title,
    },
  ];
}

function normalizedTabTitle(title: string): string {
  return title.toLocaleLowerCase("ru-RU").trim();
}

function isPriceTab(title: string): boolean {
  const value = normalizedTabTitle(title);

  return (
    value.includes("получить цену") ||
    value.includes("get price") ||
    value.includes("fiyat")
  );
}

function tabKind(title: string): ProductTabKind {
  const value = normalizedTabTitle(title);

  if (
    value.includes("галере") ||
    value.includes("gallery") ||
    value.includes("galeri")
  ) {
    return "gallery";
  }

  return "html";
}

function extractImagesFromHtml(
  html?: string,
): string[] {
  if (!html) return [];

  const result: string[] = [];
  const regex =
    /<img[^>]+src=["']([^"']+)["']/gi;

  let match: RegExpExecArray | null;

  while ((match = regex.exec(html)) !== null) {
    const src = match[1]?.trim();

    if (src) {
      result.push(src);
    }
  }

  return result;
}

function removeImagesFromHtml(
  html?: string,
): string {
  if (!html) return "";

  return html.replace(/<img\b[^>]*>/gi, "");
}

function normalizedImageSource(
  value?: string,
): string {
  if (!value) return "";

  try {
    const url = new URL(value);
    url.hash = "";
    url.search = "";
    return url.toString();
  } catch {
    return value.trim();
  }
}

async function CategoryPage({
  route,
}: {
  route: CatalogRoute;
}) {
  const sourceId = route.source_id;

  const [
    content,
    data,
    categoryIndex,
    productIndex,
    childIds,
    productIds,
  ] = await Promise.all([
    getEffectiveContent("categories", sourceId),
    getEntityData("categories", sourceId),
    getIndex("categories"),
    getIndex("products"),
    childCategoryIds(sourceId),
    directProductIds(sourceId),
  ]);

  if (!content) {
    notFound();
  }

  const categoryById = new Map(
    categoryIndex.map((item) => [
      item.source_id,
      item,
    ]),
  );

  const productById = new Map(
    productIndex.map((item) => [
      item.source_id,
      item,
    ]),
  );

  const childCategories = childIds
    .map((childId) => categoryById.get(childId))
    .filter(
      (
        item,
      ): item is NonNullable<typeof item> =>
        Boolean(item),
    );

  const products = productIds
    .map((productId) => productById.get(productId))
    .filter(
      (
        item,
      ): item is NonNullable<typeof item> =>
        Boolean(item),
    );

  const categoryImages: GalleryImage[] =
    (data?.images ?? []).flatMap(
      (image, index) => {
        const src = storedImageUrl(image);

        if (!src) return [];

        return [
          {
            key:
              image.r2_key ||
              image.source_url ||
              `category-${index}`,
            src,
            alt:
              index === 0
                ? content.title ||
                  "Polygonmach"
                : `${
                    content.title ||
                    "Polygonmach"
                  } — фото ${index + 1}`,
          },
        ];
      },
    );

  const mainCategoryImage =
    categoryImages[0] ?? null;

  const descriptionHtml =
    formatSectionHeadings(
      cleanContentHtml(content.html),
    );

  return (
    <>
      <Container className="py-10">
        <Breadcrumbs
          items={breadcrumbItems(route)}
        />

        <section
          className={[
            "mt-12 border-b border-zinc-200 pb-12",
            mainCategoryImage
              ? "grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center"
              : "",
          ].join(" ")}
        >
          <div className="max-w-5xl">
            <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
              Категория оборудования
            </div>

            <h1 className="mt-4 text-5xl font-black leading-[1.02] tracking-[-0.045em] text-zinc-950 md:text-7xl">
              {content.title}
            </h1>

            <p className="mt-6 max-w-3xl text-lg leading-8 text-zinc-600">
              Выберите тип оборудования, чтобы
              посмотреть доступные модели и
              фотографии.
            </p>
          </div>

          {mainCategoryImage ? (
            <div className="overflow-hidden rounded-3xl bg-zinc-100 shadow-sm">
              <img
                src={mainCategoryImage.src}
                alt={mainCategoryImage.alt}
                className="aspect-[4/3] h-full w-full object-cover"
                loading="eager"
              />
            </div>
          ) : null}
        </section>

        {childCategories.length > 0 ? (
          <section className="mt-14">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
                  Разделы
                </div>

                <h2 className="mt-3 text-3xl font-black tracking-tight text-zinc-950 md:text-4xl">
                  {content.title}
                </h2>
              </div>

              <div className="text-sm font-semibold text-zinc-500">
                {childCategories.length} разделов
              </div>
            </div>

            <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {childCategories.map((item) => (
                <CategoryCard
                  key={item.source_id}
                  item={item}
                />
              ))}
            </div>
          </section>
        ) : null}

        {products.length > 0 ? (
          <section
            className={
              childCategories.length > 0
                ? "mt-20"
                : "mt-14"
            }
          >
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
                  Модели
                </div>

                <h2 className="mt-3 text-3xl font-black tracking-tight text-zinc-950 md:text-4xl">
                  Оборудование
                </h2>
              </div>

              <div className="text-sm font-semibold text-zinc-500">
                {products.length} позиций
              </div>
            </div>

            <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {products.map((item) => (
                <ProductCard
                  key={item.source_id}
                  item={item}
                />
              ))}
            </div>
          </section>
        ) : null}

        {descriptionHtml ? (
          <section className="mt-20 border-t border-zinc-200 pt-12">
            <div className="max-w-5xl">
              <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
                О категории
              </div>

              <div
                className={[
                  "prose-industrial mt-8 max-w-none",
                  "[&_h2]:mt-12 [&_h2]:text-3xl [&_h2]:font-black [&_h2]:tracking-tight",
                  "[&_h3]:mt-10 [&_h3]:text-2xl [&_h3]:font-black [&_h3]:tracking-tight",
                  "[&_h4]:mt-8 [&_h4]:text-xl [&_h4]:font-black",
                  "[&_p]:mt-5 [&_p]:leading-8",
                  "[&_ul]:mt-5 [&_ol]:mt-5",
                  "[&_li]:my-2",
                  "[&_table]:my-8 [&_table]:w-full",
                ].join(" ")}
                dangerouslySetInnerHTML={{
                  __html: descriptionHtml,
                }}
              />
            </div>
          </section>
        ) : null}
      </Container>

      <Cta />
    </>
  );
}

async function ProductPage({
  route,
}: {
  route: CatalogRoute;
}) {
  const sourceId = route.source_id;

  const [content, data] = await Promise.all([
    getEffectiveContent("products", sourceId),
    getEntityData("products", sourceId),
  ]);

  if (!content) {
    notFound();
  }

  const fallbackHtml =
    cleanContentHtml(content.html);

  const storedImages: GalleryImage[] =
    (data?.images ?? []).flatMap(
      (image, index) => {
        const src = storedImageUrl(image);

        if (!src) return [];

        return [
          {
            key:
              image.r2_key ||
              image.source_url ||
              `stored-${index}`,
            src,
            alt:
              index === 0
                ? content.title ||
                  "Polygonmach"
                : `${
                    content.title ||
                    "Polygonmach"
                  } — фото ${index + 1}`,
          },
        ];
      },
    );

  const storedImageBySource = new Map(
    (data?.images ?? []).flatMap((image) => {
      const source = normalizedImageSource(
        image.source_url,
      );
      const stored = storedImageUrl(image);

      if (!source || !stored) {
        return [];
      }

      return [[source, stored] as const];
    }),
  );

  const tabImages: GalleryImage[] =
    (content.tabs ?? []).flatMap(
      (tab, tabIndex) =>
        extractImagesFromHtml(tab.html).flatMap(
          (sourceSrc, imageIndex) => {
            const src =
              storedImageBySource.get(
                normalizedImageSource(
                  sourceSrc,
                ),
              );

            if (!src) {
              return [];
            }

            return [{
              key: `tab-${tabIndex}-${imageIndex}-${src}`,
              src,
              alt:
                content.title || "Polygonmach",
            }];
          },
        ),
    );

  const galleryImages: GalleryImage[] = [
    ...storedImages,
    ...tabImages,
  ].filter(
    (image, index, array) =>
      array.findIndex(
        (item) => item.src === image.src,
      ) === index,
  );

  const sourceTabs: ProductDisplayTab[] =
    (content.tabs ?? [])
      .filter(
        (tab) =>
          !isPriceTab(tab.title || ""),
      )
      .map((tab, index) => ({
        id:
          tab.id ||
          `tab-${index + 1}`,
        title:
          tab.title ||
          `Раздел ${index + 1}`,
        kind: tabKind(
          tab.title || "",
        ),
        text: tab.text || "",
        html: removeImagesFromHtml(
          cleanContentHtml(tab.html),
        ),
      }));

  const productTabs: ProductDisplayTab[] =
    galleryImages.length > 0 &&
    !sourceTabs.some(
      (tab) => tab.kind === "gallery",
    )
      ? [
          ...sourceTabs,
          {
            id: "gallery",
            title: "ГАЛЕРЕЯ",
            kind: "gallery",
            html: "",
            text: "",
          },
        ]
      : sourceTabs;

  return (
    <>
      <Container className="py-10">
        <Breadcrumbs
          items={breadcrumbItems(route)}
        />

        <section className="mt-10 grid gap-12 lg:grid-cols-[1.15fr_.85fr]">
          <Gallery images={galleryImages} />

          <aside className="lg:sticky lg:top-28 lg:self-start">
            <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
              Polygonmach
            </div>

            <h1 className="mt-4 text-4xl font-black tracking-tight md:text-5xl">
              {content.title}
            </h1>

            <a
              href={`tel:${site.phoneHref}`}
              className="mt-8 block rounded-xl bg-red-600 px-6 py-4 text-center text-sm font-black text-white hover:bg-red-500"
            >
              Получить предложение
            </a>
          </aside>
        </section>

        {productTabs.length > 0 ? (
          <ProductTabs
            tabs={productTabs}
            galleryImages={galleryImages}
          />
        ) : fallbackHtml ? (
          <section className="mt-20 max-w-4xl border-t border-zinc-200 pt-12">
            <h2 className="text-3xl font-black">
              Описание
            </h2>

            <div
              className="prose-industrial mt-8"
              dangerouslySetInnerHTML={{
                __html: fallbackHtml,
              }}
            />
          </section>
        ) : null}
      </Container>

      <Cta />
    </>
  );
}

export default async function CatalogEntityPage({
  params,
}: {
  params: Promise<{ path: string[] }>;
}) {
  const { path } = await params;
  const route =
    await getCatalogRouteByPath(path);

  if (!route) {
    notFound();
  }

  if (route.kind === "category") {
    return <CategoryPage route={route} />;
  }

  return <ProductPage route={route} />;
}

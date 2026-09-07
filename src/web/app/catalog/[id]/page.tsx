import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { CategoryCard } from "@/components/category-card";
import { Container } from "@/components/container";
import { Cta } from "@/components/cta";
import { ProductCard } from "@/components/product-card";
import {
  getEffectiveContent,
  getIndex,
} from "@/lib/r2";

export const dynamicParams = false;

export async function generateStaticParams() {
  const categories = await getIndex("categories");

  return categories.map((item) => ({
    id: String(item.source_id),
  }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const content = await getEffectiveContent("categories", Number(id));

  return {
    title: content?.title || `Категория ${id}`,
  };
}

export default async function CategoryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const sourceId = Number(id);

  const [content, categoryIndex, productIndex] = await Promise.all([
    getEffectiveContent("categories", sourceId),
    getIndex("categories"),
    getIndex("products"),
  ]);

  if (!content) {
    notFound();
  }

  const categoryById = new Map(
    categoryIndex.map((item) => [item.source_id, item]),
  );

  const productById = new Map(
    productIndex.map((item) => [item.source_id, item]),
  );

  const childCategories = (content.category_ids ?? [])
    .map((childId) => categoryById.get(childId))
    .filter(
      (item): item is NonNullable<typeof item> => Boolean(item),
    );

  const products = (content.product_ids ?? [])
    .map((productId) => productById.get(productId))
    .filter(
      (item): item is NonNullable<typeof item> => Boolean(item),
    );

  return (
    <>
      <Container className="py-10">
        <Breadcrumbs
          items={[
            { label: "Главная", href: "/" },
            { label: "Каталог", href: "/catalog/" },
            {
              label:
                content.title ||
                `Категория ${sourceId}`,
            },
          ]}
        />

        <section className="mt-12 border-b border-zinc-200 pb-12">
          <div className="max-w-5xl">
            <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
              Категория оборудования
            </div>

            <h1 className="mt-4 text-5xl font-black leading-[1.02] tracking-[-0.045em] text-zinc-950 md:text-7xl">
              {content.title}
            </h1>

            <p className="mt-6 max-w-3xl text-lg leading-8 text-zinc-600">
              Выберите тип оборудования, чтобы посмотреть доступные модели,
              фотографии и технические характеристики.
            </p>
          </div>
        </section>

        {childCategories.length ? (
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

        {products.length ? (
          <section className={childCategories.length ? "mt-20" : "mt-14"}>
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

        {!childCategories.length && !products.length ? (
          <div className="mt-14 rounded-2xl border border-zinc-200 bg-zinc-50 p-8 text-zinc-600">
            Для этой категории дочерние разделы или товары пока не определены.
            После повторного запуска crawler связи появятся автоматически.
          </div>
        ) : null}
      </Container>

      <Cta />
    </>
  );
}

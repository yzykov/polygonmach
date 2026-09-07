import Link from "next/link";

import { CategoryCard } from "@/components/category-card";
import { Container } from "@/components/container";
import { Cta } from "@/components/cta";
import { ProductCard } from "@/components/product-card";
import { getEffectiveContent, getIndex } from "@/lib/r2";

export default async function HomePage() {
  const [allCategories, products, root] = await Promise.all([
    getIndex("categories"),
    getIndex("products"),
    getEffectiveContent("categories", 1),
  ]);

  const categoryById = new Map(
    allCategories.map((item) => [item.source_id, item]),
  );

  const rootIds = root?.category_ids ?? [];

  const mainCategories = rootIds.length
    ? rootIds
        .map((id) => categoryById.get(id))
        .filter((item): item is NonNullable<typeof item> => Boolean(item))
    : allCategories
        .filter((item) => item.source_id !== 1)
        .slice(0, 8);

  return (
    <>
      <section className="bg-zinc-950 text-white">
        <Container className="grid min-h-[600px] items-center gap-12 py-20 lg:grid-cols-2">
          <div>
            <div className="text-xs font-black uppercase tracking-[0.24em] text-red-500">
              Оборудование Polygonmach
            </div>

            <h1 className="mt-5 text-5xl font-black leading-[0.98] tracking-[-0.045em] sm:text-6xl">
              Промышленные решения для производства и переработки материалов
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-zinc-400">
              Бетонные и асфальтовые заводы, дробильно-сортировочные комплексы,
              промывочное оборудование и силосы.
            </p>

            <div className="mt-9 flex gap-3">
              <Link
                href="/catalog/"
                className="rounded-xl bg-red-600 px-6 py-4 text-sm font-black"
              >
                Каталог
              </Link>

              <Link
                href="/contacts/"
                className="rounded-xl border border-white/20 px-6 py-4 text-sm font-black"
              >
                Связаться
              </Link>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-3xl bg-zinc-900 p-8">
              <div className="text-5xl font-black">
                {mainCategories.length}
              </div>
              <div className="mt-2 text-zinc-400">
                основных направлений
              </div>
            </div>

            <div className="rounded-3xl bg-red-600 p-8">
              <div className="text-5xl font-black">
                {products.length}
              </div>
              <div className="mt-2 text-red-100">
                моделей
              </div>
            </div>
          </div>
        </Container>
      </section>

      <Container className="py-20">
        <h2 className="text-4xl font-black tracking-tight">
          Основные направления
        </h2>

        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {mainCategories.map((item) => (
            <CategoryCard
              key={item.source_id}
              item={item}
            />
          ))}
        </div>
      </Container>

      <section className="bg-zinc-50 py-20">
        <Container>
          <h2 className="text-4xl font-black tracking-tight">
            Оборудование
          </h2>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {products.slice(0, 8).map((item) => (
              <ProductCard
                key={item.source_id}
                item={item}
              />
            ))}
          </div>
        </Container>
      </section>

      <Cta />
    </>
  );
}

import { Breadcrumbs } from "@/components/breadcrumbs";
import { CategoryCard } from "@/components/category-card";
import { Container } from "@/components/container";
import { Cta } from "@/components/cta";
import { getEffectiveContent, getIndex } from "@/lib/r2";

export default async function CatalogPage() {
  const [allCategories, root] = await Promise.all([
    getIndex("categories"),
    getEffectiveContent("categories", 1),
  ]);

  const byId = new Map(
    allCategories.map((item) => [item.source_id, item]),
  );

  const rootIds = root?.category_ids ?? [];

  const categories = rootIds.length
    ? rootIds
        .map((id) => byId.get(id))
        .filter((item): item is NonNullable<typeof item> => Boolean(item))
    : allCategories.filter((item) => item.source_id !== 1);

  return (
    <>
      <Container className="py-10">
        <Breadcrumbs
          items={[
            { label: "Главная", href: "/" },
            { label: "Каталог" },
          ]}
        />

        <section className="mt-12 max-w-4xl">
          <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
            Polygonmach
          </div>
          <h1 className="mt-4 text-5xl font-black tracking-[-0.04em] text-zinc-950 md:text-7xl">
            Каталог оборудования
          </h1>
          <p className="mt-6 text-lg leading-8 text-zinc-600">
            Выберите направление оборудования. Внутри разделов находятся
            подкатегории и конкретные модели.
          </p>
        </section>

        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((item) => (
            <CategoryCard key={item.source_id} item={item} />
          ))}
        </div>
      </Container>

      <Cta />
    </>
  );
}

import { notFound } from "next/navigation";
import { Breadcrumbs } from "@/components/breadcrumbs";
import { Container } from "@/components/container";
import { Cta } from "@/components/cta";
import { Gallery } from "@/components/gallery";
import { cleanContentHtml } from "@/lib/content";
import { getEffectiveContent, getEntityData, getIndex } from "@/lib/r2";
import { site } from "@/lib/site";

export const dynamicParams = false;

export async function generateStaticParams() {
  return (await getIndex("products")).map((item) => ({
    id: String(item.source_id),
  }));
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const sourceId = Number(id);

  const [content, data] = await Promise.all([
    getEffectiveContent("products", sourceId),
    getEntityData("products", sourceId),
  ]);

  if (!content) notFound();

  const images = data?.images ?? [];
  const specs = Object.entries(content.specifications ?? {});
  const html = cleanContentHtml(content.html);

  return (
    <>
      <Container className="py-10">
        <Breadcrumbs items={[
          { label: "Главная", href: "/" },
          { label: "Каталог", href: "/catalog/" },
          { label: content.title || `Товар ${sourceId}` },
        ]} />

        <section className="mt-10 grid gap-12 lg:grid-cols-[1.15fr_.85fr]">
          <Gallery images={images} title={content.title || ""} />

          <aside className="lg:sticky lg:top-28 lg:self-start">
            <div className="text-xs font-black uppercase tracking-[0.22em] text-red-600">
              Polygonmach
            </div>
            <h1 className="mt-4 text-4xl font-black tracking-tight md:text-5xl">
              {content.title}
            </h1>

            {specs.length ? (
              <div className="mt-8 divide-y divide-zinc-200 border-y border-zinc-200">
                {specs.slice(0, 5).map(([key, value]) => (
                  <div key={key} className="grid grid-cols-[1fr_auto] gap-5 py-4 text-sm">
                    <span className="text-zinc-500">{key}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
            ) : null}

            <a
              href={`tel:${site.phoneHref}`}
              className="mt-8 block rounded-xl bg-red-600 px-6 py-4 text-center text-sm font-black text-white"
            >
              Получить предложение
            </a>
          </aside>
        </section>

        {specs.length ? (
          <section className="mt-20">
            <h2 className="text-3xl font-black">Технические характеристики</h2>
            <div className="mt-8 overflow-hidden rounded-2xl border border-zinc-200">
              {specs.map(([key, value], index) => (
                <div
                  key={`${key}-${index}`}
                  className="grid gap-2 border-b border-zinc-200 px-5 py-4 last:border-b-0 md:grid-cols-2"
                >
                  <div className="font-semibold text-zinc-500">{key}</div>
                  <div className="font-bold">{String(value)}</div>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {html ? (
          <section className="mt-20 max-w-4xl border-t border-zinc-200 pt-12">
            <h2 className="text-3xl font-black">Описание</h2>
            <div
              className="prose-industrial mt-8"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          </section>
        ) : null}
      </Container>

      <Cta />
    </>
  );
}

import { Container } from "@/components/container";
import { site } from "@/lib/site";

export function Cta() {
  return (
    <Container className="mt-24">
      <section className="rounded-3xl bg-zinc-950 px-6 py-10 text-white md:px-12 md:py-14">
        <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="text-xs font-black uppercase tracking-[0.22em] text-red-500">
              Подбор оборудования
            </div>
            <h2 className="mt-3 max-w-3xl text-3xl font-black tracking-tight md:text-5xl">
              Нужно подобрать конфигурацию под вашу задачу?
            </h2>
          </div>
          <a
            href={`tel:${site.phoneHref}`}
            className="rounded-xl bg-red-600 px-6 py-4 text-center text-sm font-black text-white hover:bg-red-500"
          >
            {site.phone}
          </a>
        </div>
      </section>
    </Container>
  );
}

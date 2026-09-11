import { Bitrix24Form } from "@/components/bitrix24-form";
import { Container } from "@/components/container";
import { site } from "@/lib/site";

export default function ContactsPage() {
  return (
    <Container className="py-16">
      <h1 className="text-6xl font-black tracking-tight">
        Контакты
      </h1>

      <div className="mt-10 grid gap-5 md:grid-cols-3">
        <a
          href={`tel:${site.phoneHref}`}
          className="group rounded-2xl bg-red-600 px-6 py-5 text-white transition hover:bg-red-500"
        >
          <div className="text-xs font-black uppercase tracking-[0.18em] text-red-100">
            Телефон
          </div>

          <div className="mt-2 text-2xl font-black">
            {site.phone}
          </div>
        </a>

        <a
          href={`mailto:${site.email}`}
          className="group rounded-2xl bg-zinc-950 px-6 py-5 text-white transition hover:bg-zinc-800"
        >
          <div className="text-xs font-black uppercase tracking-[0.18em] text-zinc-400">
            Email
          </div>

          <div className="mt-2 text-2xl font-black">
            {site.email}
          </div>
        </a>

        <a
          href={`tel:${site.phoneHref2}`}
          className="group rounded-2xl bg-red-600 px-6 py-5 text-white transition hover:bg-red-500"
        >
          <div className="text-xs font-black uppercase tracking-[0.18em] text-red-100">
            Телефон
          </div>

          <div className="mt-2 text-2xl font-black">
            {site.phone2}
          </div>
        </a>
      </div>

      <section className="mt-14 rounded-3xl bg-zinc-950 px-6 py-10 text-white md:px-12 md:py-14">
        <div className="mx-auto max-w-3xl text-center">
          <div className="text-xs font-black uppercase tracking-[0.22em] text-red-500">
            Обратная связь
          </div>

          <h2 className="mt-3 text-3xl font-black tracking-tight md:text-5xl">
            Оставить заявку
          </h2>
        </div>

        <div className="mx-auto mt-10 max-w-2xl">
          <div className="overflow-hidden rounded-2xl bg-white p-4 text-zinc-950 shadow-2xl md:p-6">
            <Bitrix24Form />
          </div>
        </div>
      </section>
    </Container>
  );
}

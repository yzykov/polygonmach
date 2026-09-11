import { Bitrix24Form } from "@/components/bitrix24-form";
import { Container } from "@/components/container";

export function Cta() {
  return (
    <Container className="mt-24">
      <section className="rounded-3xl bg-zinc-950 px-6 py-10 text-white md:px-12 md:py-14">
        <div className="mx-auto max-w-3xl text-center">
          <div className="text-xs font-black uppercase tracking-[0.22em] text-red-500">
            Подбор оборудования
          </div>

          <h2 className="mt-3 text-3xl font-black tracking-tight md:text-5xl">
            Нужно подобрать конфигурацию под вашу задачу?
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

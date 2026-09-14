import Link from "next/link";
import { Container } from "@/components/container";
import { site } from "@/lib/site";

export function Footer() {
  return (
    <footer className="mt-24 bg-zinc-950 text-white">
      <Container className="grid gap-10 py-14 md:grid-cols-3">
        <div>
          <div className="text-xl font-black">{site.name}</div>
          <p className="mt-4 max-w-sm text-sm leading-6 text-zinc-400">
            Компания "ООО ИМПЕРИЯ ТЕХНИКИ" - официальный дистрибьютор POLYGONMACH (Турция)
          </p>
        </div>

        <div className="space-y-3 text-sm">
          <div className="font-bold text-zinc-300">Навигация</div>
          <Link className="block text-zinc-400 hover:text-white" href="/catalog/">Каталог</Link>
          <Link className="block text-zinc-400 hover:text-white" href="/about/">О компании</Link>
          <Link className="block text-zinc-400 hover:text-white" href="/contacts/">Контакты</Link>
        </div>

        <div className="space-y-3 text-sm">
          <div className="font-bold text-zinc-300">Связаться</div>
          <a className="block text-zinc-400 hover:text-white" href={`tel:${site.phoneHref}`}>{site.phone}</a>
          <a className="block text-zinc-400 hover:text-white" href={`tel:${site.phoneHref2}`}>{site.phone2}</a>
          <a className="block text-zinc-400 hover:text-white" href={`mailto:${site.email}`}>{site.email}</a>
        </div>
      </Container>
    </footer>
  );
}

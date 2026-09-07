import Link from "next/link";
import { Container } from "@/components/container";
import { site } from "@/lib/site";

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-black/5 bg-white/95 backdrop-blur">
      <Container className="flex h-20 items-center justify-between gap-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-red-600 text-lg font-black text-white">
            P
          </span>
          <span className="text-lg font-black tracking-tight">{site.name}</span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-semibold text-zinc-700 lg:flex">
          <Link href="/catalog/" className="hover:text-red-600">Оборудование</Link>
          <Link href="/about/" className="hover:text-red-600">О компании</Link>
          <Link href="/contacts/" className="hover:text-red-600">Контакты</Link>
        </nav>

        <a
          href={`tel:${site.phoneHref}`}
          className="rounded-xl bg-zinc-950 px-5 py-3 text-sm font-bold text-white hover:bg-red-600"
        >
          {site.phone}
        </a>
      </Container>
    </header>
  );
}

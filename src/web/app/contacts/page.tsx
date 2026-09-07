import { Container } from "@/components/container";
import { site } from "@/lib/site";

export default function ContactsPage() {
  return (
    <Container className="py-16">
      <h1 className="text-6xl font-black tracking-tight">Контакты</h1>
      <div className="mt-10 grid gap-5 md:grid-cols-2">
        <a href={`tel:${site.phoneHref}`} className="rounded-3xl border border-zinc-200 p-8">
          <div className="text-sm text-zinc-400">Телефон</div>
          <div className="mt-3 text-2xl font-black">{site.phone}</div>
        </a>
        <a href={`mailto:${site.email}`} className="rounded-3xl border border-zinc-200 p-8">
          <div className="text-sm text-zinc-400">Email</div>
          <div className="mt-3 text-2xl font-black">{site.email}</div>
        </a>
      </div>
    </Container>
  );
}

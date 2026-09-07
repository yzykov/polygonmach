import { Container } from "@/components/container";

export default function AboutPage() {
  return (
    <Container className="py-16">
      <h1 className="text-6xl font-black tracking-tight">О компании</h1>
      <p className="mt-8 max-w-3xl text-xl leading-9 text-zinc-600">
        Здесь будет ваш собственный текст о дилере, поставках, монтаже и сервисе.
      </p>
    </Container>
  );
}

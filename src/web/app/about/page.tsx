import type { Metadata } from "next";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { Container } from "@/components/container";
import { Cta } from "@/components/cta";
import sourceData from "@/content/about/source.ru.json";
import localizationData from "@/content/about/localization.ru.json";

interface AboutAdvantage {
  title: string;
  text: string;
}

interface AboutContent {
  source_url: string;
  title: string;
  eyebrow: string;
  lead: string;
  intro: string[];
  mission: {
    title: string;
    text: string;
  };
  directions_title: string;
  directions: string[];
  advantages_title: string;
  advantages: AboutAdvantage[];
  quality: {
    title: string;
    text: string;
  };
}

const source = sourceData as AboutContent;
const localization =
  localizationData as Partial<AboutContent>;

const content: AboutContent = {
  ...source,
  ...localization,
  mission: {
    ...source.mission,
    ...(localization.mission ?? {}),
  },
  quality: {
    ...source.quality,
    ...(localization.quality ?? {}),
  },
};

export const metadata: Metadata = {
  title: `${content.title} — Полигонмаш`,
  description: content.lead,
};

export default function AboutPage() {
  return (
    <>
      <Container className="py-10">
        <Breadcrumbs
          items={[
            { label: "Главная", href: "/" },
            { label: content.title },
          ]}
        />

        <section className="mt-10 overflow-hidden rounded-3xl bg-zinc-950 px-6 py-12 text-white md:px-10 md:py-16">
          <div className="max-w-4xl">
            <div className="text-xs font-black uppercase tracking-[0.24em] text-red-500">
              {content.eyebrow}
            </div>

            <h1 className="mt-5 text-4xl font-black tracking-[-0.04em] sm:text-5xl md:text-6xl">
              {content.title}
            </h1>

            <p className="mt-7 max-w-3xl text-lg leading-8 text-zinc-300 md:text-xl">
              {content.lead}
            </p>
          </div>
        </section>

        <section className="grid gap-10 py-16 lg:grid-cols-[1.15fr_.85fr]">
          <div className="space-y-6 text-base leading-8 text-zinc-700">
            {content.intro.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-6 md:p-8">
            <div className="text-xs font-black uppercase tracking-[0.2em] text-red-600">
              {content.mission.title}
            </div>

            <p className="mt-4 leading-7 text-zinc-700">
              {content.mission.text}
            </p>
          </div>
        </section>

        <section className="border-t border-zinc-200 py-16">
          <h2 className="text-3xl font-black tracking-tight md:text-4xl">
            {content.directions_title}
          </h2>

          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {content.directions.map((direction) => (
              <div
                key={direction}
                className="rounded-2xl border border-zinc-200 bg-white px-5 py-5 text-sm font-bold leading-6 text-zinc-800"
              >
                {direction}
              </div>
            ))}
          </div>
        </section>

        <section className="border-t border-zinc-200 py-16">
          <h2 className="text-3xl font-black tracking-tight md:text-4xl">
            {content.advantages_title}
          </h2>

          <div className="mt-8 grid gap-5 md:grid-cols-2">
            {content.advantages.map((item) => (
              <article
                key={item.title}
                className="rounded-2xl border border-zinc-200 bg-white p-6"
              >
                <h3 className="text-xl font-black">
                  {item.title}
                </h3>

                <p className="mt-3 leading-7 text-zinc-600">
                  {item.text}
                </p>
              </article>
            ))}
          </div>
        </section>

        <section className="border-t border-zinc-200 py-16">
          <div className="max-w-4xl rounded-2xl bg-zinc-50 p-6 md:p-8">
            <h2 className="text-2xl font-black tracking-tight">
              {content.quality.title}
            </h2>

            <p className="mt-4 leading-7 text-zinc-700">
              {content.quality.text}
            </p>
          </div>
        </section>
      </Container>

      <Cta />
    </>
  );
}

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

interface AboutTextSection {
  title: string;
  text: string;
}

interface AboutContent {
  source_url: string;
  title: string;
  eyebrow: string;
  lead: string;
  intro: string[];
  advantages_title: string;
  advantages: AboutAdvantage[];
  manufacturer: AboutTextSection;
  quality: AboutTextSection;
  localization: AboutTextSection;
  warranty: AboutTextSection & {
    note: string;
  };
  service: AboutTextSection;
  dealers: AboutTextSection;
  contacts: {
    website: string;
    phone: string;
    mobile: string;
    email: string;
  };
}

type AboutLocalization = Partial<
  Omit<
    AboutContent,
    | "manufacturer"
    | "quality"
    | "localization"
    | "warranty"
    | "service"
    | "dealers"
    | "contacts"
  >
> & {
  manufacturer?: Partial<AboutTextSection>;
  quality?: Partial<AboutTextSection>;
  localization?: Partial<AboutTextSection>;
  warranty?: Partial<AboutContent["warranty"]>;
  service?: Partial<AboutTextSection>;
  dealers?: Partial<AboutTextSection>;
  contacts?: Partial<AboutContent["contacts"]>;
};

const source: AboutContent = sourceData;
const localization: AboutLocalization = localizationData;

const content: AboutContent = {
  ...source,
  ...localization,
  manufacturer: {
    ...source.manufacturer,
    ...(localization.manufacturer ?? {}),
  },
  quality: {
    ...source.quality,
    ...(localization.quality ?? {}),
  },
  localization: {
    ...source.localization,
    ...(localization.localization ?? {}),
  },
  warranty: {
    ...source.warranty,
    ...(localization.warranty ?? {}),
  },
  service: {
    ...source.service,
    ...(localization.service ?? {}),
  },
  dealers: {
    ...source.dealers,
    ...(localization.dealers ?? {}),
  },
  contacts: {
    ...source.contacts,
    ...(localization.contacts ?? {}),
  },
};

export const metadata: Metadata = {
  title: `${content.title} — Полигонмаш`,
  description: content.lead,
};

function TextCard({
  title,
  text,
}: AboutTextSection) {
  return (
    <article className="rounded-2xl border border-zinc-200 bg-white p-6 md:p-8">
      <h2 className="text-2xl font-black tracking-tight text-zinc-950">
        {title}
      </h2>

      <p className="mt-4 leading-7 text-zinc-700">
        {text}
      </p>
    </article>
  );
}

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
              {content.manufacturer.title}
            </div>

            <p className="mt-4 leading-7 text-zinc-700">
              {content.manufacturer.text}
            </p>
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

        <section className="grid gap-5 border-t border-zinc-200 py-16 lg:grid-cols-2">
          <TextCard {...content.quality} />
          <TextCard {...content.localization} />
          <TextCard {...content.service} />
          <TextCard {...content.dealers} />
        </section>

        <section className="border-t border-zinc-200 py-16">
          <div className="rounded-2xl bg-zinc-50 p-6 md:p-8">
            <h2 className="text-2xl font-black tracking-tight text-zinc-950">
              {content.warranty.title}
            </h2>

            <p className="mt-4 leading-7 text-zinc-700">
              {content.warranty.text}
            </p>

            <p className="mt-5 text-sm leading-6 text-zinc-500">
              {content.warranty.note}
            </p>
          </div>
        </section>
      </Container>

      <Cta />
    </>
  );
}

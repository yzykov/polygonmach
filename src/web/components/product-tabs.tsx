"use client";

import { useEffect, useMemo, useState } from "react";

import type { GalleryImage } from "@/components/gallery";

export type ProductTabKind =
  | "info"
  | "features"
  | "order"
  | "translation"
  | "gallery"
  | "html";

export type ProductDisplayTab = {
  id: string;
  title: string;
  kind?: ProductTabKind;
  html?: string;
  text?: string;
};

function htmlText(html?: string): string {
  return (html ?? "")
    .replace(/<[^>]*>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function hasUsefulText(tab: ProductDisplayTab): boolean {
  const text = `${tab.text ?? ""} ${htmlText(tab.html)}`.trim();
  return text.length > 0;
}

function formatSectionHeadings(html?: string): string {
  if (!html) {
    return "";
  }

  let result = html;

  result = result.replace(
    /<(p|div)([^>]*)>\s*(\*{1,2})\s*([\s\S]*?)\s*\3\s*<\/\1>/gi,
    (_match, _tag, _attrs, _stars, title: string) =>
      `<h3 class="mt-10 mb-4 text-2xl font-black tracking-tight text-zinc-950">${title.trim()}</h3>`,
  );

  result = result.replace(
    /(?:^|<br\s*\/?>)\s*(\*{1,2})\s*([^*<]+?)\s*\1\s*(?=<br\s*\/?>|$)/gim,
    (_match, _stars, title: string) =>
      `<h3 class="mt-10 mb-4 text-2xl font-black tracking-tight text-zinc-950">${title.trim()}</h3>`,
  );

  result = result.replace(
    /\*{1,2}\s*([^*]+?)\s*\*{1,2}/g,
    "<strong>$1</strong>",
  );

  return result;
}

export function ProductTabs({
  tabs,
  galleryImages,
}: {
  tabs: ProductDisplayTab[];
  galleryImages: GalleryImage[];
}) {
  const visibleTabs = useMemo(
    () =>
      tabs.filter((tab) => {
        if (tab.kind === "gallery") {
          return galleryImages.length > 0;
        }

        return hasUsefulText(tab);
      }),
    [tabs, galleryImages.length],
  );

  const [active, setActive] = useState(
    visibleTabs[0]?.id ?? "",
  );

  const [lightboxIndex, setLightboxIndex] =
    useState<number | null>(null);

  useEffect(() => {
    if (
      visibleTabs.length > 0 &&
      !visibleTabs.some((tab) => tab.id === active)
    ) {
      setActive(visibleTabs[0].id);
    }
  }, [active, visibleTabs]);

  useEffect(() => {
    if (lightboxIndex === null) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setLightboxIndex(null);
      }

      if (
        event.key === "ArrowLeft" &&
        galleryImages.length > 1
      ) {
        setLightboxIndex((value) =>
          value === null
            ? null
            : (value - 1 + galleryImages.length) %
              galleryImages.length,
        );
      }

      if (
        event.key === "ArrowRight" &&
        galleryImages.length > 1
      ) {
        setLightboxIndex((value) =>
          value === null
            ? null
            : (value + 1) % galleryImages.length,
        );
      }
    };

    window.addEventListener("keydown", onKeyDown);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [lightboxIndex, galleryImages.length]);

  if (!visibleTabs.length) {
    return null;
  }

  const current =
    visibleTabs.find((tab) => tab.id === active) ??
    visibleTabs[0];

  return (
    <section className="mt-16 border-t border-zinc-200 pt-8">
      <div className="flex flex-wrap gap-1 border-b border-zinc-200">
        {visibleTabs.map((tab) => {
          const selected = tab.id === current.id;

          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActive(tab.id)}
              className={[
                "border-b-2 px-4 py-3 text-sm font-black transition",
                selected
                  ? "border-red-600 text-zinc-950"
                  : "border-transparent text-zinc-500 hover:text-zinc-950",
              ].join(" ")}
            >
              {tab.title}
            </button>
          );
        })}
      </div>

      {current.kind === "gallery" ? (
        <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {galleryImages.map((image, index) => (
            <button
              key={image.key}
              type="button"
              onClick={() => setLightboxIndex(index)}
              className="group overflow-hidden rounded-xl border border-zinc-200 bg-zinc-100"
              aria-label={`Открыть фото ${index + 1}`}
            >
              <div className="aspect-[4/3]">
                <img
                  src={image.src}
                  alt={image.alt}
                  className="h-full w-full object-contain transition duration-300 group-hover:scale-[1.03]"
                />
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div
          className="prose-industrial mt-8 max-w-none"
          dangerouslySetInnerHTML={{
            __html: formatSectionHeadings(current.html),
          }}
        />
      )}

      {lightboxIndex !== null &&
        galleryImages[lightboxIndex] && (
          <div
            className="fixed inset-0 z-[100] flex items-center justify-center bg-black/85 p-4 md:p-8"
            onClick={() => setLightboxIndex(null)}
            role="dialog"
            aria-modal="true"
          >
            <button
              type="button"
              className="absolute right-4 top-4 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-black/50 text-3xl text-white hover:bg-black/70"
              onClick={(event) => {
                event.stopPropagation();
                setLightboxIndex(null);
              }}
              aria-label="Закрыть"
            >
              ×
            </button>

            {galleryImages.length > 1 && (
              <button
                type="button"
                className="absolute left-3 top-1/2 z-10 flex h-14 w-14 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-5xl text-white hover:bg-black/70 md:left-6"
                onClick={(event) => {
                  event.stopPropagation();
                  setLightboxIndex(
                    (lightboxIndex -
                      1 +
                      galleryImages.length) %
                      galleryImages.length,
                  );
                }}
                aria-label="Предыдущее изображение"
              >
                ‹
              </button>
            )}

            <img
              src={galleryImages[lightboxIndex].src}
              alt={galleryImages[lightboxIndex].alt}
              className="max-h-[90vh] max-w-[92vw] object-contain"
              onClick={(event) => event.stopPropagation()}
            />

            {galleryImages.length > 1 && (
              <button
                type="button"
                className="absolute right-3 top-1/2 z-10 flex h-14 w-14 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-5xl text-white hover:bg-black/70 md:right-6"
                onClick={(event) => {
                  event.stopPropagation();
                  setLightboxIndex(
                    (lightboxIndex + 1) %
                      galleryImages.length,
                  );
                }}
                aria-label="Следующее изображение"
              >
                ›
              </button>
            )}

            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/50 px-4 py-2 text-sm font-bold text-white">
              {lightboxIndex + 1} / {galleryImages.length}
            </div>
          </div>
        )}
    </section>
  );
}

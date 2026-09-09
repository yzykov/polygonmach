"use client";

import { useEffect, useState } from "react";

export type GalleryImage = {
  key: string;
  src: string;
  alt: string;
};

export function Gallery({
  images,
}: {
  images: GalleryImage[];
}) {
  const [opened, setOpened] = useState(false);
  const [current, setCurrent] = useState(0);

  const close = () => setOpened(false);

  const previous = () => {
    setCurrent((value) =>
      (value - 1 + images.length) % images.length,
    );
  };

  const next = () => {
    setCurrent((value) => (value + 1) % images.length);
  };

  useEffect(() => {
    if (!opened) {
      return;
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        close();
      } else if (event.key === "ArrowLeft" && images.length > 1) {
        previous();
      } else if (event.key === "ArrowRight" && images.length > 1) {
        next();
      }
    };

    window.addEventListener("keydown", onKeyDown);

    return () => {
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [opened, images.length]);

  if (!images.length) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        onClick={() => {
          setCurrent(0);
          setOpened(true);
        }}
        className="block w-full overflow-hidden rounded-2xl bg-zinc-100"
        aria-label="Открыть изображение"
      >
        <img
          src={images[0].src}
          alt={images[0].alt}
          className="aspect-[4/3] w-full object-contain"
        />
      </button>

      {opened && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/85 p-4 md:p-8"
          onClick={close}
          role="dialog"
          aria-modal="true"
        >
          <button
            type="button"
            className="absolute right-4 top-4 z-10 flex h-12 w-12 items-center justify-center rounded-full bg-black/50 text-3xl text-white hover:bg-black/70"
            onClick={(event) => {
              event.stopPropagation();
              close();
            }}
            aria-label="Закрыть"
          >
            ×
          </button>

          {images.length > 1 && (
            <button
              type="button"
              className="absolute left-3 top-1/2 z-10 flex h-14 w-14 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-5xl text-white hover:bg-black/70 md:left-6"
              onClick={(event) => {
                event.stopPropagation();
                previous();
              }}
              aria-label="Предыдущее изображение"
            >
              ‹
            </button>
          )}

          <img
            src={images[current].src}
            alt={images[current].alt}
            className="max-h-[90vh] max-w-[92vw] object-contain"
            onClick={(event) => event.stopPropagation()}
          />

          {images.length > 1 && (
            <button
              type="button"
              className="absolute right-3 top-1/2 z-10 flex h-14 w-14 -translate-y-1/2 items-center justify-center rounded-full bg-black/50 text-5xl text-white hover:bg-black/70 md:right-6"
              onClick={(event) => {
                event.stopPropagation();
                next();
              }}
              aria-label="Следующее изображение"
            >
              ›
            </button>
          )}

          {images.length > 1 && (
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-black/50 px-4 py-2 text-sm font-bold text-white">
              {current + 1} / {images.length}
            </div>
          )}
        </div>
      )}
    </>
  );
}

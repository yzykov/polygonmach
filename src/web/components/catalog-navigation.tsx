"use client";

import Link from "next/link";
import { createPortal } from "react-dom";
import {
  useEffect,
  useMemo,
  useState,
} from "react";

import type {
  CatalogMenuSection,
} from "@/components/header";

interface CatalogNavigationProps {
  catalogMenu: CatalogMenuSection[];
  phone: string;
  phoneHref: string;
  phone2: string;
  phoneHref2: string;
}

function Chevron({
  className = "",
}: {
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <path
        d="m6 8 4 4 4-4"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function MenuIcon({
  open,
}: {
  open: boolean;
}) {
  return (
    <span className="relative block h-5 w-6">
      <span
        className={[
          "absolute left-0 top-1 h-0.5 w-6 bg-current transition",
          open ? "translate-y-1.5 rotate-45" : "",
        ].join(" ")}
      />
      <span
        className={[
          "absolute left-0 top-2.5 h-0.5 w-6 bg-current transition",
          open ? "opacity-0" : "",
        ].join(" ")}
      />
      <span
        className={[
          "absolute left-0 top-4 h-0.5 w-6 bg-current transition",
          open ? "-translate-y-1.5 -rotate-45" : "",
        ].join(" ")}
      />
    </span>
  );
}

export function CatalogNavigation({
  catalogMenu,
  phone,
  phoneHref,
  phone2,
  phoneHref2,
}: CatalogNavigationProps) {
  const [desktopCatalogOpen, setDesktopCatalogOpen] =
    useState(false);

  const firstSectionId =
    catalogMenu[0]?.sourceId ?? null;

  const [activeSectionId, setActiveSectionId] =
    useState<number | null>(firstSectionId);

  const [mobileOpen, setMobileOpen] =
    useState(false);

  const [mobileCatalogOpen, setMobileCatalogOpen] =
    useState(true);

  const [mobileSectionId, setMobileSectionId] =
    useState<number | null>(null);

  const [mounted, setMounted] = useState(false);

  const activeSection = useMemo(
    () =>
      catalogMenu.find(
        (item) =>
          item.sourceId === activeSectionId,
      ) ??
      catalogMenu[0] ??
      null,
    [catalogMenu, activeSectionId],
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mobileOpen) {
      return;
    }

    const previous =
      document.body.style.overflow;

    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previous;
    };
  }, [mobileOpen]);

  useEffect(() => {
    const onKeyDown = (
      event: KeyboardEvent,
    ) => {
      if (event.key === "Escape") {
        setDesktopCatalogOpen(false);
        setMobileOpen(false);
      }
    };

    window.addEventListener(
      "keydown",
      onKeyDown,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        onKeyDown,
      );
    };
  }, []);

  function closeMobile() {
    setMobileOpen(false);
  }

  return (
    <>
      <div className="hidden h-full flex-1 items-center justify-end gap-8 lg:flex">
        <nav className="flex h-full items-center gap-8 text-sm font-semibold text-zinc-700">
          <div
            className="relative flex h-full items-center"
            onMouseEnter={() =>
              setDesktopCatalogOpen(true)
            }
            onMouseLeave={() =>
              setDesktopCatalogOpen(false)
            }
          >
            <button
              type="button"
              aria-expanded={desktopCatalogOpen}
              aria-haspopup="true"
              onClick={() =>
                setDesktopCatalogOpen(
                  (value) => !value,
                )
              }
              onFocus={() =>
                setDesktopCatalogOpen(true)
              }
              className={[
                "flex h-full items-center gap-1.5 transition",
                desktopCatalogOpen
                  ? "text-red-600"
                  : "hover:text-red-600",
              ].join(" ")}
            >
              Каталог

              <Chevron
                className={[
                  "h-4 w-4 transition-transform duration-200",
                  desktopCatalogOpen
                    ? "rotate-180"
                    : "",
                ].join(" ")}
              />
            </button>

            <div
              className={[
                "absolute left-1/2 top-full z-50 w-[min(980px,calc(100vw-3rem))]",
                "-translate-x-1/2 pt-2 transition duration-150",
                desktopCatalogOpen
                  ? "visible translate-y-0 opacity-100"
                  : "invisible translate-y-2 opacity-0",
              ].join(" ")}
            >
              <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-2xl shadow-black/10">
                <div className="flex items-center justify-between border-b border-zinc-100 px-6 py-4">
                  <div>
                    <div className="text-xs font-black uppercase tracking-[0.18em] text-red-600">
                      Оборудование
                    </div>

                    <div className="mt-1 text-base font-black text-zinc-950">
                      Каталог Polygonmach
                    </div>
                  </div>

                  <Link
                    href="/catalog/"
                    className="rounded-lg px-3 py-2 text-sm font-bold text-red-600 transition hover:bg-red-50"
                    onClick={() =>
                      setDesktopCatalogOpen(false)
                    }
                  >
                    Весь каталог →
                  </Link>
                </div>

                <div className="grid min-h-[360px] grid-cols-[0.88fr_1.12fr]">
                  <div className="border-r border-zinc-100 bg-zinc-50 p-3">
                    <div className="max-h-[62vh] space-y-1 overflow-y-auto pr-1">
                      {catalogMenu.map(
                        (section) => {
                          const active =
                            activeSection?.sourceId ===
                            section.sourceId;

                          return (
                            <button
                              key={
                                section.sourceId
                              }
                              type="button"
                              onMouseEnter={() =>
                                setActiveSectionId(
                                  section.sourceId,
                                )
                              }
                              onFocus={() =>
                                setActiveSectionId(
                                  section.sourceId,
                                )
                              }
                              onClick={() =>
                                setActiveSectionId(
                                  section.sourceId,
                                )
                              }
                              className={[
                                "flex w-full items-center justify-between gap-4 rounded-xl px-4 py-3 text-left text-sm font-bold leading-snug transition",
                                active
                                  ? "bg-white text-red-600 shadow-sm"
                                  : "text-zinc-700 hover:bg-white hover:text-zinc-950",
                              ].join(" ")}
                            >
                              <span>
                                {section.title}
                              </span>

                              <span
                                aria-hidden="true"
                                className={[
                                  "text-lg leading-none transition-transform",
                                  active
                                    ? "translate-x-0.5 text-red-600"
                                    : "text-zinc-400",
                                ].join(" ")}
                              >
                                →
                              </span>
                            </button>
                          );
                        },
                      )}
                    </div>
                  </div>

                  <div className="p-6">
                    {activeSection ? (
                      <>
                        <div className="flex items-start justify-between gap-6">
                          <div>
                            <div className="text-xs font-black uppercase tracking-[0.18em] text-zinc-400">
                              Раздел
                            </div>

                            <h3 className="mt-2 text-2xl font-black leading-tight text-zinc-950">
                              {
                                activeSection.title
                              }
                            </h3>
                          </div>

                          <Link
                            href={
                              activeSection.href
                            }
                            className="shrink-0 rounded-lg bg-red-50 px-3 py-2 text-sm font-black text-red-600 transition hover:bg-red-100"
                            onClick={() =>
                              setDesktopCatalogOpen(
                                false,
                              )
                            }
                          >
                            Все →
                          </Link>
                        </div>

                        {activeSection.children
                          .length > 0 ? (
                          <div className="mt-6 grid max-h-[50vh] grid-cols-2 gap-2 overflow-y-auto pr-1">
                            {activeSection.children.map(
                              (child) => (
                                <Link
                                  key={
                                    child.sourceId
                                  }
                                  href={child.href}
                                  className="rounded-xl border border-zinc-100 px-4 py-3 text-sm font-semibold leading-snug text-zinc-700 transition hover:border-red-100 hover:bg-red-50 hover:text-red-600"
                                  onClick={() =>
                                    setDesktopCatalogOpen(
                                      false,
                                    )
                                  }
                                >
                                  {child.title}
                                </Link>
                              ),
                            )}
                          </div>
                        ) : (
                          <div className="mt-8 rounded-xl bg-zinc-50 p-4 text-sm text-zinc-500">
                            В этом разделе нет
                            подразделов.
                          </div>
                        )}
                      </>
                    ) : (
                      <div className="grid min-h-[280px] place-items-center text-sm text-zinc-500">
                        Разделы каталога пока
                        не загружены.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <Link
            href="/about/"
            className="transition hover:text-red-600"
          >
            О компании
          </Link>

          <Link
            href="/contacts/"
            className="transition hover:text-red-600"
          >
            Контакты
          </Link>
        </nav>

        <a
          href={`tel:${phoneHref}`}
          className="shrink-0 rounded-xl bg-zinc-950 px-5 py-3 text-sm font-bold text-white transition hover:bg-red-600"
        >
          {phone}
        </a>
        <a
          href={`tel:${phoneHref2}`}
          className="shrink-0 rounded-xl bg-red-600 px-5 py-3 text-sm font-bold text-white transition hover:bg-red-600"
        >
          {phone2}
        </a>
      </div>

      <div className="flex items-center gap-2 lg:hidden">
        <a
          href={`tel:${phoneHref}`}
          aria-label={`Позвонить ${phone}`}
          className="grid h-11 w-11 place-items-center rounded-xl border border-zinc-200 text-zinc-800 transition hover:border-red-200 hover:text-red-600"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path
              d="M7.2 3.5 9.6 7.8 7.9 9.5c1.2 2.4 3.2 4.4 5.6 5.6l1.7-1.7 4.3 2.4-.7 3.4c-.2.9-1 1.5-1.9 1.5C9.4 20.7 3.3 14.6 3.3 7.1c0-.9.6-1.7 1.5-1.9l2.4-.7Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </a>

        <a
          href={`tel:${phoneHref2}`}
          aria-label={`Позвонить ${phone2}`}
          className="grid h-11 w-11 place-items-center rounded-xl border border-red-200 bg-red-50 text-red-600 transition hover:bg-red-100"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="h-5 w-5"
            aria-hidden="true"
          >
            <path
              d="M7.2 3.5 9.6 7.8 7.9 9.5c1.2 2.4 3.2 4.4 5.6 5.6l1.7-1.7 4.3 2.4-.7 3.4c-.2.9-1 1.5-1.9 1.5C9.4 20.7 3.3 14.6 3.3 7.1c0-.9.6-1.7 1.5-1.9l2.4-.7Z"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </a>

        <button
          type="button"
          aria-expanded={mobileOpen}
          aria-label={
            mobileOpen
              ? "Закрыть меню"
              : "Открыть меню"
          }
          onClick={() =>
            setMobileOpen((value) => !value)
          }
          className="grid h-11 w-11 place-items-center rounded-xl border border-zinc-200 text-zinc-950 transition hover:border-red-200 hover:text-red-600"
        >
          <MenuIcon open={mobileOpen} />
        </button>
      </div>

      {mounted
        ? createPortal(
            (
              <div
                className={[
                  "fixed inset-0 z-[9999] lg:hidden",
                  mobileOpen
                    ? "pointer-events-auto"
                    : "pointer-events-none",
                ].join(" ")}
                aria-hidden={!mobileOpen}
              >
                <button
                  type="button"
                  aria-label="Закрыть меню"
                  onClick={closeMobile}
                  className={[
                    "absolute inset-0 bg-black/35 backdrop-blur-[1px] transition-opacity",
                    mobileOpen
                      ? "opacity-100"
                      : "opacity-0",
                  ].join(" ")}
                />
              
                <aside
                  className={[
                    "absolute right-0 top-0 z-[10000] flex h-dvh w-[min(92vw,420px)] flex-col bg-white shadow-2xl transition-transform duration-200",
                    mobileOpen
                      ? "translate-x-0"
                      : "translate-x-full",
                  ].join(" ")}
                >
                  <div className="flex h-20 items-center justify-between border-b border-zinc-100 px-5">
                    <div className="text-lg font-black">
                      Меню
                    </div>
              
                    <button
                      type="button"
                      onClick={closeMobile}
                      aria-label="Закрыть меню"
                      className="grid h-10 w-10 place-items-center rounded-xl border border-zinc-200 text-zinc-800"
                    >
                      <MenuIcon open />
                    </button>
                  </div>
              
                  <div className="flex-1 overflow-y-auto px-4 py-4">
                    <nav className="space-y-2">
                      <Link
                        href="/"
                        onClick={closeMobile}
                        className="block rounded-xl px-4 py-3 text-base font-bold text-zinc-950 hover:bg-zinc-50"
                      >
                        Главная
                      </Link>
              
                      <div className="overflow-hidden rounded-xl border border-zinc-200">
                        <button
                          type="button"
                          aria-expanded={
                            mobileCatalogOpen
                          }
                          onClick={() =>
                            setMobileCatalogOpen(
                              (value) => !value,
                            )
                          }
                          className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-base font-black text-zinc-950"
                        >
                          Каталог
              
                          <Chevron
                            className={[
                              "h-5 w-5 transition-transform",
                              mobileCatalogOpen
                                ? "rotate-180"
                                : "",
                            ].join(" ")}
                          />
                        </button>
              
                        {mobileCatalogOpen ? (
                          <div className="border-t border-zinc-100 bg-zinc-50 p-2">
                            <Link
                              href="/catalog/"
                              onClick={closeMobile}
                              className="mb-2 block rounded-lg bg-white px-3 py-2.5 text-sm font-black text-red-600"
                            >
                              Весь каталог →
                            </Link>
              
                            <div className="space-y-1">
                              {catalogMenu.map(
                                (section) => {
                                  const open =
                                    mobileSectionId ===
                                    section.sourceId;
              
                                  return (
                                    <div
                                      key={
                                        section.sourceId
                                      }
                                      className="overflow-hidden rounded-lg bg-white"
                                    >
                                      <button
                                        type="button"
                                        aria-expanded={
                                          open
                                        }
                                        onClick={() =>
                                          setMobileSectionId(
                                            open
                                              ? null
                                              : section.sourceId,
                                          )
                                        }
                                        className="flex w-full items-center justify-between gap-3 px-3 py-3 text-left text-sm font-bold leading-snug text-zinc-900"
                                      >
                                        <span>
                                          {
                                            section.title
                                          }
                                        </span>
              
                                        <Chevron
                                          className={[
                                            "h-4 w-4 shrink-0 transition-transform",
                                            open
                                              ? "rotate-180"
                                              : "",
                                          ].join(" ")}
                                        />
                                      </button>
              
                                      {open ? (
                                        <div className="border-t border-zinc-100 px-2 pb-2 pt-1">
                                          <Link
                                            href={
                                              section.href
                                            }
                                            onClick={
                                              closeMobile
                                            }
                                            className="block rounded-lg px-3 py-2.5 text-sm font-black text-red-600"
                                          >
                                            Все в разделе →
                                          </Link>
              
                                          {section.children.map(
                                            (child) => (
                                              <Link
                                                key={
                                                  child.sourceId
                                                }
                                                href={
                                                  child.href
                                                }
                                                onClick={
                                                  closeMobile
                                                }
                                                className="block rounded-lg px-3 py-2.5 text-sm font-medium leading-snug text-zinc-600 hover:bg-zinc-50 hover:text-red-600"
                                              >
                                                {
                                                  child.title
                                                }
                                              </Link>
                                            ),
                                          )}
                                        </div>
                                      ) : null}
                                    </div>
                                  );
                                },
                              )}
                            </div>
                          </div>
                        ) : null}
                      </div>
              
                      <Link
                        href="/about/"
                        onClick={closeMobile}
                        className="block rounded-xl px-4 py-3 text-base font-bold text-zinc-950 hover:bg-zinc-50"
                      >
                        О компании
                      </Link>
              
                      <Link
                        href="/contacts/"
                        onClick={closeMobile}
                        className="block rounded-xl px-4 py-3 text-base font-bold text-zinc-950 hover:bg-zinc-50"
                      >
                        Контакты
                      </Link>
                    </nav>
                  </div>
              
                  <div className="space-y-2 border-t border-zinc-100 p-4">
                    <a
                      href={`tel:${phoneHref}`}
                      className="block rounded-xl bg-zinc-950 px-5 py-4 text-center text-sm font-black text-white transition hover:bg-zinc-800"
                    >
                      {phone}
                    </a>

                    <a
                      href={`tel:${phoneHref2}`}
                      className="block rounded-xl bg-red-600 px-5 py-4 text-center text-sm font-black text-white transition hover:bg-red-500"
                    >
                      {phone2}
                    </a>
                  </div>
                </aside>
              </div>
            ),
            document.body,
          )
        : null}

    </>
  );
}

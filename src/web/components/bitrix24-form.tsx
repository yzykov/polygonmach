"use client";

import { useEffect, useRef } from "react";

const FORM_ID = "inline/36/xbydxp";
const LOADER_URL =
  "https://cdn-ru.bitrix24.ru/b18390534/crm/form/loader_36.js";

export function Bitrix24Form() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;

    if (!container) {
      return;
    }

    const script = document.createElement("script");

    script.async = true;
    script.setAttribute(
      "data-b24-form",
      FORM_ID,
    );
    script.setAttribute(
      "data-skip-moving",
      "true",
    );

    script.src =
      `${LOADER_URL}?` +
      `${Math.floor(Date.now() / 180000)}`;

    container.appendChild(script);

    return () => {
      container.replaceChildren();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="w-full"
    />
  );
}

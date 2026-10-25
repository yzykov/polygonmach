"use client";

import Script from "next/script";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

const METRIKA_ID = 113787407;

declare global {
  interface Window {
    ym?: (...args: unknown[]) => void;
  }
}

function YandexMetrikaNavigation() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const firstRender = useRef(true);

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }

    if (!window.ym) {
      return;
    }

    const query = searchParams.toString();
    const url =
      window.location.origin +
      pathname +
      (query ? `?${query}` : "");

    window.ym(METRIKA_ID, "hit", url, {
      title: document.title,
      referer: document.referrer,
    });
  }, [pathname, searchParams]);

  return null;
}

export function YandexMetrika() {
  return (
    <>
      <Script id="yandex-metrika" strategy="afterInteractive">
        {`
          (function(m,e,t,r,i,k,a){
            m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
            m[i].l=1*new Date();
            for(var j=0;j<document.scripts.length;j++){
              if(document.scripts[j].src===r){return;}
            }
            k=e.createElement(t);
            a=e.getElementsByTagName(t)[0];
            k.async=1;
            k.src=r;
            a.parentNode.insertBefore(k,a);
          })(window,document,'script','https://mc.yandex.ru/metrika/tag.js?id=113787407','ym');

          ym(113787407,'init',{
            ssr:true,
            defer:true,
            webvisor:true,
            clickmap:true,
            ecommerce:"dataLayer",
            accurateTrackBounce:true,
            trackLinks:true
          });
        `}
      </Script>

      <Suspense fallback={null}>
        <YandexMetrikaNavigation />
      </Suspense>

      <noscript>
        <div>
          <img
            src="https://mc.yandex.ru/watch/113787407"
            style={{ position: "absolute", left: "-9999px" }}
            alt=""
          />
        </div>
      </noscript>
    </>
  );
}
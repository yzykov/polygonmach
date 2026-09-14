import Script from "next/script";

const BITRIX_WIDGET_CSS = `
  .b24-window-mounts [id^="b24-window-mount-"],
  .b24-form [id^="b24-"] {
    --b24-background-color: rgba(255, 255, 255, 1) !important;
  }

  .b24-window-popup-wrapper,
  .b24-window-scrollable,
  .b24-window-popup-body {
    background-color: rgba(255, 255, 255, 1) !important;
  }
`;

export function Bitrix24SiteWidget() {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: BITRIX_WIDGET_CSS }} />

      <Script id="bitrix24-site-widget" strategy="afterInteractive">
        {`
          (function(w,d,u){
            var s=d.createElement('script');
            s.async=true;
            s.src=u+'?'+(Date.now()/60000|0);
            var h=d.getElementsByTagName('script')[0];
            h.parentNode.insertBefore(s,h);
          })(window,document,'https://cdn-ru.bitrix24.ru/b18390534/crm/site_button/loader_2_mb287l.js');
        `}
      </Script>
    </>
  );
}

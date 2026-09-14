import Script from "next/script";

export function Bitrix24SiteWidget() {
  return (
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
  );
}

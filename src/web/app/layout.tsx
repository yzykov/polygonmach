import type { Metadata } from "next";
import "@/app/globals.css";
import { Footer } from "@/components/footer";
import { Header } from "@/components/header";
import { Bitrix24SiteWidget } from "@/components/bitrix24-site-widget";
import { site } from "@/lib/site";

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: `${site.name} — промышленное оборудование Polygonmach`,
    template: `%s | ${site.name}`,
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru" data-scroll-behavior="smooth">
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
        <Bitrix24SiteWidget />
      </body>
    </html>
  );
}

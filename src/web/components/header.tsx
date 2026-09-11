import Link from "next/link";

import { CatalogNavigation } from "@/components/catalog-navigation";
import { Container } from "@/components/container";
import {
  catalogCategoryHref,
  rootCategoryIds,
} from "@/lib/catalog-url";
import { getSiteBundle } from "@/lib/r2";
import { site } from "@/lib/site";

export interface CatalogMenuChild {
  sourceId: number;
  title: string;
  href: string;
}

export interface CatalogMenuSection {
  sourceId: number;
  title: string;
  href: string;
  children: CatalogMenuChild[];
}

async function buildCatalogMenu(): Promise<CatalogMenuSection[]> {
  const [bundle, rootIds] = await Promise.all([
    getSiteBundle(),
    rootCategoryIds(),
  ]);

  const result: CatalogMenuSection[] = [];

  for (const sourceId of rootIds) {
    const record = bundle.categories[String(sourceId)];

    if (!record) {
      continue;
    }

    const title =
      record.content.title?.trim() ||
      record.index.title?.trim();

    if (!title) {
      continue;
    }

    const childIds = Array.isArray(
      record.content.category_ids,
    )
      ? record.content.category_ids
      : [];

    const children = (
      await Promise.all(
        childIds.map(async (childId) => {
          const child =
            bundle.categories[String(childId)];

          if (!child) {
            return null;
          }

          const childTitle =
            child.content.title?.trim() ||
            child.index.title?.trim();

          if (!childTitle) {
            return null;
          }

          return {
            sourceId: childId,
            title: childTitle,
            href: await catalogCategoryHref(childId),
          };
        }),
      )
    ).filter(
      (
        item,
      ): item is CatalogMenuChild => item !== null,
    );

    result.push({
      sourceId,
      title,
      href: await catalogCategoryHref(sourceId),
      children,
    });
  }

  return result;
}

export async function Header() {
  const catalogMenu = await buildCatalogMenu();

  return (
    <header className="sticky top-0 z-50 border-b border-black/5 bg-white/95 backdrop-blur">
      <Container className="flex h-20 items-center justify-between gap-4">
        <Link
          href="/"
          className="flex shrink-0 items-center gap-3"
        >
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-red-600 text-lg font-black text-white">
            P
          </span>

          <span className="text-lg font-black tracking-tight">
            {site.name}
          </span>
        </Link>

        <CatalogNavigation
          catalogMenu={catalogMenu}
          phone={site.phone}
          phoneHref={site.phoneHref}
          phone2={site.phone2}
          phoneHref2={site.phoneHref2}
        />
      </Container>
    </header>
  );
}

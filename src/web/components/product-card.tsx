import Link from "next/link";

import { EntityImage } from "@/components/entity-image";
import { catalogProductHref } from "@/lib/catalog-url";
import {
  entityMainImage,
  getEntityData,
} from "@/lib/r2";
import type { IndexItem } from "@/lib/types";

export async function ProductCard({
  item,
}: {
  item: IndexItem;
}) {
  const [data, href] = await Promise.all([
    getEntityData("products", item.source_id),
    catalogProductHref(item.source_id),
  ]);

  const image = entityMainImage(
    data,
    item.main_image,
  );

  return (
    <Link
      href={href}
      className="group overflow-hidden rounded-2xl border border-zinc-200 bg-white transition hover:-translate-y-1 hover:shadow-card"
    >
      <div className="aspect-[4/3] overflow-hidden bg-zinc-100">
        <EntityImage
          src={image}
          alt={item.title}
          className="h-full w-full transition duration-500 group-hover:scale-[1.035]"
        />
      </div>

      <div className="p-5">
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-zinc-400">
          Polygonmach
        </div>

        <h3 className="mt-2 text-lg font-extrabold leading-snug">
          {item.title}
        </h3>

        <div className="mt-5 text-sm font-bold text-red-600">
          Подробнее →
        </div>
      </div>
    </Link>
  );
}

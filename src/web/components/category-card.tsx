import Link from "next/link";
import { EntityImage } from "@/components/entity-image";
import { entityMainImage, getEntityData } from "@/lib/r2";
import type { IndexItem } from "@/lib/types";

export async function CategoryCard({ item }: { item: IndexItem }) {
  const data = await getEntityData("categories", item.source_id);
  const image = entityMainImage(data, item.main_image);

  return (
    <Link
      href={`/catalog/${item.source_id}/`}
      className="group overflow-hidden rounded-2xl border border-zinc-200 bg-white transition hover:-translate-y-1 hover:shadow-card"
    >
      <div className="aspect-[4/3] overflow-hidden bg-zinc-100">
        <EntityImage
          src={image}
          alt={item.title}
          className="h-full w-full transition duration-500 group-hover:scale-[1.03]"
        />
      </div>
      <div className="p-5">
        <h3 className="text-lg font-extrabold leading-snug">{item.title}</h3>
        <div className="mt-5 text-sm font-bold text-red-600">
          Смотреть оборудование →
        </div>
      </div>
    </Link>
  );
}

import { EntityImage } from "@/components/entity-image";
import { storedImageUrl } from "@/lib/r2";
import type { StoredImage } from "@/lib/types";

export function Gallery({
  images,
  title,
}: {
  images: StoredImage[];
  title: string;
}) {
  if (!images.length) return null;

  const [first, ...rest] = images;

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <div className="overflow-hidden rounded-2xl bg-zinc-100 md:row-span-2">
        <EntityImage
          src={storedImageUrl(first)}
          alt={title}
          className="h-full min-h-[360px] w-full"
        />
      </div>

      {rest.slice(0, 4).map((image, index) => (
        <div
          className="aspect-[4/3] overflow-hidden rounded-2xl bg-zinc-100"
          key={image.r2_key}
        >
          <EntityImage
            src={storedImageUrl(image)}
            alt={`${title} — фото ${index + 2}`}
            className="h-full w-full"
          />
        </div>
      ))}
    </div>
  );
}

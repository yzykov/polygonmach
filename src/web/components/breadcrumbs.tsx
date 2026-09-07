import Link from "next/link";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav className="flex flex-wrap items-center gap-2 text-sm text-zinc-500">
      {items.map((item, index) => (
        <span key={`${item.label}-${index}`} className="flex items-center gap-2">
          {index > 0 ? <span className="text-zinc-300">/</span> : null}
          {item.href ? (
            <Link className="hover:text-red-600" href={item.href}>{item.label}</Link>
          ) : (
            <span className="text-zinc-700">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}

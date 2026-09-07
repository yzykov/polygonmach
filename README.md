# Web

Next.js web frontend for the Polygonmach crawler project.

This directory is intended to live at:

```text
polygonmach/src/web/
```

The root `polygonmach/README.md` is not replaced.

## Install

Run commands from `polygonmach/src/web`:

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000
```

## R2 data

The site reads the existing R2 structure:

```text
index/categories.json
index/products.json

categories/{source_id}/data.json
categories/{source_id}/source/ru.json
categories/{source_id}/localization/ru.json

products/{source_id}/data.json
products/{source_id}/source/ru.json
products/{source_id}/localization/ru.json
```

If `localization/ru.json` exists, its fields override `source/ru.json`.

## Build

```powershell
npm run build
```

Static output:

```text
polygonmach/src/web/out/
```

## Cloudflare Pages

Set:

```text
Root directory: src/web
Build command: npm run build
Build output directory: out
```

R2 credentials are build-time secrets only and must not use `NEXT_PUBLIC_`.

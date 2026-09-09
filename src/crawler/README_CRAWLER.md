# Polygonmach crawler: что и когда запускать

Эта версия разделяет два разных сценария:

1. **Обычная синхронизация с сайтом поставщика** — `python -m src.crawler.sync`.
   Именно её нужно ставить в GitHub Actions, например раз в неделю.
2. **Аварийная пересборка `index/site.json` из уже существующего R2** —
   `python -m src.crawler.build_site_bundle`.
   Это recovery-команда. В обычном расписании её запускать не надо.

Главная цель изменений: после полного crawl **не проходить второй раз по всем
`source/*.json`, `localization/*.json` и `data.json` в R2** только ради сборки
`index/site.json`.

---

## 1. Нормальный полный sync

Запускать из корня репозитория:

```powershell
cd C:\polygonmach\polygonmach
python -m src.crawler.sync
```

### Что делает `sync`

Схема теперь такая:

```text
Polygonmach
    ↓
discovery категорий
    ↓
парсинг категорий RU/TR
    ↓
парсинг товаров RU/TR
    ↓
все актуальные данные уже находятся в памяти crawler-а
    ↓
обновление только изменившихся source/data/images в R2
    ↓
index/categories.json
index/products.json
    ↓
index/site.json собирается ИЗ ПАМЯТИ
    ↓
один PUT site.json только если содержимое изменилось
```

### Что crawler читает из R2 при обычном полном sync

В начале выполняется один обычный GET:

```text
index/site.json
```

Из него crawler получает предыдущие:

- `source_hash` для RU/TR;
- `data.json` snapshot;
- список изображений;
- snapshot ручной RU-локализации;
- предыдущие category/product index entries;
- текущие маршруты.

Поэтому при каждом объекте больше не требуется делать:

```text
GET categories/10/source/ru.json
GET categories/10/source/tr.json
GET categories/10/data.json
GET products/118/source/ru.json
GET products/118/source/tr.json
GET products/118/data.json
...
```

Текущий `site.json` имеет bundle version `2` и хранит необходимые snapshots
для следующего sync.

### Что записывается в R2

Если `source_hash` не изменился, `source/<language>.json` не перезаписывается.

Если `data.json` не изменился, он тоже не перезаписывается.

Если список URL изображений тот же, image sync вообще пропускается:

```text
images: skipped (same source URLs)
```

Если `index/categories.json`, `index/products.json` или `index/site.json`
не изменились, они не записываются повторно.

В конце нормального запуска должно быть:

```text
R2 scan:      NO
Bundle:       index/site.json
```

---

## 2. Еженедельная GitHub Actions job

Для регулярной проверки сайта поставщика использовать **только**:

```bash
python -m src.crawler.sync
```

Например раз в неделю:

```yaml
name: Polygonmach weekly sync

on:
  schedule:
    - cron: "0 3 * * 1"
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install crawler dependencies
        run: |
          python -m pip install --upgrade pip
          pip install playwright boto3 httpx python-dotenv
          python -m playwright install --with-deps chromium

      - name: Sync Polygonmach
        env:
          R2_ENDPOINT: ${{ secrets.R2_ENDPOINT }}
          R2_BUCKET: ${{ secrets.R2_BUCKET }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
          R2_PUBLIC_URL: ${{ secrets.R2_PUBLIC_URL }}
          SOURCE_BASE_URL: https://polygonmach.com
          HEADLESS: "true"
        run: |
          python -m src.crawler.sync
```

`cron` в GitHub Actions задаётся в UTC.

После успешной синхронизации можно вызвать Cloudflare Pages Deploy Hook,
чтобы Pages пересобрал статический сайт и забрал новый `index/site.json`.

---

## 3. Точечная синхронизация одной категории или товара

Используется для разработки, проверки конкретной страницы или ручного
обновления одной сущности.

Категория:

```powershell
python -m src.crawler.sync_one --category 10 --language ru
```

Товар:

```powershell
python -m src.crawler.sync_one --product 118 --language ru
```

Если объект новый и URL ещё неизвестен:

```powershell
python -m src.crawler.sync_one `
  --product 999 `
  --language ru `
  --url "https://polygonmach.com/ru/product/....html"
```

### Что делает `sync_one`

Он:

1. один раз читает `index/site.json`;
2. идёт только на нужную страницу поставщика;
3. обновляет только эту сущность;
4. читает только её `localization/ru.json`, чтобы подхватить ручную правку;
5. пересчитывает route table полностью **в памяти**;
6. обновляет соответствующий `index/categories.json` или
   `index/products.json` без полного R2 scan;
7. записывает `index/site.json`, только если он реально изменился.

В конце будет:

```text
Full R2 scan: NO
```

---

## 4. `build_site_bundle` — только recovery / migration

Команда:

```powershell
python -m src.crawler.build_site_bundle
```

**Не ставить её в еженедельный cron.**

Она нужна, если:

- `index/site.json` был случайно удалён;
- `index/site.json` повреждён;
- нужно восстановить bundle из уже лежащих в R2 JSON;
- вручную менялись `localization/ru.json` сразу у многих сущностей и нужно
  перечитать все localization files;
- нужно мигрировать старый R2 snapshot в новый bundle format без повторного
  crawl поставщика.

Эта команда намеренно читает R2 последовательно:

```text
index/categories.json
index/products.json
        ↓
для каждой категории:
  source/ru.json
  source/tr.json
  localization/ru.json
  data.json
        ↓
для каждого товара:
  source/ru.json
  source/tr.json
  localization/ru.json
  data.json
        ↓
index/site.json
```

Это не DDoS: параллельного шторма запросов нет. Но Class B операций будет
много, поэтому это именно аварийная/ручная команда, а не штатный job.

---

## 5. Что делать с ручной локализацией

Crawler **никогда не записывает**:

```text
categories/{id}/localization/ru.json
products/{id}/localization/ru.json
```

При нормальном weekly sync используется snapshot локализации из
`index/site.json`, поэтому для каждой сущности не выполняется отдельный R2 GET.

Если вручную изменили localization у **одной** сущности, проще запустить:

```powershell
python -m src.crawler.sync_one --category 10 --language ru
```

или:

```powershell
python -m src.crawler.sync_one --product 118 --language ru
```

`sync_one` перечитает именно её localization.

Если вручную массово изменили много localization JSON, запустить один раз:

```powershell
python -m src.crawler.build_site_bundle
```

---

## 6. Первый запуск после установки этой версии

Если `index/site.json` уже существует, можно сразу:

```powershell
python -m src.crawler.sync
```

Если это старый bundle v1, crawler переведёт его в v2. Для записей, которые
уже были помечены как localized, он точечно подхватит существующую ручную
локализацию.

Если `index/site.json` отсутствует, но в R2 уже есть важные ручные
`localization/*.json`, сначала один раз:

```powershell
python -m src.crawler.build_site_bundle
```

а затем обычный:

```powershell
python -m src.crawler.sync
```

Если `index/site.json` отсутствует и ручных localization нет, можно сразу
запустить `sync`: он соберёт новый bundle напрямую из данных поставщика.

---

## 7. Переменные окружения

Используются существующие переменные crawler-а:

```env
R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com
R2_BUCKET=polygonmach
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...

# временно можно pub-xxxx.r2.dev
R2_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev

SOURCE_BASE_URL=https://polygonmach.com
HEADLESS=true
MIN_DELAY_SEC=2
MAX_DELAY_SEC=5
HTTP_TIMEOUT_SEC=30
```

Секреты в Git не коммитить.

---

## 8. Что запускать в разных ситуациях

| Ситуация | Команда |
|---|---|
| Еженедельная проверка Polygonmach | `python -m src.crawler.sync` |
| Проверить одну категорию | `python -m src.crawler.sync_one --category 10 --language ru` |
| Проверить один товар | `python -m src.crawler.sync_one --product 118 --language ru` |
| Новый товар с известным URL | `sync_one --product ... --language ru --url ...` |
| Потерян / повреждён `index/site.json` | `python -m src.crawler.build_site_bundle` |
| Массово правили localization в R2 | `python -m src.crawler.build_site_bundle` |
| Обычная GitHub cron job | **только `python -m src.crawler.sync`** |

---

## 9. Что больше НЕ надо делать

После полного sync не нужно отдельно запускать:

```powershell
python -m src.crawler.build_site_bundle
```

`sync` сам собирает свежий `index/site.json` из уже полученных от поставщика
данных в памяти.

И web не должен на каждой странице обходить все JSON в R2. Web получает один
`index/site.json` перед `next dev` / `next build`, а страницы затем работают с
локальным generated bundle.

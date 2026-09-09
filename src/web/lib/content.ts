import sanitizeHtml from "sanitize-html";

export function cleanContentHtml(html?: string): string {
  if (!html) return "";

  return sanitizeHtml(html, {
    allowedTags: [
      "div",
      "section",
      "article",
      "span",
      "p",
      "h2",
      "h3",
      "h4",
      "h5",
      "ul",
      "ol",
      "li",
      "strong",
      "b",
      "em",
      "i",
      "br",
      "hr",
      "a",
      "table",
      "thead",
      "tbody",
      "tfoot",
      "tr",
      "th",
      "td",
      "dl",
      "dt",
      "dd",
      "blockquote",
    ],
    allowedAttributes: {
      a: ["href", "target", "rel"],
      th: ["colspan", "rowspan"],
      td: ["colspan", "rowspan"],
    },
    allowedSchemes: ["http", "https", "mailto", "tel"],
    disallowedTagsMode: "discard",
  });
}

export function formatSectionHeadings(html?: string): string {
  if (!html) return "";

  let result = html;

  // Отдельный <p>*Заголовок*</p> или <p>**Заголовок**</p>.
  result = result.replace(
    /<(p|div)([^>]*)>\s*(\*{1,2})\s*([\s\S]*?)\s*\3\s*<\/\1>/gi,
    (_match, _tag, _attrs, _stars, title: string) =>
      `<h3>${title.trim()}</h3>`,
  );

  // Отдельная строка *Заголовок* между <br>.
  result = result.replace(
    /(?:^|<br\s*\/?>)\s*(\*{1,2})\s*([^*<]+?)\s*\1\s*(?=<br\s*\/?>|$)/gim,
    (_match, _stars, title: string) =>
      `<h3>${title.trim()}</h3>`,
  );

  // Оставшиеся *...* / **...** считаем обычным выделением.
  result = result.replace(
    /\*{1,2}\s*([^*]+?)\s*\*{1,2}/g,
    "<strong>$1</strong>",
  );

  return result;
}

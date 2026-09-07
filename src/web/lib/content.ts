import sanitizeHtml from "sanitize-html";

export function cleanContentHtml(html?: string): string {
  if (!html) return "";

  return sanitizeHtml(html, {
    allowedTags: [
      "p", "h2", "h3", "h4", "h5",
      "ul", "ol", "li",
      "strong", "b", "em", "i", "br",
      "table", "thead", "tbody", "tr", "th", "td",
      "blockquote"
    ],
    allowedAttributes: {},
    disallowedTagsMode: "discard",
  });
}

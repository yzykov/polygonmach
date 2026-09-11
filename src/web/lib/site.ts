export const site = {
  name: process.env.SITE_NAME || "Полигонмаш",
  url: (process.env.SITE_URL || "https://example.ru").replace(/\/+$/, ""),
  phone: process.env.CONTACT_PHONE || "+7 (000) 000-00-00",
  phoneHref: process.env.CONTACT_PHONE_HREF || "+70000000000",
  phone2: process.env.CONTACT_PHONE_2 || "+7 (000) 000-00-00",
  phoneHref2: process.env.CONTACT_PHONE_HREF_2 || "+70000000000",
  email: process.env.CONTACT_EMAIL || "sales@example.ru",
};

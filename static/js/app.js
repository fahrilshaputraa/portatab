// PortaTap client helpers.
// HTMX handles server-driven interactions; this file only wires up the small
// pieces HTMX does not: CSRF propagation and local browser behaviours.

document.body?.addEventListener("htmx:configRequest", (event) => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (token) {
    event.detail.headers["X-CSRFToken"] = token;
  }
});

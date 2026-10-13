// PortaTap client behaviour.
// HTMX owns server-driven interaction. This file adds the small amount of motion
// the CSS cannot do alone: CSRF, scroll reveals, the pointer spotlight, and
// easing swapped fragments in.
//
// Every effect here is decorative. Each degrades to a static, correct interface
// when the visitor prefers reduced motion.

const calmMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = window.matchMedia("(pointer: fine)").matches;

// HTMX must send the CSRF token on state-changing requests.
document.body?.addEventListener("htmx:configRequest", (event) => {
  const token = document.querySelector('meta[name="csrf-token"]')?.content;
  if (token) {
    event.detail.headers["X-CSRFToken"] = token;
  }
});

// Ease swapped fragments in rather than snapping them into place.
document.body?.addEventListener("htmx:afterSwap", (event) => {
  const target = event.detail?.target;
  if (!(target instanceof Element)) return;
  target.classList.remove("swap-in");
  void target.offsetWidth; // force a reflow so the animation restarts
  target.classList.add("swap-in");
});

// Scroll reveal: sections fade and rise once as they enter the viewport.
// `.reveal` elements start hidden in CSS, so this observer is what shows them.
if (!calmMotion) {
  const revealables = document.querySelectorAll(".reveal");
  if (revealables.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          entry.target.classList.add("is-in");
          observer.unobserve(entry.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px", threshold: 0.08 },
    );
    revealables.forEach((element) => observer.observe(element));
  }
}

// Pointer-tracked spotlight on bento tiles. One delegated listener keeps it
// working for fragments swapped in later.
if (finePointer && !calmMotion) {
  document.addEventListener(
    "pointermove",
    (event) => {
      const tile = event.target instanceof Element ? event.target.closest(".spot") : null;
      if (!tile) return;
      const box = tile.getBoundingClientRect();
      tile.style.setProperty("--mx", `${event.clientX - box.left}px`);
      tile.style.setProperty("--my", `${event.clientY - box.top}px`);
    },
    { passive: true },
  );
}

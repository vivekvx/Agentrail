"use client";

import { useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

let registered = false;

function ensureRegistered() {
  if (registered || typeof window === "undefined") return;
  gsap.registerPlugin(ScrollTrigger);
  registered = true;
}

export function prefersReducedMotion() {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Reveal direct descendants matching `selector` inside `scope` with a
 * staggered fade-rise as they scroll into view. No-ops under reduced motion
 * (elements stay at their natural, fully visible state).
 */
export function useRevealOnScroll(
  scopeRef: React.RefObject<HTMLElement | null>,
  selector = "[data-reveal]",
) {
  useEffect(() => {
    const scope = scopeRef.current;
    if (!scope) return;
    if (prefersReducedMotion()) return;

    ensureRegistered();

    const targets = Array.from(
      scope.querySelectorAll<HTMLElement>(selector),
    );
    if (targets.length === 0) return;

    const ctx = gsap.context(() => {
      targets.forEach((el) => {
        gsap.fromTo(
          el,
          { opacity: 0, y: 24 },
          {
            opacity: 1,
            y: 0,
            duration: 0.7,
            ease: "power3.out",
            scrollTrigger: {
              trigger: el,
              start: "top 88%",
              toggleActions: "play none none none",
            },
          },
        );
      });
    }, scope);

    return () => ctx.revert();
  }, [scopeRef, selector]);
}

/**
 * Entrance timeline for a hero region: children with `data-hero` rise in
 * sequence on mount. Returns immediately under reduced motion.
 */
export function useHeroIntro(
  scopeRef: React.RefObject<HTMLElement | null>,
  selector = "[data-hero]",
) {
  useEffect(() => {
    const scope = scopeRef.current;
    if (!scope) return;
    if (prefersReducedMotion()) return;

    ensureRegistered();

    const ctx = gsap.context(() => {
      gsap.fromTo(
        scope.querySelectorAll(selector),
        { opacity: 0, y: 28 },
        {
          opacity: 1,
          y: 0,
          duration: 0.85,
          ease: "power3.out",
          stagger: 0.09,
        },
      );
    }, scope);

    return () => ctx.revert();
  }, [scopeRef, selector]);
}

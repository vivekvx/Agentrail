"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * Ambient WebGL backdrop. Renders a fixed, full-viewport fragment shader
 * behind all content (pointer-events: none, z-index below the app). The
 * shader is a slow dark flow field with a faint emerald signal grid that
 * evokes a trace being followed -- the product's namesake.
 *
 * Cost controls: dpr capped at 1.5, render loop paused when the tab is
 * hidden, fully disabled under prefers-reduced-motion (renders one static
 * frame instead of animating).
 */

const FRAGMENT_SHADER = /* glsl */ `
  precision highp float;

  uniform vec2 uResolution;
  uniform float uTime;

  // cheap hash + value noise
  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
  }

  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    for (int i = 0; i < 4; i++) {
      v += a * noise(p);
      p *= 2.0;
      a *= 0.5;
    }
    return v;
  }

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution.xy;
    vec2 p = uv;
    p.x *= uResolution.x / uResolution.y;

    float t = uTime * 0.02;

    // slow flowing field
    float flow = fbm(p * 2.2 + vec2(t, t * 0.6));
    flow = fbm(p * 2.0 + flow + vec2(-t * 0.5, t));

    // faint emerald signal grid that drifts
    vec2 g = p * 26.0 + vec2(t * 2.0, -t * 1.2);
    float grid = smoothstep(0.94, 1.0, max(
      abs(sin(g.x)),
      abs(sin(g.y))
    ));
    float gridFade = smoothstep(0.2, 0.85, flow);

    // base dark field with a breath of depth
    vec3 base = mix(vec3(0.03, 0.033, 0.035), vec3(0.05, 0.082, 0.072), flow);
    vec3 emerald = vec3(0.063, 0.725, 0.506);

    // drifting emerald signal grid
    vec3 col = base + emerald * grid * gridFade * 0.34;

    // soft off-center emerald glow that breathes with the flow
    vec2 glowC = vec2(0.3 + 0.05 * sin(t * 0.7), 0.42);
    float glow = smoothstep(0.62, 0.0, length((uv - glowC) * vec2(1.4, 1.0)));
    col += emerald * glow * (0.07 + 0.04 * flow);

    // vignette so edges sink into the page
    float vig = smoothstep(1.35, 0.15, length(uv - 0.5));
    col *= mix(0.6, 1.0, vig);

    gl_FragColor = vec4(col, 1.0);
  }
`;

const VERTEX_SHADER = /* glsl */ `
  void main() {
    gl_Position = vec4(position, 1.0);
  }
`;

export function WebGLBackground() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prefersReduced = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: false,
        powerPreference: "low-power",
      });
    } catch {
      // No WebGL: leave the CSS background as the fallback.
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.Camera();

    const uniforms = {
      uResolution: {
        value: new THREE.Vector2(window.innerWidth, window.innerHeight),
      },
      uTime: { value: 0 },
    };

    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
    scene.add(mesh);

    function onResize() {
      const w = window.innerWidth;
      const h = window.innerHeight;
      renderer.setSize(w, h);
      uniforms.uResolution.value.set(w, h);
    }
    window.addEventListener("resize", onResize);

    let raf = 0;
    const start = performance.now();

    function renderFrame(now: number) {
      uniforms.uTime.value = (now - start) / 1000;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(renderFrame);
    }

    if (prefersReduced) {
      // Single static frame, no loop.
      renderer.render(scene, camera);
    } else {
      raf = requestAnimationFrame(renderFrame);
    }

    function onVisibility() {
      if (prefersReduced) return;
      if (document.hidden) {
        cancelAnimationFrame(raf);
        raf = 0;
      } else if (!raf) {
        raf = requestAnimationFrame(renderFrame);
      }
    }
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", onVisibility);
      mesh.geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="pointer-events-none fixed inset-0 z-0"
    />
  );
}

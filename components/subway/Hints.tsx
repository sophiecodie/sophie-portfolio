"use client";
// Navigation hints (2026-11-20), after first-time visitors couldn't tell where the project
// posters were or that the newspaper scrolls:
//  - PosterPointers: bouncing LED arrows over each project poster that's on screen, with its
//    route bullet. Clicking one opens that project.
//  - StepArrows: Street View-style chevrons near the bottom of the screen that walk to the
//    next or previous stop on the floor, each labeled with where it goes.
//  - ScrollCue: a "More below" tab pinned to the bottom of any scrolling panel while there is
//    more to read. Put it as the last child inside the panel.
// Plain React + CSS (./hints.css), no extra libraries.
import { useEffect, useRef, useState } from "react";
import type { DollhouseScene } from "./scene";
import "./hints.css";

type Bulleted = (id: string) => [string, string, string?];

function Dot({ id, bulletOf, size }: { id: string; bulletOf: Bulleted; size: number }) {
  const [l, c, ink] = bulletOf(id);
  return <span className="sw-bullet" style={{ background: c, color: ink ?? "#fff", width: size, height: size, fontSize: size * 0.62 }} aria-hidden="true">{l}</span>;
}

// ------------------------------------------------------------------ arrows over the posters
// The posters hang on the platform's right-hand tile wall (components/posters/posterWall.ts):
// face 10 cm off the wall at x = 5, 1.04 m tall, centered 1.45 m up, one every projectStep.
const POSTER_FACE_X = 4.88, POSTER_TOP = 1.99, POSTER_BOTTOM = 0.93;
const MAX_POINTERS = 3;

export function PosterPointers({ scene, y0, step, ids, bulletOf, titleOf, onGo }: {
  scene: DollhouseScene | null;
  y0: number; step: number; // where the first poster hangs along the track, and the spacing
  ids: string[];
  bulletOf: Bulleted;
  titleOf: (id: string) => string;
  onGo: (id: string) => void;
}) {
  const [spots, setSpots] = useState<{ id: string; x: number; y: number; h: number }[]>([]);
  useEffect(() => {
    if (!scene) return;
    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      const W = window.innerWidth, H = window.innerHeight;
      let next: { id: string; x: number; y: number; h: number }[] = [];
      ids.forEach((id, i) => {
        const y = y0 + i * step;
        const top = [POSTER_FACE_X, y, POSTER_TOP], bottom = [POSTER_FACE_X, y, POSTER_BOTTOM];
        if (!scene.ahead(top)) return;
        const a = scene.toScreen(top), b = scene.toScreen(bottom);
        const h = b.y - a.y;
        // skip posters that are off screen or too far away to make out
        if (a.x < 30 || a.x > W - 30 || a.y < 100 || a.y > H - 40 || h < 48) return;
        next.push({ id, x: Math.round(a.x), y: Math.round(a.y - 6), h: Math.round(h) });
      });
      // the nearest few only, so the far end of the platform doesn't turn into a pile of arrows
      next = next.sort((p, q) => q.h - p.h).slice(0, MAX_POINTERS).sort((p, q) => ids.indexOf(p.id) - ids.indexOf(q.id));
      setSpots((o) => (o.length === next.length && o.every((s, i) => s.id === next[i].id && Math.abs(s.x - next[i].x) < 1 && Math.abs(s.y - next[i].y) < 1) ? o : next));
    };
    tick();
    return () => cancelAnimationFrame(raf);
  }, [scene, ids, y0, step]);
  return (
    <div className="sw-ptrs" aria-label="Project posters">
      {spots.map((s, i) => (
        <button key={s.id} className="sw-ptr" style={{ left: s.x, top: s.y, ["--d" as string]: `${i * 0.12}s`, ["--k" as string]: Math.max(0.75, Math.min(1.15, s.h / 160)) }}
          onClick={() => onGo(s.id)} aria-label={"Open " + titleOf(s.id)} title={titleOf(s.id)}>
          <span className="sw-ptr-tag"><Dot id={s.id} bulletOf={bulletOf} size={20} /><span>Open</span></span>
          <svg className="sw-ptr-arrow" viewBox="0 0 24 16" aria-hidden="true"><path d="M2 3l10 10L22 3" /></svg>
        </button>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ Street View-style step arrows
type Step = { id: string; label: string; bullet?: string } | null;
export function StepArrows({ prev, next, bulletOf, onGo, pulse = false }: {
  prev: Step; next: Step; bulletOf: Bulleted; onGo: (id: string) => void; pulse?: boolean;
}) {
  if (!prev && !next) return null;
  const one = (s: NonNullable<Step>, dir: "fwd" | "back") => (
    <button className={"sw-go-btn " + dir + (pulse && dir === "fwd" ? " pulse" : "")} onClick={() => onGo(s.id)}
      aria-label={(dir === "fwd" ? "Next stop: " : "Previous stop: ") + s.label}>
      <span className="sw-go-chev" aria-hidden="true">
        <svg viewBox="0 0 48 32"><path d="M6 26L24 8l18 18" /></svg>
      </span>
      <span className="sw-go-label">
        <small>{dir === "fwd" ? "Next" : "Back"}</small>
        {s.bullet && <Dot id={s.bullet} bulletOf={bulletOf} size={18} />}
        <span>{s.label}</span>
      </span>
    </button>
  );
  return (
    <nav className="sw-go" aria-label="Walk to the next stop">
      {next && one(next, "fwd")}
      {prev && one(prev, "back")}
    </nav>
  );
}

// ------------------------------------------------------------------ "More below" on scrolling panels
function scrollerOf(el: HTMLElement | null): HTMLElement | null {
  for (let p = el?.parentElement ?? null; p; p = p.parentElement) {
    const o = getComputedStyle(p).overflowY;
    if (o === "auto" || o === "scroll") return p;
  }
  return null;
}

export function ScrollCue({ as = "div", label = "More below" }: { as?: "div" | "li"; label?: string }) {
  const ref = useRef<HTMLElement | null>(null);
  const [more, setMore] = useState(false);
  useEffect(() => {
    const sc = scrollerOf(ref.current);
    if (!sc) return;
    const check = () => setMore(sc.scrollHeight - sc.clientHeight - sc.scrollTop > 24);
    check();
    // content (images, fonts, the card's opening animation) can change the height after mount
    const ro = new ResizeObserver(check);
    ro.observe(sc);
    for (const c of Array.from(sc.children)) ro.observe(c);
    const t = window.setTimeout(check, 1000);
    sc.addEventListener("scroll", check, { passive: true });
    return () => { ro.disconnect(); window.clearTimeout(t); sc.removeEventListener("scroll", check); };
  }, []);
  const down = () => {
    const sc = scrollerOf(ref.current);
    sc?.scrollBy({ top: sc.clientHeight * 0.7, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  };
  const Tag = as;
  return (
    <Tag ref={ref as never} className={"sw-more" + (more ? " on" : "")} aria-hidden={!more}>
      <button onClick={down} tabIndex={more ? 0 : -1}>
        <span>{label}</span>
        <svg viewBox="0 0 24 16" aria-hidden="true"><path d="M3 4l9 9 9-9" /></svg>
      </button>
    </Tag>
  );
}

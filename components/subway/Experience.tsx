"use client";
// The subway portfolio: a baked Blender station you ride through, stop by stop.
// Ways to move: scroll / arrow keys / Next stop, the line map, the arrivals board,
// clicking props in the station, or the plain "All stops" list.
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { projects } from "@/data/projects";
import { favoriteBooks, writing } from "@/data/library";
import { site } from "@/data/site";
import type { Layout } from "./scene";

const BASE = "/subway";
const LINES = [
  { key: "data", name: "Data line", letter: "D", color: "#e8732c", stops: ["new-york-census", "purchase-intent", "college-app-atlas"] },
  { key: "health", name: "Health line", letter: "H", color: "#2a9d8f", stops: ["agent00hl7", "dream-team", "neurobiome"] },
  { key: "words", name: "Words line", letter: "W", color: "#c2508a", stops: ["folio", "reading"] },
];
const BULLET: Record<string, [string, string]> = {
  "college-app-atlas": ["A", "#3a5ccc"], "purchase-intent": ["M", "#e8732c"], "new-york-census": ["N", "#e6a823"],
  folio: ["F", "#c2508a"], agent00hl7: ["7", "#2a9d8f"], "dream-team": ["D", "#7c5cbf"], neurobiome: ["B", "#4f9a5b"],
  reading: ["W", "#a0522d"],
};
const PROJECT_IDS = ["college-app-atlas", "purchase-intent", "new-york-census", "folio", "agent00hl7", "dream-team", "neurobiome"];
// the order "Next stop" rides through
const ROUTE = ["title", "map", "board", ...PROJECT_IDS.map((id) => "project:" + id), "newsstand", "exit"];
const CAPTION: Record<string, string> = {
  title: "The train is pulling in. Click it, scroll, or pick a stop.",
  map: "Choose a line: each one groups projects by what they're about.",
  board: "Every project is a train. Pick one from the board.",
  newsstand: "Favorite books and things I've written.",
  exit: "Up the stairs: who I am and how to reach me.",
};

function Bullet({ id, size = 28 }: { id: string; size?: number }) {
  const [l, c] = BULLET[id] ?? ["S", "#e8732c"];
  return (
    <span className="sw-bullet" style={{ background: c, width: size, height: size, fontSize: size * 0.55 }} aria-hidden="true">{l}</span>
  );
}

const titleOf = (id: string) => (id === "reading" ? "Books & Writing" : projects.find((p) => p.id === id)?.title ?? id);

export default function Experience() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<import("./scene").SubwayScene | null>(null);
  const layoutRef = useRef<Layout | null>(null);
  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [stop, setStop] = useState("title");
  const [listOpen, setListOpen] = useState(false);
  const [line, setLine] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const wheelLock = useRef(0);

  const go = useCallback((id: string) => {
    if (id === "reading") id = "newsstand";
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L || !L.stops[id]) return;
    s.goTo(L.stops[id]);
    setStop(id);
    setListOpen(false);
    setLine(null);
    if (typeof window !== "undefined") history.replaceState(null, "", "#" + id.replace("project:", ""));
  }, []);

  const stopRef = useRef("title");
  useEffect(() => { stopRef.current = stop; }, [stop]);
  const step = useCallback((dir: 1 | -1) => {
    const i = Math.max(0, ROUTE.indexOf(stopRef.current));
    const next = ROUTE[Math.min(ROUTE.length - 1, Math.max(0, i + dir))];
    if (next !== stopRef.current) go(next);
  }, [go]);

  useEffect(() => {
    let disposed = false;
    (async () => {
      try {
        const [{ SubwayScene }, layout] = await Promise.all([
          import("./scene"),
          fetch(BASE + "/layout.json").then((r) => r.json() as Promise<Layout>),
        ]);
        if (disposed || !canvasRef.current) return;
        layoutRef.current = layout;
        const s = new SubwayScene(canvasRef.current, layout);
        s.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        sceneRef.current = s;
        s.resize();
        s.start();
        await s.load(BASE, setProgress);
        if (disposed) return;
        setReady(true);
        s.arrive();
        const hash = location.hash.slice(1);
        if (hash) {
          const id = PROJECT_IDS.includes(hash) ? "project:" + hash : hash;
          if (layout.stops[id]) setTimeout(() => go(id), 400);
        }
      } catch (e) {
        console.error(e);
        setFailed(true);
      }
    })();
    const onResize = () => sceneRef.current?.resize();
    window.addEventListener("resize", onResize);
    return () => { disposed = true; window.removeEventListener("resize", onResize); sceneRef.current?.dispose(); };
  }, [go]);

  // keyboard + wheel = ride forward/back
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.closest?.("input,textarea")) return;
      if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === "PageDown") { e.preventDefault(); step(1); }
      if (e.key === "ArrowLeft" || e.key === "ArrowUp" || e.key === "PageUp") { e.preventDefault(); step(-1); }
      if (e.key === "Escape") { setListOpen(false); setLine(null); }
    };
    const onWheel = (e: WheelEvent) => {
      if ((e.target as HTMLElement)?.closest?.(".sw-panel,.sw-list")) return;
      const now = performance.now();
      if (now - wheelLock.current < 900 || Math.abs(e.deltaY) < 12) return;
      wheelLock.current = now;
      step(e.deltaY > 0 ? 1 : -1);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("wheel", onWheel, { passive: true });
    return () => { window.removeEventListener("keydown", onKey); window.removeEventListener("wheel", onWheel); };
  }, [step]);

  // touch swipe
  useEffect(() => {
    let y0 = 0, x0 = 0;
    const s = (e: TouchEvent) => { y0 = e.touches[0].clientY; x0 = e.touches[0].clientX; };
    const end = (e: TouchEvent) => {
      if ((e.target as HTMLElement)?.closest?.(".sw-panel,.sw-list,button,a")) return;
      const dy = y0 - e.changedTouches[0].clientY, dx = x0 - e.changedTouches[0].clientX;
      if (Math.max(Math.abs(dx), Math.abs(dy)) > 50) step((Math.abs(dy) > Math.abs(dx) ? dy : dx) > 0 ? 1 : -1);
    };
    window.addEventListener("touchstart", s, { passive: true });
    window.addEventListener("touchend", end, { passive: true });
    return () => { window.removeEventListener("touchstart", s); window.removeEventListener("touchend", end); };
  }, [step]);

  const onCanvasClick = (e: React.MouseEvent) => {
    const id = sceneRef.current?.pick(e.clientX, e.clientY);
    if (!id) return;
    if (id === "train") go("map");
    else go(id);
  };
  const onCanvasMove = (e: React.MouseEvent) => {
    const s = sceneRef.current; if (!s) return;
    s.setPointer((e.clientX / window.innerWidth) * 2 - 1, -((e.clientY / window.innerHeight) * 2 - 1));
    const id = s.pick(e.clientX, e.clientY);
    setHover(id && id !== stop ? id : null);
  };

  const project = stop.startsWith("project:") ? projects.find((p) => p.id === stop.slice(8)) : undefined;
  const routeIdx = ROUTE.indexOf(stop);
  const nextId = ROUTE[routeIdx + 1];
  const nextLabel = useMemo(() => {
    if (!nextId) return null;
    if (nextId.startsWith("project:")) return titleOf(nextId.slice(8));
    return { map: "Line map", board: "Arrivals board", newsstand: "Books & Writing", exit: "About & contact" }[nextId] ?? nextId;
  }, [nextId]);

  const hoverLabel = hover ? (hover.startsWith("project:") ? titleOf(hover.slice(8)) :
    { map: "Line map", board: "Arrivals board", newsstand: "Books & Writing", exit: "About & contact", train: "Board the train", title: "Platform" }[hover]) : null;

  return (
    <div className={"sw-root" + (hover ? " sw-hovering" : "")}>
      <canvas ref={canvasRef} className="sw-canvas" onClick={onCanvasClick} onMouseMove={onCanvasMove}
        aria-label="A 3D subway station you can ride through. Use the menus to navigate." role="img" />

      {!ready && !failed && (
        <div className="sw-loading" role="status">
          <div className="sw-loading-sign"><Bullet id="purchase-intent" /> <span>Sophie Shih&apos;s Portfolio</span></div>
          <div className="sw-loading-bar"><span style={{ width: `${Math.round(progress * 100)}%` }} /></div>
          <p>Train approaching… {Math.round(progress * 100)}%</p>
        </div>
      )}
      {failed && (
        <div className="sw-loading" role="alert">
          <p>The 3D station couldn&apos;t load on this device. Here are all the stops instead.</p>
        </div>
      )}

      <header className="sw-nav">
        <button className="sw-name" onClick={() => go("title")}><Bullet id="purchase-intent" size={22} /> SOPHIE SHIH</button>
        <nav aria-label="Stations">
          <button onClick={() => go("map")} aria-current={stop === "map"}>Line map</button>
          <button onClick={() => go("board")} aria-current={stop === "board"}>Arrivals</button>
          <button onClick={() => go("newsstand")} aria-current={stop === "newsstand"}>Books</button>
          <button onClick={() => go("exit")} aria-current={stop === "exit"}>About</button>
          <button className="sw-all" onClick={() => setListOpen((v) => !v)} aria-expanded={listOpen}>All stops</button>
        </nav>
      </header>

      {hoverLabel && <div className="sw-tip" aria-hidden="true">{hoverLabel} →</div>}

      {/* Stop-specific panels */}
      {ready && stop === "title" && (
        <div className="sw-hero">
          <p className="sw-eyebrow">NOW ARRIVING</p>
          <h1>Sophie Shih</h1>
          <p>{site.lede}</p>
          <div className="sw-row">
            <button className="sw-btn" onClick={() => go("map")}>Board the train →</button>
            <button className="sw-btn ghost" onClick={() => setListOpen(true)}>See every stop</button>
          </div>
        </div>
      )}

      {ready && stop === "map" && (
        <aside className="sw-panel">
          <p className="sw-eyebrow">CHOOSE YOUR LINE</p>
          {LINES.map((l) => (
            <div key={l.key} className="sw-line">
              <button className="sw-line-head" onClick={() => setLine(line === l.key ? null : l.key)} aria-expanded={line === l.key}>
                <span className="sw-bullet" style={{ background: l.color }}>{l.letter}</span> {l.name}
              </button>
              {line === l.key && (
                <ol className="sw-stops" style={{ borderColor: l.color }}>
                  {l.stops.map((id) => (
                    <li key={id}><button onClick={() => go(id === "reading" ? "newsstand" : "project:" + id)}>{titleOf(id)}</button></li>
                  ))}
                </ol>
              )}
            </div>
          ))}
        </aside>
      )}

      {ready && stop === "board" && (
        <aside className="sw-panel sw-board">
          <p className="sw-eyebrow">NEXT TRAINS</p>
          {[...PROJECT_IDS, "reading"].map((id, i) => (
            <button key={id} className="sw-board-row" onClick={() => go(id === "reading" ? "newsstand" : "project:" + id)}>
              <Bullet id={id} size={24} /> <span>{titleOf(id)}</span>
              <em>{["Arriving", "2 min", "4 min", "6 min", "9 min", "12 min", "15 min", "Express"][i]}</em>
            </button>
          ))}
        </aside>
      )}

      {ready && project && (
        <aside className="sw-panel sw-project">
          <div className="sw-ptitle"><Bullet id={project.id} size={34} /><div><p className="sw-eyebrow">{project.year} · {project.context}</p><h2>{project.title}</h2></div></div>
          {project.image && <img src={project.image} alt="" className="sw-pimg" />}
          <p>{project.summary}</p>
          <ul>{project.highlights.map((h) => <li key={h}>{h}</li>)}</ul>
          <p className="sw-tech">{project.tech}</p>
          <div className="sw-row">{project.links.map((l) => <a key={l.href} className="sw-btn" href={l.href} target="_blank" rel="noopener">{l.label} ↗</a>)}</div>
        </aside>
      )}

      {ready && stop === "newsstand" && (
        <aside className="sw-panel">
          <p className="sw-eyebrow">ON THE SHELF</p>
          <div className="sw-covers">{favoriteBooks.map((b) => <figure key={b.title}><img src={b.cover} alt={`${b.title} by ${b.author}`} /><figcaption>{b.title}</figcaption></figure>)}</div>
          <p className="sw-eyebrow" style={{ marginTop: 18 }}>WRITTEN BY ME</p>
          <ul className="sw-writing">{writing.map((w) => <li key={w.href}><a href={w.href} target="_blank" rel="noopener">{w.title}</a><span>{w.meta}</span></li>)}</ul>
        </aside>
      )}

      {ready && stop === "exit" && (
        <aside className="sw-panel">
          <div className="sw-about"><img src={site.headshot} alt="Sophie Shih" /><div><p className="sw-eyebrow">STREET LEVEL</p><h2>{site.name}</h2></div></div>
          <p>{site.lede}</p>
          <div className="sw-row">
            <a className="sw-btn" href={`mailto:${site.email}`}>Email</a>
            <a className="sw-btn" href={site.linkedin} target="_blank" rel="noopener">LinkedIn ↗</a>
            <a className="sw-btn" href={site.github} target="_blank" rel="noopener">GitHub ↗</a>
            <a className="sw-btn" href={site.resume} target="_blank" rel="noopener">Résumé ↗</a>
          </div>
        </aside>
      )}

      {ready && stop !== "title" && (
        <div className="sw-caption">
          <p className="sw-eyebrow">{stop.startsWith("project:") ? "THIS STOP" : "NOW AT"}</p>
          <p>{project ? project.summary.split(".")[0] + "." : CAPTION[stop]}</p>
          <div className="sw-row">
            <button className="sw-btn ghost" onClick={() => step(-1)} aria-label="Previous stop">←</button>
            {nextLabel && <button className="sw-btn" onClick={() => step(1)}>Next stop: {nextLabel} →</button>}
          </div>
        </div>
      )}

      {(listOpen || failed) && (
        <div className="sw-list" role="dialog" aria-label="All stops">
          <div className="sw-list-inner">
            <div className="sw-list-head"><h2>All stops</h2>{!failed && <button onClick={() => setListOpen(false)} aria-label="Close">✕</button>}</div>
            <ol>
              {projects.filter((p) => !p.isReadingShelf).map((p) => (
                <li key={p.id}>
                  {failed ? <a href={p.links[0]?.href}><Bullet id={p.id} size={24} /> {p.title}</a>
                    : <button onClick={() => go("project:" + p.id)}><Bullet id={p.id} size={24} /> <span>{p.title}</span><em>{p.summary}</em></button>}
                </li>
              ))}
              <li><button onClick={() => go("newsstand")}><Bullet id="reading" size={24} /> <span>Books &amp; Writing</span><em>Favorite books and my essays.</em></button></li>
              <li><button onClick={() => go("exit")}><span className="sw-bullet" style={{ background: "#2a2219" }}>↑</span> <span>About &amp; contact</span><em>{site.email}</em></button></li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

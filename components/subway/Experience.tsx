"use client";
// The subway portfolio, as a dollhouse. The station is cut open into three levels (street,
// mezzanine, platform) that are all on screen at once. Click a level or anything on it and
// the camera flies in through the cut. Inside a level, drag to look around and use the arrow
// keys to walk from object to object. Esc goes back up one level. A project or book opens as
// a card that grows out of its lightbox, and the train comes in behind it.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { projects } from "@/data/projects";
import { favoriteBooks, writing } from "@/data/library";
import { site } from "@/data/site";
import type { Layout, Mode, Rect } from "./scene";

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
const WAIT = ["Arriving", "2 min", "4 min", "6 min", "9 min", "12 min", "15 min", "Express"];

type Level = "platform" | "mezzanine" | "street";
const LEVELS: { key: Level; name: string; stop: string; blurb: string }[] = [
  { key: "platform", name: "Platform", stop: "title", blurb: "Sign and seven projects" },
  { key: "mezzanine", name: "Mezzanine", stop: "map", blurb: "Line map, arrivals, books, stairs" },
  { key: "street", name: "Street", stop: "street", blurb: "About & contact" },
];
// which level each stop is on (null = the overview)
const LEVEL_OF: Record<string, Level> = { title: "platform", map: "mezzanine", board: "mezzanine", newsstand: "mezzanine", exit: "mezzanine", street: "street" };
const levelOf = (stop: string | null): Level | null => (stop === null ? null : stop.startsWith("project:") ? "platform" : LEVEL_OF[stop] ?? null);
// hotspot id (from layout-dollhouse.json) -> the stop it goes to
const STOP_OF_HOT: Record<string, string> = { "level:platform": "title", "level:mezzanine": "map", "level:street": "street", exit: "street" };
const stopOf = (hot: string) => STOP_OF_HOT[hot] ?? hot;
const LABEL: Record<string, string> = {
  title: "Sophie Shih's sign", map: "Line map", board: "Arrivals board", newsstand: "Books & Writing",
  exit: "Stairs up to the street", street: "About & contact", "level:platform": "Platform", "level:mezzanine": "Mezzanine", "level:street": "Street",
};
const CAPTION: Record<string, string> = {
  title: "The train is in the tunnel. Pick a project tile to see it.",
  map: "Choose a line: each one groups projects by what they're about.",
  board: "Every project is a train. Pick one from the board.",
  newsstand: "Favorite books and things I've written.",
  exit: "Up the stairs: who I am and how to reach me.",
  street: "About me and how to reach me.",
};

type CardState = { kind: "project" | "books" | "about"; projectId?: string; hot: string; rect: Rect; phase: "opening" | "open" | "closing" };

function Bullet({ id, size = 28 }: { id: string; size?: number }) {
  const [l, c] = BULLET[id] ?? ["S", "#e8732c"];
  return <span className="sw-bullet" style={{ background: c, width: size, height: size, fontSize: size * 0.55 }} aria-hidden="true">{l}</span>;
}

const titleOf = (id: string) => (id === "reading" ? "Books & Writing" : projects.find((p) => p.id === id)?.title ?? id);
const labelOf = (hot: string) => (hot.startsWith("project:") ? titleOf(hot.slice(8)) : LABEL[hot] ?? hot);
const hashOf = (stop: string) => (stop.startsWith("project:") ? stop.slice(8) : stop === "newsstand" ? "books" : stop === "street" ? "about" : stop);

export default function Experience() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sceneRef = useRef<import("./scene").DollhouseScene | null>(null);
  const layoutRef = useRef<Layout | null>(null);
  const stopRef = useRef<string | null>(null);
  const busyRef = useRef(false);
  const cardRef = useRef<CardState | null>(null);
  const downRef = useRef<{ x: number; y: number; lx: number; ly: number; moved: boolean } | null>(null);
  const cardEl = useRef<HTMLElement>(null);

  const [progress, setProgress] = useState(0);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const [stop, setStop] = useState<string | null>(null);
  const [card, setCardState] = useState<CardState | null>(null);
  const [listOpen, setListOpen] = useState(false);
  const [filter, setFilter] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [trainMoving, setTrainMoving] = useState(false);
  const [busy, setBusy] = useState(false);

  const setCard = useCallback((c: CardState | null) => {
    cardRef.current = c;
    setCardState(c);
  }, []);

  const project = card?.kind === "project" ? projects.find((p) => p.id === card.projectId) : undefined;
  const level = levelOf(stop);

  // ------------------------------------------------------------ the card (case study, books, about)
  const closeCard = useCallback(async () => {
    const s = sceneRef.current, c = cardRef.current, L = layoutRef.current;
    if (!s || !c || !L) return;
    if (c.kind === "project") {
      setTrainMoving(false);
      void s.trainTo(L.train.parkY, 1.2);
    }
    const rect = s.screenRect(c.hot) ?? c.rect;
    setCard({ ...c, rect, phase: "closing" });
    await new Promise((r) => setTimeout(r, s.reduced ? 0 : 650));
    setCard(null);
  }, [setCard]);

  const openCard = useCallback((kind: "project" | "books" | "about", projectId?: string) => {
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L) return;
    const hot = kind === "project" ? "project:" + projectId : kind === "books" ? "newsstand" : "street";
    const rect = s.screenRect(hot) ?? { left: window.innerWidth / 2 - 60, top: window.innerHeight / 2 - 60, width: 120, height: 120 };
    setCard({ kind, projectId, hot, rect, phase: "opening" });
    if (kind === "project") {
      setTrainMoving(true);
      void s.trainTo(L.train.stopY, 2.0).then(() => setTrainMoving(false));
    }
  }, [setCard]);

  // the card grows out of its lightbox (FLIP), and shrinks back into it on close
  useLayoutEffect(() => {
    const el = cardEl.current;
    if (!el || !card) return;
    const s = sceneRef.current;
    if (card.phase === "opening") {
      el.style.transition = "none";
      el.style.transform = "translate(-50%, -50%)";
      el.style.opacity = "1";
      const fin = el.getBoundingClientRect();
      if (s?.reduced) {
        setCard({ ...card, phase: "open" });
        return;
      }
      const f = card.rect;
      const dx = f.left + f.width / 2 - (fin.left + fin.width / 2);
      const dy = f.top + f.height / 2 - (fin.top + fin.height / 2);
      el.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(${f.width / fin.width}, ${f.height / fin.height}) perspective(900px) rotateY(-14deg)`;
      el.style.opacity = "0.3";
      void el.offsetHeight;
      el.style.transition = "transform .9s cubic-bezier(.2,.8,.2,1), opacity .5s";
      el.style.transform = "translate(-50%, -50%) perspective(900px) rotateY(0deg)";
      el.style.opacity = "1";
      const t = setTimeout(() => {
        if (cardRef.current?.phase === "opening") setCard({ ...cardRef.current, phase: "open" });
      }, 900);
      return () => clearTimeout(t);
    }
    if (card.phase === "closing") {
      const cur = el.getBoundingClientRect();
      const f = card.rect;
      const dx = f.left + f.width / 2 - (cur.left + cur.width / 2);
      const dy = f.top + f.height / 2 - (cur.top + cur.height / 2);
      el.style.transition = "transform .6s cubic-bezier(.4,0,.2,1), opacity .5s";
      el.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(${f.width / cur.width}, ${f.height / cur.height})`;
      el.style.opacity = "0";
    }
  }, [card?.phase, card?.hot]); // eslint-disable-line react-hooks/exhaustive-deps

  // ------------------------------------------------------------ moving between stops
  const goOverview = useCallback(async () => {
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L || busyRef.current) return;
    busyRef.current = true; setBusy(true);
    try {
      if (cardRef.current) await closeCard();
      s.setFourthWall(false);
      s.setActiveLevel(null);
      await s.fly(L.stops.overview, "overview" as Mode);
      stopRef.current = null; setStop(null);
      if (typeof history !== "undefined") history.replaceState(null, "", location.pathname);
    } finally {
      busyRef.current = false; setBusy(false);
    }
  }, [closeCard]);

  const go = useCallback(async (target: string) => {
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L || busyRef.current || !L.stops[target]) return;
    busyRef.current = true; setBusy(true);
    try {
      if (cardRef.current) await closeCard();
      const from = stopRef.current;
      const fromLevel = levelOf(from), toLevel = levelOf(target);
      if (from !== null && fromLevel !== toLevel) {
        // leave the level through the open cut
        s.setFourthWall(false);
        s.setActiveLevel(null);
        await s.fly(L.stops.overview, "overview" as Mode);
        stopRef.current = null; setStop(null);
      }
      const dest = L.stops[target];
      const entering = toLevel !== null && (stopRef.current === null || levelOf(stopRef.current) !== toLevel);
      // coming from outside the cut: pass the waypoint just outside the wall, at eye height
      const via = entering ? [[-14, dest.pos[1], dest.pos[2]]] : [];
      await s.fly(dest, "inside" as Mode, via);
      s.setActiveLevel(toLevel);
      s.setFourthWall(toLevel === "platform" || toLevel === "mezzanine");
      stopRef.current = target; setStop(target);
      setListOpen(false);
      if (typeof history !== "undefined") history.replaceState(null, "", "#" + hashOf(target));
      if (target.startsWith("project:")) openCard("project", target.slice(8));
      else if (target === "newsstand") openCard("books");
      else if (target === "street") openCard("about");
    } finally {
      busyRef.current = false; setBusy(false);
    }
  }, [closeCard, openCard]);

  const walk = useCallback((dir: 1 | -1) => {
    const L = layoutRef.current;
    const cur = stopRef.current;
    const lv = levelOf(cur);
    if (!L || !cur || !lv) return;
    const list = L.walk[lv] ?? [];
    const next = list[list.indexOf(cur) + dir];
    if (next) void go(next);
  }, [go]);

  const skipTrain = () => {
    const L = layoutRef.current;
    if (L) void sceneRef.current?.trainTo(L.train.stopY, 0);
    setTrainMoving(false);
  };

  // ------------------------------------------------------------ load the scene
  useEffect(() => {
    let disposed = false;
    (async () => {
      try {
        const [{ DollhouseScene }, layout] = await Promise.all([
          import("./scene"),
          fetch(BASE + "/layout-dollhouse.json").then((r) => r.json() as Promise<Layout>),
        ]);
        if (disposed || !canvasRef.current) return;
        layoutRef.current = layout;
        const s = new DollhouseScene(canvasRef.current, layout);
        s.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        sceneRef.current = s;
        s.resize();
        s.start();
        await s.load(BASE, setProgress);
        if (disposed) return;
        setReady(true);
        // deep links: #folio goes straight to that project, #about to the street
        const hash = location.hash.slice(1);
        const target = PROJECT_IDS.includes(hash) ? "project:" + hash
          : hash === "about" ? "street"
          : hash === "books" || hash === "reading" ? "newsstand"
          : ["title", "map", "board", "exit"].includes(hash) ? hash : null;
        if (target) setTimeout(() => void go(target), 400);
      } catch (e) {
        console.error(e);
        setFailed(true);
      }
    })();
    const onResize = () => sceneRef.current?.resize();
    window.addEventListener("resize", onResize);
    return () => { disposed = true; window.removeEventListener("resize", onResize); sceneRef.current?.dispose(); };
  }, [go]);

  // line filter: dim the project tiles that are not on the chosen line
  useEffect(() => {
    const line = LINES.find((l) => l.key === filter);
    sceneRef.current?.setDim(line ? line.stops : null);
  }, [filter, ready]);

  // keyboard: arrows walk, Esc goes up one level
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.closest?.("input,textarea")) return;
      if (e.key === "Escape") {
        if (cardRef.current) void closeCard();
        else if (listOpen) setListOpen(false);
        else if (stopRef.current) void goOverview();
      }
      if (stopRef.current && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
        e.preventDefault();
        walk(e.key === "ArrowRight" ? 1 : -1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [closeCard, goOverview, walk, listOpen]);

  // ------------------------------------------------------------ pointer: hover, drag, click
  const onPointerDown = (e: React.PointerEvent) => {
    downRef.current = { x: e.clientX, y: e.clientY, lx: e.clientX, ly: e.clientY, moved: false };
  };
  const onPointerMove = (e: React.PointerEvent) => {
    const s = sceneRef.current;
    if (!s) return;
    const d = downRef.current;
    if (d) {
      if (Math.abs(e.clientX - d.x) + Math.abs(e.clientY - d.y) > 6) d.moved = true;
      s.drag(e.clientX - d.lx, e.clientY - d.ly);
      d.lx = e.clientX;
      d.ly = e.clientY;
      return;
    }
    s.setPointer((e.clientX / window.innerWidth) * 2 - 1, -((e.clientY / window.innerHeight) * 2 - 1));
    const id = s.pick(e.clientX, e.clientY);
    s.setHover(id);
    setHover(id);
  };
  const onPointerUp = (e: React.PointerEvent) => {
    const d = downRef.current;
    downRef.current = null;
    if (!d || d.moved) return;
    const s = sceneRef.current;
    const id = s?.pick(e.clientX, e.clientY);
    if (id) void go(stopOf(id));
  };
  const onWheel = (e: React.WheelEvent) => sceneRef.current?.zoomBy(e.deltaY);

  // ------------------------------------------------------------ derived lists
  const hoverLabel = hover && !busy ? labelOf(hover) : null;
  const walkList = useMemo(() => (level && layoutRef.current ? layoutRef.current.walk[level] ?? [] : []), [level, ready]); // eslint-disable-line react-hooks/exhaustive-deps
  const posInWalk = stop ? walkList.indexOf(stop) : -1;
  const prevStop = posInWalk > 0 ? walkList[posInWalk - 1] : null;
  const nextStop = posInWalk >= 0 && posInWalk < walkList.length - 1 ? walkList[posInWalk + 1] : null;

  return (
    <div className={"sw-root" + (hover ? " sw-hovering" : "")}>
      <canvas ref={canvasRef} className="sw-canvas" role="img"
        aria-label="A cutaway subway station with three levels. Use the menus to move around."
        onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp}
        onPointerLeave={() => { downRef.current = null; sceneRef.current?.setHover(null); setHover(null); }}
        onWheel={onWheel} />

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
        <button className="sw-name" onClick={() => void goOverview()}><Bullet id="purchase-intent" size={22} /> SOPHIE SHIH</button>
        <nav aria-label="Levels">
          {LEVELS.map((l) => (
            <button key={l.key} onClick={() => void go(l.stop)} aria-current={level === l.key}>{l.name}</button>
          ))}
          <button className="sw-all" onClick={() => setListOpen((v) => !v)} aria-expanded={listOpen}>All stops</button>
        </nav>
      </header>

      {hoverLabel && <div className="sw-tip" aria-hidden="true">{hoverLabel} →</div>}

      {/* Overview: every level and object, plus the line filter */}
      {ready && stop === null && !card && (
        <aside className="sw-panel sw-overview" aria-label="The station">
          <p className="sw-eyebrow">THE STATION, CUT OPEN</p>
          <p className="sw-lede">Click a level or anything on it. The camera flies in through the cut. Inside, drag to look around and use the arrow keys to walk.</p>
          {LEVELS.map((l) => (
            <div key={l.key} className="sw-level">
              <button className="sw-level-head" onClick={() => void go(l.stop)}>{l.name} <span>{l.blurb}</span></button>
              <div className="sw-objs">
                {(l.key === "platform" ? ["title", ...PROJECT_IDS.map((id) => "project:" + id)]
                  : l.key === "mezzanine" ? ["map", "board", "newsstand", "exit"] : ["street"]).map((id) => (
                  <button key={id} onClick={() => void go(id)}>
                    {id.startsWith("project:") ? <Bullet id={id.slice(8)} size={18} /> : null}
                    {labelOf(id)}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <p className="sw-eyebrow" style={{ marginTop: 14 }}>LINES</p>
          <div className="sw-chips">
            {LINES.map((l) => (
              <button key={l.key} className={"sw-chip" + (filter === l.key ? " on" : "")} onClick={() => setFilter(filter === l.key ? null : l.key)}
                aria-pressed={filter === l.key}>
                <span className="sw-bullet" style={{ background: l.color, width: 18, height: 18, fontSize: 10 }}>{l.letter}</span> {l.name}
              </button>
            ))}
          </div>
          {filter && <p className="sw-hint">Dimmed: projects that aren&apos;t on the {LINES.find((l) => l.key === filter)?.name.toLowerCase()}.</p>}
        </aside>
      )}

      {/* Title stop: the intro */}
      {ready && stop === "title" && (
        <div className="sw-hero">
          <p className="sw-eyebrow">NOW ARRIVING</p>
          <h1>Sophie Shih</h1>
          <p>{site.lede}</p>
          <div className="sw-row">
            <button className="sw-btn" onClick={() => void go("project:" + PROJECT_IDS[0])}>Start with a project →</button>
            <button className="sw-btn ghost" onClick={() => setListOpen(true)}>See every stop</button>
          </div>
        </div>
      )}

      {/* Mezzanine: the line map as a menu */}
      {ready && stop === "map" && (
        <aside className="sw-panel">
          <p className="sw-eyebrow">CHOOSE YOUR LINE</p>
          {LINES.map((l) => (
            <div key={l.key} className="sw-line">
              <div className="sw-line-head"><span className="sw-bullet" style={{ background: l.color }}>{l.letter}</span> {l.name}</div>
              <ol className="sw-stops" style={{ borderColor: l.color }}>
                {l.stops.map((id) => (
                  <li key={id}><button onClick={() => void go(id === "reading" ? "newsstand" : "project:" + id)}>{titleOf(id)}</button></li>
                ))}
              </ol>
            </div>
          ))}
        </aside>
      )}

      {/* Mezzanine: the arrivals board as a menu */}
      {ready && stop === "board" && (
        <aside className="sw-panel sw-board">
          <p className="sw-eyebrow">NEXT TRAINS</p>
          {[...PROJECT_IDS, "reading"].map((id, i) => (
            <button key={id} className="sw-board-row" onClick={() => void go(id === "reading" ? "newsstand" : "project:" + id)}>
              <Bullet id={id} size={24} /> <span>{titleOf(id)}</span>
              <em>{WAIT[i]}</em>
            </button>
          ))}
        </aside>
      )}

      {/* Stairs: a view up toward the street */}
      {ready && stop === "exit" && (
        <div className="sw-caption">
          <p className="sw-eyebrow">UP THE STAIRS</p>
          <p>{CAPTION.exit}</p>
          <div className="sw-row"><button className="sw-btn" onClick={() => void go("street")}>Go up to the street →</button></div>
        </div>
      )}

      {/* Inside a level: where you are, and the walk controls */}
      {ready && stop !== null && stop !== "title" && stop !== "map" && stop !== "board" && stop !== "exit" && !card && (
        <div className="sw-caption">
          <p className="sw-eyebrow">{stop.startsWith("project:") ? "THIS STOP" : "NOW AT"}</p>
          <p>{stop.startsWith("project:") ? projects.find((p) => p.id === stop.slice(8))?.summary.split(".")[0] + "." : CAPTION[stop] ?? ""}</p>
        </div>
      )}
      {ready && stop !== null && (
        <div className="sw-walk" role="group" aria-label="Walk along this level">
          <button className="sw-btn ghost" onClick={() => prevStop && void go(prevStop)} disabled={!prevStop || busy} aria-label="Previous stop">←</button>
          <button className="sw-btn ghost" onClick={() => void goOverview()} disabled={busy}>Overview</button>
          <button className="sw-btn ghost" onClick={() => nextStop && void go(nextStop)} disabled={!nextStop || busy} aria-label="Next stop">→</button>
        </div>
      )}

      {/* The opened card: a case study, the books, or about */}
      {ready && card && (
        <>
          <div className={"sw-dim" + (card.phase !== "closing" ? " on" : "")} onClick={() => void closeCard()} aria-hidden="true" />
          <article ref={cardEl} className="sw-card" role="dialog" aria-modal="true"
            aria-label={card.kind === "project" ? project?.title : card.kind === "books" ? "Books & Writing" : "About & contact"}
            style={{ left: "50%", top: "50%", transform: "translate(-50%, -50%)" }}>
            <button className="sw-card-close" onClick={() => void closeCard()} aria-label="Close">✕</button>
            {card.kind === "project" && project && (
              <>
                <div className="sw-ptitle"><Bullet id={project.id} size={34} /><div><p className="sw-eyebrow">{project.year} · {project.context}</p><h2>{project.title}</h2></div></div>
                {project.image && <img src={project.image} alt="" className="sw-pimg" />}
                <p>{project.summary}</p>
                <ul>{project.highlights.map((h) => <li key={h}>{h}</li>)}</ul>
                <p className="sw-tech">{project.tech}</p>
                <div className="sw-row">{project.links.map((l) => <a key={l.href} className="sw-btn" href={l.href} target="_blank" rel="noopener">{l.label} ↗</a>)}</div>
              </>
            )}
            {card.kind === "books" && (
              <>
                <p className="sw-eyebrow">ON THE SHELF</p>
                <div className="sw-covers">{favoriteBooks.map((b) => <figure key={b.title}><img src={b.cover} alt={`${b.title} by ${b.author}`} /><figcaption>{b.title}</figcaption></figure>)}</div>
                <p className="sw-eyebrow" style={{ marginTop: 18 }}>WRITTEN BY ME</p>
                <ul className="sw-writing">{writing.map((w) => <li key={w.href}><a href={w.href} target="_blank" rel="noopener">{w.title}</a><span>{w.meta}</span></li>)}</ul>
              </>
            )}
            {card.kind === "about" && (
              <>
                <div className="sw-about"><img src={site.headshot} alt="Sophie Shih" /><div><p className="sw-eyebrow">STREET LEVEL</p><h2>{site.name}</h2></div></div>
                <p>{site.lede}</p>
                <div className="sw-row">
                  <a className="sw-btn" href={`mailto:${site.email}`}>Email</a>
                  <a className="sw-btn" href={site.linkedin} target="_blank" rel="noopener">LinkedIn ↗</a>
                  <a className="sw-btn" href={site.github} target="_blank" rel="noopener">GitHub ↗</a>
                  <a className="sw-btn" href={site.resume} target="_blank" rel="noopener">Résumé ↗</a>
                </div>
              </>
            )}
            {trainMoving && <button className="sw-skip" onClick={skipTrain}>Skip the train</button>}
          </article>
        </>
      )}

      {(listOpen || failed) && (
        <div className="sw-list" role="dialog" aria-label="All stops">
          <div className="sw-list-inner">
            <div className="sw-list-head"><h2>All stops</h2>{!failed && <button onClick={() => setListOpen(false)} aria-label="Close">✕</button>}</div>
            <ol>
              {projects.filter((p) => !p.isReadingShelf).map((p) => (
                <li key={p.id}>
                  {failed ? <a href={p.links[0]?.href}><Bullet id={p.id} size={24} /> {p.title}</a>
                    : <button onClick={() => void go("project:" + p.id)}><Bullet id={p.id} size={24} /> <span>{p.title}</span><em>{p.summary}</em></button>}
                </li>
              ))}
              <li><button onClick={() => void go("newsstand")}><Bullet id="reading" size={24} /> <span>Books &amp; Writing</span><em>Favorite books and my essays.</em></button></li>
              <li><button onClick={() => void go("street")}><span className="sw-bullet" style={{ background: "#2a2219" }}>↑</span> <span>About &amp; contact</span><em>{site.email}</em></button></li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}

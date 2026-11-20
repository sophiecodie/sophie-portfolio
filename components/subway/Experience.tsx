"use client";
// The subway portfolio, as a dollhouse. The station is cut open into three levels (street,
// mezzanine, platform) that are all on screen at once. Click a level or anything on it and
// the camera flies in through the cut. Inside a level, drag to look around and use the arrow
// keys to walk from object to object. Esc goes back up one level. A project or book opens as
// a card that grows out of its lightbox, and the train comes in behind it.
// The visit opens on the platform as the train pulls in, like the original ride-through.
// Cards are styled as MTA station signs: black panel, white rule, Libre Franklin, numbered
// route bullets, and an LED strip in Subway Ticker that types itself out.
import StreetMoodToggle from "../street/StreetMoodToggle";
import Newspaper, { newspaperClass } from "../posters/Newspaper";
import { AllStops, Arrivals, LineMap, Wayfinder } from "./Boards";
import { PosterPointers, ScrollCue, StepArrows } from "./Hints";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { projects } from "@/data/projects";
import { favoriteBooks, writing } from "@/data/library";
import { site } from "@/data/site";
import type { Layout, Mode, Rect } from "./scene";

const BASE = "/subway";
// MTA trunk colors: like the real system, a line's projects share its color and each has its
// own number. Numbers follow the order of the tiles on the platform.
// Data = red (like the 1 2 3), Words = purple (like the 7), Health = green (like the 4 5 6).
const RED = "#ee352e", GREEN = "#00933c", PURPLE = "#b933ad", YELLOW = "#fccc0a";
const LINES = [
  { key: "data", name: "Data line", letter: "D", color: RED, stops: ["college-app-atlas", "purchase-intent", "new-york-census"], about: "Data, cities and prediction" },
  { key: "health", name: "Health line", letter: "H", color: GREEN, stops: ["agent00hl7", "dream-team", "neurobiome"], about: "AI for medicine and patients" },
  { key: "words", name: "Words line", letter: "W", color: PURPLE, stops: ["folio", "reading"], about: "Reading, writing and literature" },
];
// [label, background, text color]
const BULLET: Record<string, [string, string, string?]> = {
  "college-app-atlas": ["1", RED], "purchase-intent": ["2", RED], "new-york-census": ["3", RED],
  folio: ["4", PURPLE], agent00hl7: ["5", GREEN], "dream-team": ["6", GREEN], neurobiome: ["7", GREEN],
  reading: ["W", YELLOW, "#111"],
};
const lineOf = (id: string) => LINES.find((l) => l.stops.includes(id));
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
const STOP_OF_HOT: Record<string, string> = { "level:platform": "title", "level:mezzanine": "map", "level:street": "street", exit: "street", stairs_down: "title", entrance: "exit" };
const stopOf = (hot: string) => STOP_OF_HOT[hot] ?? hot;
const LABEL: Record<string, string> = {
  title: "Sophie Shih's sign", map: "Line map", board: "Arrivals kiosk", newsstand: "Books & Writing",
  exit: "Stairs up to the street", stairs_down: "Stairs down to the platform", entrance: "Subway entrance", street: "About & contact", "level:platform": "Platform", "level:mezzanine": "Mezzanine", "level:street": "Street",
};
// what the typed line at the bottom left says at each stop
const CAPTION: Record<string, string> = {
  title: "Projects are the posters on the wall. Click one",
  map: "Choose a line. Each one groups projects by what they're about",
  board: "Every project is a train. Pick one from the board",
  newsstand: "Favorite books and things I've written",
  exit: "Up the stairs: who I am and how to reach me",
  street: "About me and how to reach me",
};
// After "Enter station", the camera turns from the arriving train to the poster wall, so the
// first thing you see is the projects (the opening shot itself stays on the train).
const POSTER_VIEW = { pos: [2.05, 6.8, 1.6], look: [4.9, 12.0, 1.8], fov: 58 };
const WHERE: Record<string, string> = { title: "Platform", map: "Mezzanine · Line map", board: "Mezzanine · Arrivals", newsstand: "Mezzanine · Newsstand", exit: "Mezzanine · Exit", street: "Street" };
const bulletOf = (id: string): [string, string, string?] => BULLET[id] ?? ["S", "#808183"];

type CardState = { kind: "project" | "books" | "about"; projectId?: string; hot: string; rect: Rect; phase: "opening" | "open" | "closing" };

function Bullet({ id, size = 28 }: { id: string; size?: number }) {
  const [l, c, ink] = BULLET[id] ?? ["S", "#808183"];
  return <span className="sw-bullet" style={{ background: c, color: ink ?? "#fff", width: size, height: size, fontSize: size * 0.62 }} aria-hidden="true">{l}</span>;
}

/** An LED strip line that types itself out, then leaves a blinking block cursor. */
function Ticker({ text, delay = 250, speed = 40 }: { text: string; delay?: number; speed?: number }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setN(text.length);
      return;
    }
    setN(0);
    let i = 0, iv = 0;
    const t = window.setTimeout(() => {
      iv = window.setInterval(() => {
        i += 1;
        setN(i);
        if (i >= text.length) window.clearInterval(iv);
      }, speed);
    }, delay);
    return () => { window.clearTimeout(t); window.clearInterval(iv); };
  }, [text, delay, speed]);
  return (
    <div className="sw-ticker" role="text" aria-label={text}>
      <span aria-hidden="true">{text.slice(0, n)}</span>
      <span className={"sw-caret" + (n >= text.length ? " done" : "")} aria-hidden="true" />
    </div>
  );
}

const titleOf = (id: string) => (id === "reading" ? "Books & Writing" : projects.find((p) => p.id === id)?.title ?? id);
const labelOf = (hot: string) => (hot.startsWith("project:") ? titleOf(hot.slice(8)) : LABEL[hot] ?? hot);
// what a Street View-style arrow says it leads to
const stepOf = (stop: string) => stop.startsWith("project:")
  ? { id: stop, label: titleOf(stop.slice(8)), bullet: stop.slice(8) }
  : { id: stop, label: stop === "title" ? "Start of the platform" : LABEL[stop] ?? stop };
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
  const [arriving, setArriving] = useState(false);
  // the welcome sign on the platform; it can be closed, and clicking the sign brings it back
  const [welcome, setWelcome] = useState(false);
  // overview: where each floor's label sits (client px) and how far along the track we are
  const [floorY, setFloorY] = useState<Record<string, number>>({});
  const [pan, setPan] = useState({ k: 0, lo: true, hi: true });

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
    // the train stays at the platform after a card closes
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
  }, [setCard]);

  /**
   * A project's train: whatever train is in pulls out, then one in the project's line color
   * with its route bullet pulls in and stops with its front just past the project's tile.
   */
  const bringTrain = useCallback(async (pid: string) => {
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L) return;
    const y = L.projectY0 + PROJECT_IDS.indexOf(pid) * L.projectStep - (L.train.ahead ?? 2.6);
    const [label, color] = BULLET[pid] ?? ["S", "#808183"];
    if (s.trainLine === label && s.trainAt(y)) return;
    setTrainMoving(true);
    await s.depart(1.4);
    s.setTrainLine(color, label);
    await s.arriveAt(y, 3.2);
    setTrainMoving(false);
  }, []);

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
      // come back out where you were (from the opening, the overview starts at the far end)
      const here = stopRef.current && stopRef.current !== "title" ? L.stops[stopRef.current]?.look[1] : undefined;
      await s.fly(s.overviewStop(here), "overview" as Mode);
      stopRef.current = null; setStop(null);
      if (typeof history !== "undefined") history.replaceState(null, "", location.pathname);
    } finally {
      busyRef.current = false; setBusy(false);
    }
  }, [closeCard]);

  /** Go to a stop. card: open its card (a project, the books, About) when you get there. */
  const go = useCallback(async (target: string, card = true) => {
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L || busyRef.current || !L.stops[target]) return;
    busyRef.current = true; setBusy(true);
    setListOpen(false);
    try {
      if (cardRef.current) await closeCard();
      const from = stopRef.current;
      const fromLevel = levelOf(from), toLevel = levelOf(target);
      if (from !== null && fromLevel !== toLevel) {
        // leave the level through the open cut
        s.setFourthWall(false);
        s.setActiveLevel(null);
        await s.fly(s.overviewStop(L.stops[target].look[1]), "overview" as Mode);
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
      if (typeof history !== "undefined") history.replaceState(null, "", "#" + hashOf(target));
      if (target.startsWith("project:")) {
        // the card opens right away while the project's train rolls in behind it
        const pid = target.slice(8);
        const train = bringTrain(pid);
        openCard("project", pid);
        await train;
      } else if (target === "newsstand") openCard("books");
      else if (target === "street" && card) openCard("about");
    } finally {
      busyRef.current = false; setBusy(false);
    }
  }, [closeCard, openCard, bringTrain]);

  const walk = useCallback((dir: 1 | -1) => {
    const L = layoutRef.current;
    const cur = stopRef.current;
    const lv = levelOf(cur);
    if (!L || !cur || !lv) return;
    const list = L.walk[lv] ?? [];
    const next = list[list.indexOf(cur) + dir];
    if (next) void go(next);
  }, [go]);

  /** Close the welcome sign and turn to face the project posters. */
  const enterStation = useCallback(async () => {
    setWelcome(false);
    const s = sceneRef.current, L = layoutRef.current;
    if (!s || !L || busyRef.current || stopRef.current !== "title") return;
    busyRef.current = true; setBusy(true);
    try {
      // swing out over the platform edge first, clear of the column line
      await s.fly(L.stops.title, "inside" as Mode, [[1.55, 3.6, 1.6]]);
      s.setActiveLevel("platform");
    } finally {
      busyRef.current = false; setBusy(false);
    }
  }, []);

  const skipTrain = (): void => {
    sceneRef.current?.finishTrain();
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
        // the NYC street behind the top floor (photo + depth parallax, sunny/rainy)
        void import("../street/streetBackdrop").then(({ attachStreetBackdrop }) => { if (!disposed) attachStreetBackdrop(s, layout); });
        // ad posters hung over the platform lightboxes
        void import("../posters/posterWall").then(({ attachPosters }) => { if (!disposed) attachPosters(s, layout); });
        await s.load(BASE, setProgress);
        if (disposed) return;
        setReady(true);
        // deep links: #folio goes straight to that project, #about to the street
        const hash = location.hash.slice(1);
        const target = PROJECT_IDS.includes(hash) ? "project:" + hash
          : hash === "about" ? "street"
          : hash === "books" || hash === "reading" ? "newsstand"
          : ["title", "map", "board", "exit"].includes(hash) ? hash : null;
        if (target) {
          layout.stops.title = POSTER_VIEW;
          setTimeout(() => void go(target), 400);
        }
        else {
          // the opening: stand on the platform by the title sign while the train pulls in
          s.jump("title", "inside" as Mode);
          // from now on the platform's first stop faces the posters
          layout.stops.title = POSTER_VIEW;
          s.setActiveLevel("platform");
          s.setFourthWall(true, true);
          setWelcome(true);
          stopRef.current = "title";
          setStop("title");
          setArriving(true);
          void s.arrive(6).then(() => setArriving(false));
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

  // overview: keep the floor labels on their floors and the position bar in step with the pan
  useEffect(() => {
    if (!ready || stop !== null) return;
    let raf = 0;
    const tick = () => {
      raf = requestAnimationFrame(tick);
      const s = sceneRef.current, L = layoutRef.current;
      if (!s || !L) return;
      const r = s.panRange();
      const lv = L.levels;
      // each floor's sign hangs just under that floor's ceiling, small, so it covers as little as possible
      const top = (z: number) => Math.max(s.toScreen([-6, r.at, z]).y, 58) + 10;
      const next = {
        street: top(lv.street.floor + 30),
        mezzanine: top(lv.mezzanine.ceiling ?? lv.mezzanine.floor + 3.6),
        platform: top(lv.platform.ceiling ?? 4),
      };
      setFloorY((o) => (Object.keys(next).some((k) => Math.abs((o[k] ?? 0) - next[k as Level]) > 0.5) ? next : o));
      const k = r.hi > r.lo ? (r.at - r.lo) / (r.hi - r.lo) : 0.5;
      setPan((o) => (Math.abs(o.k - k) > 0.002 || o.lo !== r.at <= r.lo + 0.01 || o.hi !== r.at >= r.hi - 0.01
        ? { k, lo: r.at <= r.lo + 0.01, hi: r.at >= r.hi - 0.01 } : o));
    };
    tick();
    return () => cancelAnimationFrame(raf);
  }, [ready, stop]);

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
        else if (welcome && stopRef.current === "title") void enterStation();
        else if (stopRef.current) void goOverview();
      }
      // inside a floor, up/down (or W/S) walk the way you are facing
      if (stopRef.current && !cardRef.current && !busyRef.current && ["ArrowUp", "ArrowDown", "w", "s", "W", "S"].includes(e.key)) {
        e.preventDefault();
        sceneRef.current?.walkBy(e.key === "ArrowUp" || e.key.toLowerCase() === "w" ? 0.8 : -0.8);
      }
      if (stopRef.current && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
        e.preventDefault();
        walk(e.key === "ArrowRight" ? 1 : -1);
      } else if (!stopRef.current && !cardRef.current && (e.key === "ArrowRight" || e.key === "ArrowLeft")) {
        e.preventDefault();
        // screen left is further along the line
        sceneRef.current?.panBy(e.key === "ArrowLeft" ? 6 : -6);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [closeCard, goOverview, walk, listOpen, welcome, enterStation]);

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
      s.drag(e.clientX - d.lx, e.clientY - d.ly, e.pointerType === "touch");
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
    // a whole level or the stairs up just take you there; an object also opens its card
    if (id === "title") setWelcome(true);
    if (id) void go(stopOf(id), !id.startsWith("level:") && id !== "exit");
  };
  const onWheel = (e: React.WheelEvent) => sceneRef.current?.zoomBy(e.deltaY - e.deltaX);

  // ------------------------------------------------------------ derived lists
  const hoverLabel = hover && !busy ? labelOf(hover) : null;
  const walkList = useMemo(() => (level && layoutRef.current ? layoutRef.current.walk[level] ?? [] : []), [level, ready]); // eslint-disable-line react-hooks/exhaustive-deps
  const posInWalk = stop ? walkList.indexOf(stop) : -1;
  const prevStop = posInWalk > 0 ? walkList[posInWalk - 1] : null;
  const nextStop = posInWalk >= 0 && posInWalk < walkList.length - 1 ? walkList[posInWalk + 1] : null;

  const goId = useCallback((id: string) => void go(id === "reading" ? "newsstand" : "project:" + id), [go]);

  // touch screens get their own walk hint
  const [touch, setTouch] = useState(false);
  useEffect(() => setTouch(window.matchMedia("(hover: none)").matches), []);

  // the typed line at the bottom left (replaces the old caption boxes, hover pill and walk hint)
  const say = useMemo(() => {
    if (!ready || card || listOpen || failed) return null;
    if (stop === "title" && welcome) return null;
    // flying between stops: stay quiet until we land (the train is the exception)
    if (busy && !trainMoving) return null;
    // next/previous stop now live in the Street View-style arrows (StepArrows)
    const step = {};
    const walkHint = level !== null ? (touch ? "Drag to look around · drag up to walk" : "Drag to look around · scroll or ↑ ↓ to walk · ← → or the arrows for the next stop") : undefined;
    const pid = stop?.startsWith("project:") ? stop.slice(8) : null;
    const where = stop === null ? "Whole station" : pid ? `Platform · Stop ${BULLET[pid]?.[0] ?? ""}` : WHERE[stop] ?? labelOf(stop);
    if (trainMoving) return { where, text: "Train approaching. Please stand back", action: { label: "Skip the train", onClick: skipTrain } };
    if (hoverLabel) return { where, text: "> " + hoverLabel, hint: "Click to go there", ...step };
    if (stop === null) {
      const line = LINES.find((l) => l.key === filter);
      return { where, text: line ? `Showing the ${line.name} only` : "Pick a floor, or drag to slide along the station",
        hint: line ? "Click its bullet in the top bar again to show every line" : "Esc or Station brings you back here" };
    }
    if (pid) return { where, text: titleOf(pid), hint: "Click the poster to open it again · " + (walkHint ?? ""), ...step };
    if (stop === "exit") return { where, text: CAPTION.exit, action: { label: "Go up to the street →", onClick: (): void => { void go("street"); } }, hint: walkHint, ...step };
    return { where, text: CAPTION[stop] ?? labelOf(stop), hint: walkHint, ...step };
  }, [ready, card, listOpen, failed, stop, welcome, busy, level, prevStop, nextStop, touch, trainMoving, hoverLabel, filter, go]); // eslint-disable-line react-hooks/exhaustive-deps


  return (
    <div className={"sw-root" + (hover ? " sw-hovering" : "")}>
      <canvas ref={canvasRef} className="sw-canvas" role="img"
        aria-label="A cutaway subway station with three levels. Use the menus to move around."
        onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp}
        onPointerLeave={() => { downRef.current = null; sceneRef.current?.setHover(null); setHover(null); }}
        onWheel={onWheel} />
      {ready && <StreetMoodToggle />}

      {!ready && !failed && (
        <div className="sw-loading" role="status">
          <div className="sw-loading-sign"><span>Sophie Shih&apos;s Portfolio</span><Bullet id="brand" size={30} /></div>
          <div className="sw-loading-bar"><span style={{ width: `${Math.round(progress * 100)}%` }} /></div>
          <p className="sw-led">TRAIN APPROACHING {Math.round(progress * 100)}%</p>
        </div>
      )}
      {failed && (
        <div className="sw-loading" role="alert">
          <p>The 3D station couldn&apos;t load on this device. Here are all the stops instead.</p>
        </div>
      )}

      <header className="sw-nav">
        <button className="sw-name" onClick={() => void goOverview()} aria-label="Whole station">
          <Bullet id="brand" size={26} /> <span>Sophie Shih</span>
        </button>
        <nav aria-label="Floors">
          <button className="sw-tab" onClick={() => void goOverview()} aria-current={stop === null}>Station</button>
          {[...LEVELS].reverse().map((l) => (
            <button key={l.key} className="sw-tab" onClick={() => void go(l.stop)} aria-current={level === l.key}>
              {l.key === "street" ? "About" : l.key === "mezzanine" ? "Map & books" : "Projects"}
            </button>
          ))}
        </nav>
        <div className="sw-nav-end">
          <div className="sw-nav-lines" role="group" aria-label="Show one line">
            {LINES.map((l) => (
              <button key={l.key} className={filter === l.key ? "on" : ""} onClick={() => setFilter(filter === l.key ? null : l.key)}
                aria-pressed={filter === l.key} title={l.name}>
                <span className="sw-bullet" style={{ background: l.color, width: 24, height: 24, fontSize: 13 }}>{l.letter}</span>
              </button>
            ))}
          </div>
          <button className="sw-all" onClick={() => setListOpen((v) => !v)} aria-expanded={listOpen}>All stops</button>
        </div>
      </header>

      {/* Overview: the three floors fill the screen. Each floor has a sign on the left edge,
          and the bar at the bottom right shows where along the station you are. */}
      {ready && stop === null && !card && (
        <>
          {LEVELS.map((l) => floorY[l.key] !== undefined && (
            <button key={l.key} className="sw-floor" style={{ top: floorY[l.key] }} onClick={() => void go(l.stop, false)}>
              <span className="sw-floor-name">{l.name}</span>
              <span className="sw-floor-blurb">{l.blurb}</span>
            </button>
          ))}
          <div className="sw-pan" role="group" aria-label="Move along the station">
            <button onClick={() => sceneRef.current?.panBy(10)} disabled={pan.hi} aria-label="Further along">◀</button>
            <span className="sw-pan-track"><span style={{ left: `${(1 - pan.k) * 100}%` }} /></span>
            <button onClick={() => sceneRef.current?.panBy(-10)} disabled={pan.lo} aria-label="Back toward the entrance">▶</button>
          </div>
        </>
      )}

      {/* Title stop: the welcome sign. It can be closed (✕, Esc or Enter station) and comes back
          when you click Sophie Shih's sign in the station. */}
      {ready && stop === "title" && welcome && !card && (
        <div className="sw-hero sw-sign" role="dialog" aria-label="Welcome">
          <Ticker text={arriving ? "NOW ARRIVING  SOPHIE SHIH'S PORTFOLIO" : "STAND CLEAR OF THE CLOSING DOORS  PICK A STOP"} delay={arriving ? 400 : 100} />
          <button className="sw-card-close" onClick={() => void enterStation()} aria-label="Close the welcome sign">✕</button>
          <div className="sw-sign-body">
            <h1>Sophie Shih&apos;s<br />Portfolio Station</h1>
            <div className="sw-bullets" role="group" aria-label="Projects">
              {[...PROJECT_IDS, "reading"].map((id) => (
                <button key={id} onClick={() => void go(id === "reading" ? "newsstand" : "project:" + id)} aria-label={titleOf(id)} title={titleOf(id)}>
                  <Bullet id={id} size={40} />
                </button>
              ))}
            </div>
            <p className="sw-desc">{site.lede}</p>
            <div className="sw-row">
              <button className="sw-btn" onClick={() => void enterStation()}>Enter station →</button>
              <button className="sw-btn ghost" onClick={() => setListOpen(true)}>All stops</button>
            </div>
          </div>
        </div>
      )}

      {/* Mezzanine: the line map and the arrivals board as menus */}
      {ready && stop === "map" && !card && (
        <LineMap lines={LINES} bulletOf={bulletOf} filter={filter} setFilter={setFilter} onGo={goId} />
      )}
      {ready && stop === "board" && !card && (
        <Arrivals ids={[...PROJECT_IDS, "reading"]} waits={WAIT} bulletOf={bulletOf} lineOf={lineOf} onGo={goId} />
      )}

      {/* The typed line at the bottom left: where you are, what you're pointing at, what to do */}
      {say && <Wayfinder {...say} />}

      {/* Hints: arrows over the posters at the start of the platform, and Street View-style
          arrows to the next and previous stop on any floor */}
      {ready && stop === "title" && !welcome && !card && !listOpen && !busy && (
        <PosterPointers scene={sceneRef.current} y0={layoutRef.current?.projectY0 ?? 10.6} step={layoutRef.current?.projectStep ?? 3.8} ids={PROJECT_IDS} bulletOf={bulletOf} titleOf={titleOf} onGo={goId} />
      )}
      {ready && level !== null && !card && !listOpen && !(stop === "title" && welcome) && !busy && (
        <div className={stop === "map" || stop === "board" ? "sw-go-wrap on-board" : "sw-go-wrap"}>
          <StepArrows bulletOf={bulletOf} onGo={(id) => void go(id)} pulse={stop === "title"}
            prev={prevStop ? stepOf(prevStop) : null} next={nextStop ? stepOf(nextStop) : null} />
        </div>
      )}

      {/* The opened card: a case study, the books, or about */}
      {ready && card && (
        <>
          <div className={"sw-dim" + (card.phase !== "closing" ? " on" : "")} onClick={() => void closeCard()} aria-hidden="true" />
          {card.kind === "project" && project ? (
          <article ref={cardEl} className={newspaperClass} role="dialog" aria-modal="true" aria-label={project.title}
            style={{ left: "50%", top: "50%", transform: "translate(-50%, -50%)" }}>
            <button className="sw-card-close" onClick={() => void closeCard()} aria-label="Close">✕</button>
            <Newspaper project={project}
              bullet={{ id: project.id, title: project.title, label: BULLET[project.id]?.[0] ?? "S", color: BULLET[project.id]?.[1] ?? "#808183" }}
              lineName={lineOf(project.id)?.name}
              transfers={(lineOf(project.id)?.stops ?? []).filter((id) => id !== project.id).map((id) => ({
                id, title: titleOf(id), label: BULLET[id]?.[0] ?? "S", color: BULLET[id]?.[1] ?? "#808183", ink: BULLET[id]?.[2] }))}
              onTransfer={(id) => void go(id === "reading" ? "newsstand" : "project:" + id)} />
            <ScrollCue label="Keep reading" />
          </article>
          ) : (
          <article ref={cardEl} className="sw-card sw-sign" role="dialog" aria-modal="true"
            aria-label={card.kind === "project" ? project?.title : card.kind === "books" ? "Books & Writing" : "About & contact"}
            style={{ left: "50%", top: "50%", transform: "translate(-50%, -50%)" }}>
            <button className="sw-card-close" onClick={() => void closeCard()} aria-label="Close">✕</button>
            {card.kind === "books" && (
              <>
                <Ticker text="NEWSSTAND  BOOKS & WRITING" delay={450} />
                <div className="sw-sign-body">
                  <div className="sw-sign-head">
                    <Bullet id="reading" size={56} />
                    <div><h2>Books &amp; Writing</h2><p className="sw-sub">Mezzanine newsstand · open late</p></div>
                  </div>
                  <p className="sw-desc">Favorite books and things I&apos;ve written.</p>
                  <p className="sw-label">On the shelf</p>
                  <div className="sw-covers">{favoriteBooks.map((b) => <figure key={b.title}><img src={b.cover} alt={`${b.title} by ${b.author}`} /><figcaption>{b.title}</figcaption></figure>)}</div>
                  <p className="sw-label">Written by me</p>
                  <ul className="sw-writing">{writing.map((w) => <li key={w.href}><a href={w.href} target="_blank" rel="noopener">{w.title} ↗</a><span>{w.meta}</span></li>)}</ul>
                </div>
              </>
            )}
            {card.kind === "about" && (
              <>
                <Ticker text="STREET LEVEL  ABOUT & CONTACT" delay={450} />
                <div className="sw-sign-body">
                  <div className="sw-sign-head sw-about">
                    <img src={site.headshot} alt="Sophie Shih" />
                    <div><h2>{site.name}</h2><p className="sw-sub">Exit to street · all lines</p></div>
                  </div>
                  <p className="sw-desc">{site.lede}</p>
                  <div className="sw-info"><span className="sw-glyph" aria-hidden="true">✉</span><a href={`mailto:${site.email}`}>{site.email}</a></div>
                  <div className="sw-row">
                    <a className="sw-btn" href={`mailto:${site.email}`}>Email</a>
                    <a className="sw-btn" href={site.linkedin} target="_blank" rel="noopener">LinkedIn ↗</a>
                    <a className="sw-btn" href={site.github} target="_blank" rel="noopener">GitHub ↗</a>
                    <a className="sw-btn" href={site.website} target="_blank" rel="noopener">Website ↗</a>
                    <a className="sw-btn" href={site.resume} target="_blank" rel="noopener">Résumé ↗</a>
                  </div>
                </div>
              </>
            )}
            {trainMoving && <button className="sw-skip" onClick={skipTrain}>Skip the train</button>}
            <ScrollCue />
          </article>
          )}
        </>
      )}

      {(listOpen || failed) && (
        <AllStops lines={LINES} bulletOf={bulletOf} onGo={goId} onAbout={() => void go("street")} failed={failed}
          here={stop?.startsWith("project:") ? stop.slice(8) : stop === "newsstand" ? "reading" : null}
          onClose={failed ? undefined : () => setListOpen(false)} />
      )}
    </div>
  );
}

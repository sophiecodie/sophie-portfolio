"use client";
// The station's boards, redesigned (2026-11-17):
//  - Wayfinder: the typed LED line at the bottom left that replaces the pop-up caption boxes.
//  - LineMap: "Choose your line", a strip map per line like the ones over subway car doors.
//  - Arrivals: "Next trains", a countdown clock with a live time and a scrolling service note.
//  - AllStops: the whole station directory, every line as a strip with its posters.
// Plain React + CSS, no extra libraries. Styles are in ./boards.css.
import { useEffect, useState } from "react";
import { projects } from "@/data/projects";
import { site } from "@/data/site";
import "./boards.css";

export type Line = { key: string; name: string; letter: string; color: string; stops: string[]; about: string };
export type BulletOf = (id: string) => [string, string, string?];

const POSTER = (id: string) => `/subway/posters/${id}.jpg`;
const projectOf = (id: string) => projects.find((p) => p.id === id);
const titleOf = (id: string) => (id === "reading" ? "Books & Writing" : projectOf(id)?.title ?? id);
const summaryOf = (id: string) => (id === "reading" ? "Favorite books and things I've written, at the mezzanine newsstand." : projectOf(id)?.summary ?? "");
const yearOf = (id: string) => (id === "reading" ? "Newsstand" : projectOf(id)?.year ?? "");
const shortOf = (id: string) => (id === "reading" ? "Books & Writing" : projectOf(id)?.spine ?? titleOf(id));

function Dot({ id, bulletOf, size = 26 }: { id: string; bulletOf: BulletOf; size?: number }) {
  const [l, c, ink] = bulletOf(id);
  return <span className="sw-bullet" style={{ background: c, color: ink ?? "#fff", width: size, height: size, fontSize: size * 0.62 }} aria-hidden="true">{l}</span>;
}

/** Types `text` out one letter at a time; restarts whenever the text changes. */
export function useTyped(text: string, speed = 28, delay = 120) {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { setN(text.length); return; }
    setN(0);
    let i = 0, iv = 0;
    const t = window.setTimeout(() => {
      iv = window.setInterval(() => { i += 1; setN(i); if (i >= text.length) window.clearInterval(iv); }, speed);
    }, delay);
    return () => { window.clearTimeout(t); window.clearInterval(iv); };
  }, [text, speed, delay]);
  return { shown: text.slice(0, n), done: n >= text.length };
}

// ------------------------------------------------------------------ the typed line, bottom left
export function Wayfinder({ where, text, hint, action, onPrev, onNext }: {
  where: string; // small label above, e.g. "Mezzanine"
  text: string; // the line that types itself out
  hint?: string; // a quiet line under it
  action?: { label: string; onClick: () => void };
  onPrev?: (() => void) | null;
  onNext?: (() => void) | null;
}) {
  const { shown, done } = useTyped(text);
  return (
    <div className="sw-say" role="status" aria-live="polite">
      <div className="sw-say-top">
        {(onPrev !== undefined || onNext !== undefined) && (
          <span className="sw-say-step">
            <button onClick={() => onPrev?.()} disabled={!onPrev} aria-label="Previous stop">‹</button>
            <button onClick={() => onNext?.()} disabled={!onNext} aria-label="Next stop">›</button>
          </span>
        )}
        <span className="sw-say-where">{where}</span>
      </div>
      <p className="sw-say-line" aria-label={text}>
        <span aria-hidden="true">{shown}</span><span className={"sw-caret" + (done ? " done" : "")} aria-hidden="true" />
      </p>
      {(hint || action) && (
        <div className="sw-say-foot">
          {action && <button className="sw-say-act" onClick={action.onClick}>{action.label}</button>}
          {hint && <span className="sw-say-hint">{hint}</span>}
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------------ one line drawn as a strip map
function Strip({ line, bulletOf, onGo, detail = false, here }: {
  line: Line; bulletOf: BulletOf; onGo: (id: string) => void; detail?: boolean; here?: string | null;
}) {
  return (
    <ol className={"sw-strip" + (detail ? " detail" : "")} style={{ ["--line" as string]: line.color }}>
      {line.stops.map((id) => (
        <li key={id} className={here === id ? "here" : ""}>
          <button onClick={() => onGo(id)}>
            <span className="sw-strip-dot" aria-hidden="true" />
            {detail && (id === "reading"
              ? <span className="sw-strip-thumb reading" aria-hidden="true"><Dot id={id} bulletOf={bulletOf} size={30} /></span>
              : <img className="sw-strip-thumb" src={POSTER(id)} alt="" loading="lazy" />)}
            <span className="sw-strip-text">
              <span className="sw-strip-name"><Dot id={id} bulletOf={bulletOf} size={detail ? 22 : 20} /> {titleOf(id)}</span>
              <span className="sw-strip-sum">{detail ? summaryOf(id) : summaryOf(id).split(/[.:]/)[0]}</span>
            </span>
            <span className="sw-strip-go" aria-hidden="true">›</span>
          </button>
        </li>
      ))}
    </ol>
  );
}

// ------------------------------------------------------------------ Choose your line
export function LineMap({ lines, bulletOf, filter, setFilter, onGo }: {
  lines: Line[]; bulletOf: BulletOf; filter: string | null; setFilter: (k: string | null) => void; onGo: (id: string) => void;
}) {
  const count = lines.reduce((n, l) => n + l.stops.length, 0);
  return (
    <aside className="sw-board2 sw-linemap" aria-label="Choose your line">
      <header className="sw-board2-head">
        <h2>Choose your line</h2>
        <p>{lines.length} lines · {count} stops · pick a stop to ride there</p>
      </header>
      <div className="sw-board2-body">
        {lines.map((l) => (
          <section key={l.key} className={"sw-lm-line" + (filter && filter !== l.key ? " faded" : "")}>
            <div className="sw-lm-head">
              <span className="sw-bullet" style={{ background: l.color, width: 38, height: 38, fontSize: 22 }} aria-hidden="true">{l.letter}</span>
              <div className="sw-lm-name"><strong>{l.name}</strong><span>{l.about}</span></div>
              <button className={"sw-lm-only" + (filter === l.key ? " on" : "")} aria-pressed={filter === l.key}
                onClick={() => setFilter(filter === l.key ? null : l.key)}>
                {filter === l.key ? "Showing only" : "Only this line"}
              </button>
            </div>
            <Strip line={l} bulletOf={bulletOf} onGo={onGo} />
          </section>
        ))}
      </div>
    </aside>
  );
}

// ------------------------------------------------------------------ Next trains
const ORD = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"];
export function Arrivals({ ids, waits, bulletOf, lineOf, onGo }: {
  ids: string[]; waits: string[]; bulletOf: BulletOf; lineOf: (id: string) => Line | undefined; onGo: (id: string) => void;
}) {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const iv = window.setInterval(() => setNow(new Date()), 15000);
    return () => window.clearInterval(iv);
  }, []);
  const clock = now ? now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }) : "";
  return (
    <aside className="sw-board2 sw-arrivals" aria-label="Next trains">
      <header className="sw-arr-head">
        <span className="sw-arr-title">NEXT TRAINS</span>
        <span className="sw-arr-clock" aria-label={"Time " + clock}>{clock}</span>
      </header>
      <p className="sw-arr-sub">Mezzanine · all lines · every project is a train</p>
      <ol className="sw-arr-rows">
        {ids.map((id, i) => {
          const w = waits[i] ?? "";
          const m = /^(\d+)\s*min$/.exec(w);
          return (
            <li key={id} style={{ ["--i" as string]: i }}>
              <button onClick={() => onGo(id)}>
                <span className="sw-arr-ord">{ORD[i]}</span>
                <Dot id={id} bulletOf={bulletOf} size={32} />
                <span className="sw-arr-dest">
                  <span className="sw-arr-name">{shortOf(id)}</span>
                  <span className="sw-arr-via">{lineOf(id)?.name ?? "Words line"} · {yearOf(id)}</span>
                </span>
                <span className={"sw-arr-min" + (i === 0 ? " now" : "")}>
                  {m ? <><b>{m[1]}</b><small>min</small></> : <b className="word">{w === "Arriving" ? "Now" : w}</b>}
                </span>
              </button>
            </li>
          );
        })}
      </ol>
      <div className="sw-arr-note" aria-hidden="true">
        <span>STAND CLEAR OF THE CLOSING DOORS · BOOKS &amp; WRITING EXPRESS AT THE NEWSSTAND · ABOUT &amp; CONTACT UP THE STAIRS TO THE STREET · </span>
        <span>STAND CLEAR OF THE CLOSING DOORS · BOOKS &amp; WRITING EXPRESS AT THE NEWSSTAND · ABOUT &amp; CONTACT UP THE STAIRS TO THE STREET · </span>
      </div>
    </aside>
  );
}

// ------------------------------------------------------------------ All stops
export function AllStops({ lines, bulletOf, onGo, onClose, onAbout, here, failed = false }: {
  lines: Line[]; bulletOf: BulletOf; onGo: (id: string) => void; onClose?: () => void; onAbout: () => void; here?: string | null; failed?: boolean;
}) {
  const { shown, done } = useTyped(`ALL STOPS  ${lines.reduce((n, l) => n + l.stops.length, 0)} STOPS ON ${lines.length} LINES`, 30, 250);
  // when the 3D station could not load, stops link straight to the projects
  const go = (id: string) => {
    if (!failed) return onGo(id);
    const href = projectOf(id)?.links[0]?.href;
    if (href) window.open(href, "_blank", "noopener");
  };
  return (
    <div className="sw-dir" role="dialog" aria-modal="true" aria-label="All stops" onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}>
      <div className="sw-dir-inner sw-sign">
        <div className="sw-ticker" aria-hidden="true"><span>{shown}</span><span className={"sw-caret" + (done ? " done" : "")} /></div>
        {onClose && <button className="sw-card-close" onClick={onClose} aria-label="Close">✕</button>}
        <div className="sw-sign-body">
          <div className="sw-dir-title">
            <h2>All stops</h2>
            <p>Every project in the station, by line. Pick one to ride there.</p>
          </div>
          <div className="sw-dir-lines">
            {lines.map((l) => (
              <section key={l.key} className="sw-dir-line" style={{ ["--line" as string]: l.color }}>
                <div className="sw-dir-line-head">
                  <span className="sw-bullet" style={{ background: l.color, width: 34, height: 34, fontSize: 20 }} aria-hidden="true">{l.letter}</span>
                  <div><strong>{l.name}</strong><span>{l.about}</span></div>
                </div>
                <Strip line={l} bulletOf={bulletOf} onGo={go} detail here={here} />
              </section>
            ))}
          </div>
          <div className="sw-dir-exit">
            <button onClick={onAbout}>
              <span className="sw-glyph" aria-hidden="true">↑</span>
              <span><strong>Exit to street · About &amp; contact</strong><em>{site.email}</em></span>
              <span className="sw-strip-go" aria-hidden="true">›</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

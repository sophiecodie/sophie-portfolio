"use client";
// A project opened from its platform poster, as the front page of "The Platform Times":
// blackletter nameplate, a headline and deck, the project image, columns, and a sidebar with
// the numbers, the tools, links and transfers to the other projects on its line.
import type { Project } from "@/data/types";
import { NEWS } from "./newsData";
import { fonts } from "./fonts";
import "./posters.css";

export type Stop = { id: string; title: string; label: string; color: string; ink?: string };
type Props = {
  project: Project;
  bullet: Stop; // this project's route bullet
  lineName?: string;
  transfers: Stop[]; // the other stops on its line
  onTransfer: (id: string) => void;
};

/** Class names for the article that holds the paper (its fonts and look). */
export const newspaperClass = `pv-card pv-newspaper ${fonts}`;

const techOf = (tech: string) => tech.split(" · ").slice(1).join(" · ") || tech;

function Dot({ s, size = 26 }: { s: Stop; size?: number }) {
  return (
    <span className="pv-bullet" style={{ background: s.color, color: s.ink ?? "#fff", width: size, height: size, fontSize: size * 0.6 }} aria-hidden="true">
      {s.label}
    </span>
  );
}

function Transfers({ transfers, onTransfer, lineName, className = "" }: Pick<Props, "transfers" | "onTransfer" | "lineName"> & { className?: string }) {
  if (!transfers.length) return null;
  return (
    <div className={"pv-transfers " + className}>
      {transfers.map((t) => (
        <button key={t.id} onClick={() => onTransfer(t.id)} aria-label={"Transfer to " + t.title} title={t.title}>
          <Dot s={t} size={24} />
        </button>
      ))}
      <span>Transfer on the {lineName}</span>
    </div>
  );
}

export default function Newspaper({ project: p, bullet, lineName, transfers, onTransfer }: Props) {
  const c = NEWS[p.id];
  const heads = ["How it works", "By design", "What’s next"];
  return (
    <div className="pv-paper">
      <div className="pv-ears">
        <p>“All the Projects<br />Fit to Ride”</p>
        <h1 className="pv-mast">The Platform Times</h1>
        <p className="r">Late Edition<br /><small>Sunny, warm, a light breeze</small></p>
      </div>
      <div className="pv-dateline">
        <span>VOL. I . . . No. {bullet.label}</span>
        <span>NEW YORK, {p.year}</span>
        <span>SOPHIE SHIH</span>
      </div>
      <div className="pv-front">
        <div className="pv-lead">
          <p className="pv-kicker"><Dot s={bullet} size={20} /> {p.title} · {lineName}</p>
          <h2>{c?.head ?? p.title}</h2>
          <p className="pv-deck">{c?.deck ?? p.summary}</p>
          {p.image && (
            <figure>
              <img src={p.image} alt="" />
              <figcaption>{p.title}. {p.context}.</figcaption>
            </figure>
          )}
          <div className="pv-cols">
            <p className="pv-drop">{p.summary}</p>
            {p.highlights.map((h, i) => (
              <div key={h}>
                <h3>{heads[i] ?? "Also"}</h3>
                <p>{h}.</p>
              </div>
            ))}
          </div>
        </div>
        <aside className="pv-side">
          <h3>By the Numbers</h3>
          {c?.numbers.map(([n, l]) => (
            <p key={l} className="pv-num"><b>{n}</b>{l}</p>
          ))}
          <h3>Built With</h3>
          <p>{techOf(p.tech)}</p>
          <h3>Read More</h3>
          <ul className="pv-links">
            {p.links.map((l) => <li key={l.href}><a href={l.href} target="_blank" rel="noopener">{l.label} ↗</a></li>)}
          </ul>
          <Transfers transfers={transfers} onTransfer={onTransfer} lineName={lineName} />
        </aside>
      </div>
    </div>
  );
}

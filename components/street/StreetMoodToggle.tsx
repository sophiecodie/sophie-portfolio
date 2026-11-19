"use client";
// The mood switch for the street floor. It only flips the shared mood; the backdrop material
// listens and cross-fades. With a single mood it renders nothing.

import { useEffect, useState } from "react";
import { getStreetMood, onStreetMood, setStreetMood, STREET_MOOD_LABELS, STREET_MOODS, type StreetMood } from "./streetBackdrop";
import css from "./street.module.css";

const ICON: Partial<Record<string, string>> = { sunny: "☀", rainy: "☂", night: "☾" };

export default function StreetMoodToggle({ className = "" }: { className?: string }) {
  const moods = Object.keys(STREET_MOOD_LABELS) as StreetMood[];
  const [mood, setMood] = useState<StreetMood>(moods[0]);
  useEffect(() => {
    setMood(getStreetMood());
    return onStreetMood(setMood);
  }, []);
  const c = STREET_MOODS[mood].credit;
  if (moods.length < 2 && !c) return null;
  return (
    <div className={`${css.wrap} ${className}`}>
    {moods.length > 1 && <div className={css.toggle} role="radiogroup" aria-label="Street mood">
      {moods.map((m) => (
        <button key={m} role="radio" aria-checked={mood === m} className={mood === m ? css.on : ""}
          onClick={() => setStreetMood(m)} title={`${STREET_MOOD_LABELS[m]} street`}>
          <span aria-hidden="true">{ICON[m]}</span> {STREET_MOOD_LABELS[m]}
        </button>
      ))}
    </div>}
    {c && <p className={css.credit}>
      Street photo: <a href={c.source} target="_blank" rel="noreferrer">{c.author}</a>,{" "}
      <a href={c.licenseUrl} target="_blank" rel="noreferrer">{c.license}</a>
    </p>}
    </div>
  );
}

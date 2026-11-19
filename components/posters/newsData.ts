// Headlines for each project's newspaper front page. Everything else comes from
// data/projects.ts, so facts stay in one place; this is only headlines, decks and a couple of numbers.
export type NewsCopy = { head: string; deck: string; numbers: [string, string][] };

export const NEWS: Record<string, NewsCopy> = {
  "college-app-atlas": {
    head: "Students Grow College Essays From a Garden of Their Own Memories",
    deck: "A new web app keeps 5,700 colleges, every prompt and every draft in one cozy place, and its AI asks questions instead of rewriting.",
    numbers: [["5,700+", "colleges in the database"], ["April 2026", "launch"]],
  },
  "purchase-intent": {
    head: "Just Browsing? A Forest of Decision Trees Says Otherwise",
    deck: "Trained on 12,000 online shopping sessions, a Random Forest predicts who will check out.",
    numbers: [["0.92", "ROC-AUC"], ["15.6%", "of sessions ended in a purchase"]],
  },
  "new-york-census": {
    head: "City Redrawn as a Subway Map, One Neighborhood per Stop",
    deck: "Housing, immigration and the economy each get a line through 55 neighborhoods, built from Census and NYC Open Data.",
    numbers: [["55", "neighborhoods"], ["r = −0.79", "rent burden vs. income"]],
  },
  folio: {
    head: "One Feed Brings Left, Right and the Lab Bench Together",
    deck: "Headlines from 12 outlets, each marked with its lean, share a board with brand-new preprints and pop culture.",
    numbers: [["12", "news outlets"], ["3", "preprint servers"]],
  },
  agent00hl7: {
    head: "Agents Turn Radiology Reports Into Letters Patients Can Read",
    deck: "A self-refining LLM loop checks every letter against the report’s ICD-10 codes. It took second place at the SIIM Hackathon.",
    numbers: [["94.94%", "ICD-10 verification accuracy"], ["81.25%", "of letters needed no fixes"]],
  },
  "dream-team": {
    head: "From Scan to Specialist Without a Minute of Hold Music",
    deck: "A team of AI agents reads a radiology report, finds the right specialist and books the consult. Second place at SIIM 2025.",
    numbers: [["4", "agents on the team"], ["100M+", "Americans facing barriers to a specialist"]],
  },
  neurobiome: {
    head: "Your Gut Has Been Talking to Your Brain. Now There’s a Map.",
    deck: "An app from a Mass General Brigham internship explains how gut and oral microbes relate to Parkinson’s disease.",
    numbers: [["66,000+", "microbe–disease links"], ["1", "knowledge graph (MINERVA)"]],
  },
};

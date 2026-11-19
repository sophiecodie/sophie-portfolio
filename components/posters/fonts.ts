// Fonts for the newspaper front page, loaded only where it is used.
import { UnifrakturMaguntia, Old_Standard_TT, Libre_Caslon_Text } from "next/font/google";

// blackletter for the newspaper's nameplate
const masthead = UnifrakturMaguntia({ subsets: ["latin"], weight: "400", variable: "--pv-mast", display: "swap" });
// an old newspaper headline face, and a book face for the columns
const headline = Old_Standard_TT({ subsets: ["latin"], weight: ["400", "700"], style: ["normal", "italic"], variable: "--pv-head", display: "swap" });
const body = Libre_Caslon_Text({ subsets: ["latin"], weight: ["400", "700"], style: ["normal", "italic"], variable: "--pv-body", display: "swap" });
export const fonts = [masthead, headline, body].map((f) => f.variable).join(" ");

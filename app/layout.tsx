import type { Metadata, Viewport } from "next";
import { Inter, Fraunces, Libre_Franklin } from "next/font/google";
import "./subway.css";

const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "700", "800"], variable: "--sw-sans", display: "swap" });
// Libre Franklin is the open stand-in for the Helvetica on MTA signs
const franklin = Libre_Franklin({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800", "900"], variable: "--sw-franklin", display: "swap" });
const fraunces = Fraunces({ subsets: ["latin"], weight: ["400", "700"], variable: "--sw-serif", display: "swap" });

export const metadata: Metadata = {
  title: "Sophie Shih · Portfolio",
  description: "Sophie Shih's portfolio as a sunny 3D subway station you can ride through, built with Blender and Three.js.",
  icons: {
    icon: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23e8732c'/%3E%3Ctext x='32' y='44' font-family='Arial' font-weight='800' font-size='34' text-anchor='middle' fill='white'%3ES%3C/text%3E%3C/svg%3E",
  },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover", themeColor: "#2a211c" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable} ${franklin.variable}`}>
      <body style={{ margin: 0, background: "#2a211c" }}>{children}</body>
    </html>
  );
}

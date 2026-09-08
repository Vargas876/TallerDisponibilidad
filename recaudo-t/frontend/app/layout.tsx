import type { Metadata } from "next";
import { Space_Grotesk, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/SiteHeader";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "RECAUDO-T — Monitoreo de Disponibilidad",
  description:
    "Instrumento de observación de disponibilidad y resiliencia: detección de caídas, redundancia activa y analítica de experimentos E0/E1.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="es"
      className={`${spaceGrotesk.variable} ${jetbrains.variable} bg-base text-ink antialiased`}
    >
      <body className="grid-bg min-h-dvh">
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
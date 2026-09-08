"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";

const RUTAS = [
  { href: "/", label: "Live" },
  { href: "/resultados", label: "Resultados" },
];

function Reloj() {
  const [ahora, setAhora] = useState("");
  useEffect(() => {
    const t = () =>
      setAhora(
        new Date().toLocaleTimeString("es-AR", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }),
      );
    t();
    const id = setInterval(t, 500);
    return () => clearInterval(id);
  }, []);
  return <span className="num text-mut">{ahora}</span>;
}

export function SiteHeader() {
  const path = usePathname();
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.5, 0, 0.1, 1] }}
      className="sticky top-0 z-40 border-b border-line bg-base/80 backdrop-blur-md"
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-5 py-3">
        <Link href="/" className="group flex items-baseline gap-3">
          <span className="text-lg font-semibold tracking-tight text-ink">
            RECAUDO<span className="text-accent">-</span>T
          </span>
          <span className="hidden md:block eyebrow">Disponibilidad &amp; Resiliencia</span>
        </Link>

        <nav className="flex items-center gap-1">
          {RUTAS.map((r) => {
            const activo = path === r.href;
            return (
              <Link
                key={r.href}
                href={r.href}
                className={
                  "px-3 py-1.5 text-[0.72rem] font-medium tracking-[0.14em] uppercase transition-colors " +
                  (activo
                    ? "text-ink border border-line bg-raised"
                    : "text-mut border border-transparent hover:text-ink")
                }
              >
                {r.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-4">
          <Reloj />
        </div>
      </div>
    </motion.header>
  );
}
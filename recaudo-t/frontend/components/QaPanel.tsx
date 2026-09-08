"use client";

export interface QaItem {
  q: string;
  a: string[];
  evidencia: string;
}

export interface QaProps {
  items: QaItem[];
  fuente: string;
}

export function QaPanel({ items, fuente }: QaProps) {
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="mono-label text-faint">Preguntas clave — análisis</h2>
        <span className="num text-[0.7rem] text-faint">
          fuente: {fuente === "live" ? "métricas del experimento" : "muestra incrustada"}
        </span>
      </div>
      <div className="grid gap-3">
        {items.map((item, i) => (
          <article key={i} className="card card-hover px-4 py-3">
            <div className="mb-2 flex items-baseline gap-3">
              <span className="num text-accent text-sm">Q{i + 1}</span>
              <h3 className="text-[0.95rem] font-semibold tracking-tight text-ink">
                {item.q}
              </h3>
            </div>
            <ul className="mb-2 space-y-1 text-sm leading-relaxed text-mut">
              {item.a.map((p, j) => (
                <li key={j}>{p}</li>
              ))}
            </ul>
            <div className="border-t border-linedim pt-2">
              <span className="mono-label text-faint">evidencia · </span>
              <span className="text-xs text-accent">{item.evidencia}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
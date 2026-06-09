/**
 * DriftMonitorExplorer — an ICAP demo for Chapter 11 (production eval & monitoring).
 *
 * A precomputed 30-day trace (dump -> JSON -> island): a frozen offline metric that
 * stays flat and "green" next to a live online signal that drifts past its guardrail
 * after the input mix shifts. The breach the offline dashboard never shows is the
 * whole point of monitoring. Predict/explain prompts live in the chapter prose.
 */
import { useState } from 'preact/hooks';

type Pt = { day: number; offline: number; online: number };
type Data = {
  name: string; note: string; days: number; guardrail: number;
  breach_day: number | null; ylabel: string; series: Pt[];
};

export default function DriftMonitorExplorer({ data }: { data: Data }) {
  const [show, setShow] = useState({ offline: true, online: true });

  const W = 360, H = 170, padL = 34, padB = 22, padT = 10, padR = 8;
  const maxY = 0.8;
  const x = (d: number) => padL + (d / (data.days - 1)) * (W - padL - padR);
  const y = (v: number) => padT + (1 - v / maxY) * (H - padT - padB);
  const path = (key: 'offline' | 'online') =>
    data.series.map((p) => `${x(p.day)},${y(p[key])}`).join(' ');
  const breachX = data.breach_day != null ? x(data.breach_day) : null;

  const chip = (label: string, color: string, on: boolean, toggle: () => void) => (
    <button onClick={toggle} style={{
      display: 'flex', alignItems: 'center', gap: 6, padding: '3px 8px', borderRadius: 6,
      border: '1px solid var(--color-border,#ccc)', background: 'transparent', cursor: 'pointer',
      fontSize: 12.5, opacity: on ? 1 : 0.45,
    }}>
      <span style={{ width: 14, height: 3, background: color, display: 'inline-block' }} />{label}
    </button>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Drift monitor</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.ylabel} · {data.days} days</span>
      </div>

      <div style={{ display: 'flex', gap: 6, margin: '10px 0' }}>
        {chip('Offline (frozen set)', '#94a3b8', show.offline, () => setShow((s) => ({ ...s, offline: !s.offline })))}
        {chip('Online (live traffic)', '#6366f1', show.online, () => setShow((s) => ({ ...s, online: !s.online })))}
      </div>

      <svg width={W} height={H} role="img" aria-label="offline vs online metric over time with a guardrail">
        {/* breach shading */}
        {breachX != null && <rect x={breachX} y={padT} width={W - padR - breachX} height={H - padT - padB} fill="#fee2e2" opacity={0.5} />}
        {/* axes */}
        <line x1={padL} y1={y(0)} x2={W - padR} y2={y(0)} stroke="var(--color-border,#ddd)" />
        <line x1={padL} y1={padT} x2={padL} y2={y(0)} stroke="var(--color-border,#ddd)" />
        {/* guardrail */}
        <line x1={padL} y1={y(data.guardrail)} x2={W - padR} y2={y(data.guardrail)} stroke="#dc2626" stroke-width={1} stroke-dasharray="5 3" />
        <text x={W - padR} y={y(data.guardrail) - 4} font-size={9} text-anchor="end" fill="#dc2626">guardrail {data.guardrail}</text>
        {/* series */}
        {show.offline && <polyline points={path('offline')} fill="none" stroke="#94a3b8" stroke-width={2} />}
        {show.online && <polyline points={path('online')} fill="none" stroke="#6366f1" stroke-width={2} />}
        {/* breach marker */}
        {breachX != null && <line x1={breachX} y1={padT} x2={breachX} y2={y(0)} stroke="#dc2626" stroke-width={1} />}
        {breachX != null && <text x={breachX + 3} y={padT + 9} font-size={9} fill="#dc2626">alert: day {data.breach_day}</text>}
        <text x={padL} y={H - 6} font-size={9} fill="#64748b">day 0</text>
        <text x={W - padR} y={H - 6} font-size={9} text-anchor="end" fill="#64748b">day {data.days - 1}</text>
      </svg>

      <p style={{ fontSize: 12.5, opacity: 0.8, margin: '8px 0 0' }}>
        The offline metric (frozen eval set) is flat and green all month. The live signal
        drifts as the input mix changes and breaches the guardrail on day {data.breach_day} —
        a failure the offline dashboard never shows.
      </p>
    </div>
  );
}

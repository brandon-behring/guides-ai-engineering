/**
 * ReliabilityExplorer — an ICAP demo for Chapter 4 (calibration & reliability).
 *
 * Reads precomputed reliability-curve data (dump -> JSON -> island; computed in
 * `mini_eval.calibration`) for two models that rank risk identically but report
 * different probabilities. Toggle between them to watch the curve sit on the
 * diagonal (calibrated) or bow below it at high confidence (overconfident), with
 * the ECE and Brier score updating. Predict/explain prompts live in the prose.
 */
import { useState } from 'preact/hooks';

type Bin = { confidence: number; accuracy: number; count: number };
type Model = { curve: Bin[]; ece: number; brier: number };
type Data = { name: string; note: string; n: number; models: Record<string, Model> };

const f3 = (x: number) => x.toFixed(3);

export default function ReliabilityExplorer({ data }: { data: Data }) {
  const [which, setWhich] = useState('calibrated');
  const m = data.models[which];

  const S = 240, pad = 4;
  const x = (v: number) => pad + v * (S - 2 * pad);
  const y = (v: number) => S - pad - v * (S - 2 * pad); // invert: accuracy up
  const maxc = Math.max(...m.curve.map((b) => b.count), 1);
  const r = (c: number) => 3 + 7 * Math.sqrt(c / maxc);
  const line = m.curve.map((b) => `${x(b.confidence)},${y(b.accuracy)}`).join(' ');

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });
  const stat = (label: string, val: string, warn = false) => (
    <div style={{ padding: '6px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)', minWidth: 88 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: warn ? '#dc2626' : 'inherit' }}>{val}</div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Reliability diagram</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.n} predictions</span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0' }}>
        {Object.keys(data.models).map((k) => (
          <button key={k} style={btn(which === k)} onClick={() => setWhich(k)}>{k}</button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <svg width={S} height={S} role="img" aria-label="reliability diagram: predicted confidence vs empirical accuracy">
          <rect x={pad} y={pad} width={S - 2 * pad} height={S - 2 * pad} fill="none" stroke="var(--color-border,#eee)" />
          {/* perfect-calibration diagonal */}
          <line x1={x(0)} y1={y(0)} x2={x(1)} y2={y(1)} stroke="#94a3b8" stroke-width={1} stroke-dasharray="4 3" />
          {/* the model's curve */}
          <polyline points={line} fill="none" stroke="var(--color-accent,#6366f1)" stroke-width={1.5} />
          {m.curve.map((b, i) => (
            <circle key={i} cx={x(b.confidence)} cy={y(b.accuracy)} r={r(b.count)}
              fill="var(--color-accent,#6366f1)" opacity={0.65} />
          ))}
          <text x={x(0.5)} y={S - 6} font-size={10} text-anchor="middle" fill="#64748b">predicted confidence →</text>
          <text x={10} y={y(0.5)} font-size={10} text-anchor="middle" fill="#64748b" transform={`rotate(-90 10 ${y(0.5)})`}>empirical accuracy →</text>
        </svg>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {stat('ECE', f3(m.ece), m.ece > 0.05)}
          {stat('Brier', f3(m.brier))}
          <p style={{ fontSize: 12, opacity: 0.75, maxWidth: 150, margin: 0 }}>
            On the dashed line = perfectly calibrated. Below it at the right = <em>overconfident</em>
            {' '}(says 0.9, is right less often). Dot size = how many predictions in that bin.
          </p>
        </div>
      </div>
    </div>
  );
}

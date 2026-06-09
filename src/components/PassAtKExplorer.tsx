/**
 * PassAtKExplorer — an ICAP demo for Chapter 10 (agentic & task evaluation).
 *
 * Precomputed pass@k curves (dump -> JSON -> island; from mini_eval.agent) for a
 * flaky vs a reliable agent. Toggle between them to see pass@k climb with attempts
 * while pass@1 — the first-try success a user actually gets — tells the real story.
 * The gap between pass@1 and pass@k is how an unreliable agent looks good on paper.
 */
import { useState } from 'preact/hooks';

type CurvePt = { k: number; pass: number };
type Scenario = { label: string; K: number; n_tasks: number; pass1: number; passK: number; curve: CurvePt[] };
type Data = { name: string; note: string; scenarios: Scenario[] };

const pct = (x: number) => (x * 100).toFixed(0) + '%';

export default function PassAtKExplorer({ data }: { data: Data }) {
  const [i, setI] = useState(0);
  const s = data.scenarios[i];

  const W = 320, H = 150, pad = 28;
  const xK = (k: number) => pad + ((k - 1) / (s.K - 1)) * (W - pad - 8);
  const yP = (p: number) => pad - 8 + (1 - p) * (H - pad - 14);
  const pts = s.curve.map((c) => `${xK(c.k)},${yP(c.pass)}`).join(' ');

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });
  const stat = (label: string, val: string, warn = false) => (
    <div style={{ padding: '6px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)', minWidth: 92 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: warn ? '#dc2626' : 'inherit' }}>{val}</div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>pass@k explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{s.n_tasks} tasks · {s.K} samples each</span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0' }}>
        {data.scenarios.map((sc, idx) => (
          <button key={sc.label} style={btn(i === idx)} onClick={() => setI(idx)}>{sc.label}</button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <svg width={W} height={H} role="img" aria-label="pass@k as a function of k">
          {/* axes */}
          <line x1={pad} y1={yP(0)} x2={W - 4} y2={yP(0)} stroke="var(--color-border,#ddd)" />
          <line x1={pad} y1={yP(0)} x2={pad} y2={yP(1)} stroke="var(--color-border,#ddd)" />
          {/* pass@1 reference line — what users actually get */}
          <line x1={pad} y1={yP(s.pass1)} x2={W - 4} y2={yP(s.pass1)} stroke="#dc2626" stroke-width={1} stroke-dasharray="4 3" />
          {/* curve */}
          <polyline points={pts} fill="none" stroke="var(--color-accent,#6366f1)" stroke-width={2} />
          {s.curve.map((c) => <circle key={c.k} cx={xK(c.k)} cy={yP(c.pass)} r={2.5} fill="var(--color-accent,#6366f1)" />)}
          <text x={pad} y={H - 4} font-size={10} fill="#64748b">k=1</text>
          <text x={W - 24} y={H - 4} font-size={10} fill="#64748b">k={s.K}</text>
          <text x={W - 70} y={yP(s.pass1) - 4} font-size={9} fill="#dc2626">pass@1 (users)</text>
        </svg>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {stat('pass@1', pct(s.pass1), s.pass1 < 0.5)}
          {stat('pass@' + s.K, pct(s.passK))}
        </div>
      </div>
      <p style={{ fontSize: 12.5, opacity: 0.8, margin: '8px 0 0' }}>
        pass@k always rises with k (more tries, more chances). The {s.label.toLowerCase()} reaches
        ~100% at pass@{s.K} yet succeeds {pct(s.pass1)} of the time on the first try —
        which is what a user lives with unless you retry-and-verify.
      </p>
    </div>
  );
}

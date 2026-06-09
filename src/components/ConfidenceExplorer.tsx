/**
 * ConfidenceExplorer — an ICAP demo for Chapter 3 (confidence & statistical rigor).
 *
 * Two precomputed lessons (dump -> JSON -> island; see scripts/build_demo_data.py,
 * all the resampling already done in `mini_eval.confidence`):
 *  1. "CIs shrink with data" — pick a sample size and watch the 95% bootstrap
 *     intervals on precision/recall/F1 contract as n grows.
 *  2. "Is B better than A?" — the bootstrap distribution of F1(B) − F1(A) with the
 *     95% CI and the zero line, plus a permutation p-value, so a raw lead can be
 *     judged real or noise. Predict/explain prompts live in the chapter prose.
 */
import { useState } from 'preact/hooks';

type CiByN = { n: number; n_pos: number; point: Record<string, number>; ci: Record<string, number[]> };
type Ab = {
  metric: string; threshold: number; n: number;
  a_point: number; b_point: number; diff: number; ci: number[];
  excludes_zero: boolean; p_value: number;
  hist: { lo: number; hi: number; bins: number; counts: number[] };
};
type Data = { name: string; note: string; threshold: number; ci_by_n: CiByN[]; ab: Ab };

const METRICS = ['precision', 'recall', 'f1'];
const LABEL: Record<string, string> = { precision: 'Precision', recall: 'Recall', f1: 'F1' };
const f3 = (x: number) => x.toFixed(3);

export default function ConfidenceExplorer({ data }: { data: Data }) {
  const [tab, setTab] = useState<'ci' | 'ab'>('ci');
  const [ni, setNi] = useState(0);

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });

  // --- mode 1: CI bars across sample sizes ---
  const TW = 240;
  const xUnit = (v: number) => Math.min(1, Math.max(0, v)) * TW; // clamp; metrics live in [0, 1]
  const row = data.ci_by_n[ni];
  const ciBar = (m: string) => {
    const p = row.point[m];
    const [lo, hi] = row.ci[m];
    return (
      <div key={m} style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '6px 0' }}>
        <span style={{ width: 70, fontSize: 13 }}>{LABEL[m]}</span>
        <svg width={TW} height={22} role="img" aria-label={`${LABEL[m]} 95% confidence interval`}>
          <line x1={0} y1={11} x2={TW} y2={11} stroke="var(--color-border,#ddd)" stroke-width={1} />
          <rect x={xUnit(lo)} y={5} width={Math.max(1, xUnit(hi) - xUnit(lo))} height={12}
            fill="var(--color-accent-soft,#e0e7ff)" stroke="var(--color-accent,#6366f1)" stroke-width={1} />
          <circle cx={xUnit(p)} cy={11} r={4} fill="var(--color-accent,#6366f1)" />
        </svg>
        <span style={{ fontSize: 12, fontVariantNumeric: 'tabular-nums', opacity: 0.85 }}>
          {f3(p)} <span style={{ opacity: 0.6 }}>[{f3(lo)}, {f3(hi)}] · w={f3(hi - lo)}</span>
        </span>
      </div>
    );
  };

  // --- mode 2: bootstrap-difference histogram for B − A ---
  const ab = data.ab;
  const HW = 340, HH = 130;
  const { lo, hi, counts } = ab.hist;
  const span = hi - lo || 1;
  const xOf = (d: number) => ((d - lo) / span) * HW;
  const maxc = Math.max(...counts, 1);
  const bw = HW / counts.length;
  const zeroIn = lo <= 0 && hi >= 0;
  const sig = ab.excludes_zero;
  const verdict = sig
    ? `B beats A by ${f3(ab.diff)} ${ab.metric}. The 95% CI [${f3(ab.ci[0])}, ${f3(ab.ci[1])}] excludes 0 (p = ${ab.p_value}) — the lead is statistically real${ab.p_value > 0.04 ? ', but only barely' : ''}.`
    : `B leads by ${f3(ab.diff)} ${ab.metric}, but the 95% CI [${f3(ab.ci[0])}, ${f3(ab.ci[1])}] includes 0 (p = ${ab.p_value}). That lead is within sampling noise — don't ship on it yet.`;

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Confidence explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.name}</span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0' }}>
        <button style={btn(tab === 'ci')} onClick={() => setTab('ci')}>CIs shrink with data</button>
        <button style={btn(tab === 'ab')} onClick={() => setTab('ab')}>Is B better than A?</button>
      </div>

      {tab === 'ci' ? (
        <div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap', margin: '6px 0' }}>
            <span style={{ fontSize: 13, opacity: 0.8 }}>Eval-set size n:</span>
            {data.ci_by_n.map((r, i) => (
              <button key={r.n} style={btn(i === ni)} onClick={() => setNi(i)}>{r.n}</button>
            ))}
            <span style={{ fontSize: 12, opacity: 0.6 }}>({row.n_pos} positive)</span>
          </div>
          <div style={{ margin: '8px 0' }}>{METRICS.map(ciBar)}</div>
          <p style={{ fontSize: 12.5, opacity: 0.8, margin: '4px 0 0' }}>
            Each bar is a 95% bootstrap interval; the dot is the point estimate. Step n up
            and the intervals contract — roughly with 1/√n. At n=100 the "metric" is a wide
            range; only the larger sets pin it down.
          </p>
        </div>
      ) : (
        <div>
          <p style={{ fontSize: 13, opacity: 0.85, margin: '2px 0 8px' }}>
            Two models on the same {ab.n}-example set: A scores <strong>{f3(ab.a_point)}</strong>,
            B scores <strong>{f3(ab.b_point)}</strong> ({ab.metric}). Below is the bootstrap
            distribution of <strong>B − A</strong>; the band is the 95% CI, the dashed line is zero.
          </p>
          <svg width={HW} height={HH + 18} role="img" aria-label="bootstrap distribution of the F1 difference between models B and A">
            {/* 95% CI band */}
            <rect x={xOf(ab.ci[0])} y={0} width={Math.max(1, xOf(ab.ci[1]) - xOf(ab.ci[0]))} height={HH}
              fill="var(--color-accent-soft,#e0e7ff)" opacity={0.6} />
            {/* histogram bars */}
            {counts.map((c, i) => {
              const h = (c / maxc) * (HH - 18);
              return <rect key={i} x={i * bw + 0.5} y={HH - h} width={bw - 1} height={h} fill="var(--color-accent,#6366f1)" opacity={0.8} />;
            })}
            {/* zero line */}
            {zeroIn && <line x1={xOf(0)} y1={0} x2={xOf(0)} y2={HH} stroke="#dc2626" stroke-width={2} stroke-dasharray="4 3" />}
            {/* point estimate */}
            <line x1={xOf(ab.diff)} y1={0} x2={xOf(ab.diff)} y2={HH} stroke="#111" stroke-width={1.5} />
            <text x={xOf(ab.diff)} y={HH + 13} font-size={10} text-anchor="middle" fill="#111">B−A = {f3(ab.diff)}</text>
            {zeroIn && <text x={xOf(0)} y={HH + 13} font-size={10} text-anchor="middle" fill="#dc2626">0</text>}
          </svg>
          <p style={{ fontSize: 13, fontWeight: 600, margin: '8px 0 0', color: sig ? '#16a34a' : '#a16207' }}>
            {sig ? '✓ ' : '⚠ '}{verdict}
          </p>
        </div>
      )}
    </div>
  );
}

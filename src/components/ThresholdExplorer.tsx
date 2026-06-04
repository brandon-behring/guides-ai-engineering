/**
 * ThresholdExplorer — an ICAP demo for Chapter 2 (the threshold trade-off).
 *
 * Reads a precomputed threshold sweep (dump -> JSON -> island; see
 * scripts/build_demo_data.py) and lets the reader drag the decision threshold to
 * watch the confusion matrix, precision/recall/F1, the score distributions, and
 * the operating point on the PR curve move together. No model, no server — all
 * the computation already happened in `mini_eval`. Predict/explain prompts live
 * in the chapter prose; this island is the "interact" step.
 */
import { useState } from 'preact/hooks';

type Row = {
  threshold: number; tp: number; fp: number; tn: number; fn: number;
  precision: number; recall: number; f1: number; accuracy: number; fpr: number; tpr: number;
};
type Data = {
  name: string; n: number; pos: number; neg: number; prevalence: number;
  sweep: Row[]; hist: { bins: number; pos: number[]; neg: number[] };
};

const pct = (x: number) => (x * 100).toFixed(1) + '%';

export default function ThresholdExplorer({ data }: { data: Data }) {
  const [t, setT] = useState(0.5);
  const idx = Math.min(data.sweep.length - 1, Math.round(t * (data.sweep.length - 1)));
  const r = data.sweep[idx];

  // --- score-distribution histogram (SVG) ---
  const W = 320, H = 120, bins = data.hist.bins;
  const maxCount = Math.max(...data.hist.pos, ...data.hist.neg, 1);
  const bw = W / bins;
  const bar = (count: number) => (count / maxCount) * (H - 16);

  // --- PR curve (SVG): x = recall, y = precision ---
  const PW = 200, PH = 120;
  const prPts = data.sweep
    .map((row) => `${row.recall * PW},${(1 - row.precision) * (PH - 10) + 5}`)
    .join(' ');

  const cell: any = { border: '1px solid var(--color-border,#ccc)', padding: '6px 10px', textAlign: 'center' };
  const metric = (label: string, val: string, hl = false) => (
    <div style={{ padding: '6px 10px', borderRadius: 6, background: hl ? 'var(--color-accent-soft,#eef)' : 'var(--color-bg-subtle,#f6f6f6)', minWidth: 92 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Threshold explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.name} · {data.pos}/{data.n} positive ({pct(data.prevalence)})</span>
      </div>

      <label style={{ display: 'block', margin: '12px 0 4px' }}>
        Decision threshold: <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{t.toFixed(2)}</strong> — predict <em>positive</em> when score ≥ {t.toFixed(2)}
      </label>
      <input type="range" min={0} max={1} step={0.01} value={t}
        onInput={(e) => setT(parseFloat((e.target as HTMLInputElement).value))}
        style={{ width: '100%' }} aria-label="decision threshold" />

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, margin: '12px 0' }}>
        {metric('Precision', pct(r.precision))}
        {metric('Recall (TPR)', pct(r.recall), true)}
        {metric('F1', r.f1.toFixed(3))}
        {metric('Accuracy', pct(r.accuracy))}
        {metric('FPR', pct(r.fpr))}
      </div>

      <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Confusion matrix</div>
          <table style={{ borderCollapse: 'collapse', fontVariantNumeric: 'tabular-nums' }}>
            <tbody>
              <tr><td style={cell}></td><td style={{ ...cell, fontSize: 11, opacity: 0.7 }}>pred +</td><td style={{ ...cell, fontSize: 11, opacity: 0.7 }}>pred −</td></tr>
              <tr><td style={{ ...cell, fontSize: 11, opacity: 0.7 }}>actual +</td><td style={{ ...cell, background: '#dcfce7' }}>TP {r.tp}</td><td style={{ ...cell, background: '#fee2e2' }}>FN {r.fn}</td></tr>
              <tr><td style={{ ...cell, fontSize: 11, opacity: 0.7 }}>actual −</td><td style={{ ...cell, background: '#fee2e2' }}>FP {r.fp}</td><td style={{ ...cell, background: '#dcfce7' }}>TN {r.tn}</td></tr>
            </tbody>
          </table>
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>Score distribution (▢ neg · ▰ pos) + threshold</div>
          <svg width={W} height={H} role="img" aria-label="score distributions with threshold line">
            {data.hist.neg.map((c, i) => <rect key={'n' + i} x={i * bw + 1} y={H - bar(c)} width={bw - 2} height={bar(c)} fill="#94a3b8" opacity={0.6} />)}
            {data.hist.pos.map((c, i) => <rect key={'p' + i} x={i * bw + 1} y={H - bar(c)} width={bw - 2} height={bar(c)} fill="#6366f1" opacity={0.75} />)}
            <line x1={t * W} y1={0} x2={t * W} y2={H} stroke="#dc2626" stroke-width={2} />
          </svg>
        </div>

        <div>
          <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 4 }}>PR curve (recall → precision)</div>
          <svg width={PW} height={PH} role="img" aria-label="precision-recall curve with current operating point">
            <polyline points={prPts} fill="none" stroke="#6366f1" stroke-width={1.5} />
            <circle cx={r.recall * PW} cy={(1 - r.precision) * (PH - 10) + 5} r={4} fill="#dc2626" />
          </svg>
        </div>
      </div>
    </div>
  );
}

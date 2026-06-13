/**
 * CascadeExplorer — an ICAP demo for guide-3 Chapter 4 (cost engineering).
 *
 * A model cascade over 10K queries/day: route easy queries to a cheap model,
 * escalate the rest to the frontier. Two levers — the routing threshold and the
 * *quality of the routing signal* (calibrated vs miscalibrated) — over a sweep
 * precomputed by mini_prod.cascade_sweep. Predict-before-reveal: can a cascade cut
 * the frontier-only bill while holding accuracy within a point of frontier? The
 * answer flips entirely on whether the confidence signal is calibrated — that is
 * the lesson the two curves make visceral, against the all-cheap / all-frontier
 * baselines.
 */
import { useState } from 'preact/hooks';

type Row = {
  threshold: number; easy_fraction: number; accuracy: number;
  cost_q: number; cost_month: number; escalation_precision: number;
};
type Endpoint = { accuracy: number; cost_q: number; cost_month: number };
type Data = {
  name: string; note: string; qpd: number; cost_easy: number; cost_hard: number;
  baseline: { all_cheap: Endpoint; all_hard: Endpoint };
  thresholds: number[];
  calibrated: Row[]; miscalibrated: Row[];
  default_threshold: number;
};

const fmt$ = (x: number) => '$' + Math.round(x).toLocaleString();
const pct = (x: number) => (x * 100).toFixed(1) + '%';

export default function CascadeExplorer({ data }: { data: Data }) {
  const [revealed, setRevealed] = useState(false);
  const [signal, setSignal] = useState<'calibrated' | 'miscalibrated'>('calibrated');
  const [threshold, setThreshold] = useState(data.default_threshold);

  const rows = data[signal];
  const row = rows.find((r) => Math.abs(r.threshold - threshold) < 1e-9) ?? rows[0];
  const cheap = data.baseline.all_cheap;
  const hard = data.baseline.all_hard;

  const accFloor = cheap.accuracy, accCeil = hard.accuracy;
  const accPct = Math.max(0, Math.min(100, ((row.accuracy - accFloor) / (accCeil - accFloor)) * 100));
  const costFloor = cheap.cost_month, costCeil = hard.cost_month;
  const costPct = Math.max(0, Math.min(100, ((row.cost_month - costFloor) / (costCeil - costFloor)) * 100));
  const savings = (1 - row.cost_month / hard.cost_month) * 100;
  const nearFrontier = row.accuracy >= hard.accuracy - 0.01;

  const btn = (active: boolean): any => ({
    padding: '4px 9px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });
  const lever = (label: string, children: any) => (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexWrap: 'wrap', margin: '4px 0' }}>
      <span style={{ fontSize: 12, opacity: 0.7, minWidth: 120 }}>{label}</span>
      {children}
    </div>
  );
  const metric = (label: string, val: string, accent?: string) => (
    <div style={{ padding: '6px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)', minWidth: 104 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: accent ?? 'inherit' }}>{val}</div>
    </div>
  );
  const gauge = (leftLabel: string, rightLabel: string, fillPct: number, color: string) => (
    <div style={{ margin: '4px 0 10px' }}>
      <div style={{ position: 'relative', height: 16, borderRadius: 5, background: 'var(--color-bg-subtle,#f0f0f0)', border: '1px solid var(--color-border,#ddd)' }}>
        <div style={{ width: `${fillPct}%`, height: '100%', borderRadius: 5, background: color }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, opacity: 0.6 }}>
        <span>{leftLabel}</span><span>{rightLabel}</span>
      </div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Model cascade explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          {data.qpd.toLocaleString()} queries/day · cheap {fmt$(cheap.cost_month)}/mo · frontier {fmt$(hard.cost_month)}/mo
        </span>
      </div>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '10px 0' }}>
            <strong>Predict first:</strong> frontier-only is {fmt$(hard.cost_month)}/month at{' '}
            {pct(hard.accuracy)} accuracy. A cascade sends the easy queries to the cheap model
            ({fmt$(cheap.cost_month)}/mo but only {pct(cheap.accuracy)}). Can routing cut the bill
            by half while holding accuracy within a point of frontier? Does it matter whether the
            confidence signal it routes on is <em>calibrated</em>?
          </p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed(true)}>
            Reveal the cascade
          </button>
        </div>
      ) : (
        <div>
          {lever('routing signal', (
            <>
              <button style={btn(signal === 'calibrated')} onClick={() => setSignal('calibrated')}>calibrated</button>
              <button style={btn(signal === 'miscalibrated')} onClick={() => setSignal('miscalibrated')}>miscalibrated</button>
            </>
          ))}
          {lever('escalate below', data.thresholds.map((t) => (
            <button key={t} style={btn(Math.abs(t - threshold) < 1e-9)} onClick={() => setThreshold(t)}>
              {t.toFixed(1)}
            </button>
          )))}

          <div style={{ margin: '12px 0 2px', fontSize: 12, opacity: 0.7 }}>
            accuracy — {pct(row.accuracy)} {nearFrontier ? '(≈ frontier)' : '(below frontier)'}
          </div>
          {gauge(`all-cheap ${pct(accFloor)}`, `frontier ${pct(accCeil)}`, accPct,
            nearFrontier ? '#16a34a' : '#f59e0b')}

          <div style={{ margin: '2px 0 2px', fontSize: 12, opacity: 0.7 }}>
            monthly bill — {fmt$(row.cost_month)} ({savings >= 0 ? savings.toFixed(0) + '% under frontier' : 'above frontier'})
          </div>
          {gauge(`all-cheap ${fmt$(costFloor)}`, `frontier ${fmt$(costCeil)}`, costPct, '#3b82f6')}

          <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
            {metric('routed cheap', pct(row.easy_fraction))}
            {metric('accuracy', pct(row.accuracy), nearFrontier ? '#16a34a' : '#d97706')}
            {metric('bill / month', fmt$(row.cost_month), '#2563eb')}
            {metric('escalations warranted', pct(row.escalation_precision),
              row.escalation_precision >= 0.8 ? '#16a34a' : '#dc2626')}
          </div>

          <p style={{ margin: '8px 0 0', fontSize: 13, opacity: 0.85 }}>{data.note}</p>
        </div>
      )}
    </div>
  );
}

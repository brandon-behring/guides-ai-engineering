/**
 * BreakEvenExplorer — an ICAP demo for guide-3 Chapter 10 (self-host vs API).
 *
 * The crossover volume where a fixed monthly GPU cost (self-host) equals the
 * per-query API bill, precomputed via mini_rag.budget.break_even_queries_per_day.
 * Three levers (GPU tier, API rate, daily volume); each cell reports the crossover,
 * both monthly bills, and which side is cheaper. Predict-before-reveal: at the
 * default volume on a frontier-class model, self-host or API — and by how much? The
 * chapter's whole point is that the answer is often close, and the non-cost factors
 * (latency, data residency, ops burden) decide before the crossover does.
 */
import { useState } from 'preact/hooks';

type Combo = {
  gpu: number; api_rate: number; vol: number;
  crossover_qpd: number; api_month: number; self_month: number; cheaper: string;
};
type Data = {
  name: string; note: string;
  levers: { gpu: number[]; api_rate: number[]; vol: number[] };
  defaults: { gpu: number; api_rate: number; vol: number };
  combos: Combo[];
};

const fmt$ = (x: number) => '$' + x.toLocaleString();
const fmtRate = (x: number) => '$' + x.toFixed(4) + '/q';

export default function BreakEvenExplorer({ data }: { data: Data }) {
  const [revealed, setRevealed] = useState(false);
  const [gpu, setGpu] = useState(data.defaults.gpu);
  const [rate, setRate] = useState(data.defaults.api_rate);
  const [vol, setVol] = useState(data.defaults.vol);

  const find = (g: number, a: number, v: number) =>
    data.combos.find((c) => c.gpu === g && c.api_rate === a && c.vol === v)!;
  const combo = find(gpu, rate, vol);
  const def = find(data.defaults.gpu, data.defaults.api_rate, data.defaults.vol);
  const selfWins = combo.cheaper === 'self-host';
  const maxBill = Math.max(combo.api_month, combo.self_month, 1);

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
  const bar = (label: string, value: number, color: string, winner: boolean) => (
    <div style={{ margin: '4px 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
        <span>{label}{winner ? ' ✓' : ''}</span>
        <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: winner ? 700 : 400 }}>{fmt$(value)}/mo</span>
      </div>
      <div style={{ height: 16, background: 'var(--color-bg-subtle,#f0f0f0)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${(value / maxBill) * 100}%`, height: '100%', background: color }} />
      </div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Self-host vs API — break-even</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>crossover = GPU/mo ÷ 30 ÷ API $/query</span>
      </div>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '10px 0' }}>
            <strong>Predict first:</strong> a {fmt$(data.defaults.gpu)}/month GPU vs a frontier-class
            API at {fmtRate(data.defaults.api_rate)}, serving {data.defaults.vol.toLocaleString()}{' '}
            queries/day. Which is cheaper — and is it close enough that something other than cost
            should decide?
          </p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed(true)}>
            Reveal the break-even
          </button>
        </div>
      ) : (
        <div>
          {lever('self-host GPU', data.levers.gpu.map((g) => (
            <button key={g} style={btn(g === gpu)} onClick={() => setGpu(g)}>{fmt$(g)}/mo</button>
          )))}
          {lever('API rate', data.levers.api_rate.map((a) => (
            <button key={a} style={btn(a === rate)} onClick={() => setRate(a)}>{fmtRate(a)}</button>
          )))}
          {lever('volume', data.levers.vol.map((v) => (
            <button key={v} style={btn(v === vol)} onClick={() => setVol(v)}>{(v / 1000)}k/day</button>
          )))}

          <div style={{ margin: '12px 0 8px', fontSize: 13 }}>
            break-even at <strong>{combo.crossover_qpd.toLocaleString()}</strong> queries/day · you're at{' '}
            <strong>{combo.vol.toLocaleString()}</strong> →{' '}
            <span style={{ fontWeight: 700, color: selfWins ? '#16a34a' : '#2563eb' }}>
              {selfWins ? 'self-host' : 'API'} is cheaper
            </span>
          </div>

          {bar('API (per-query)', combo.api_month, '#93c5fd', !selfWins)}
          {bar('Self-host (fixed GPU)', combo.self_month, '#86efac', selfWins)}

          <p style={{ margin: '10px 0 0', fontSize: 13, opacity: 0.85 }}>{data.note}</p>
        </div>
      )}
    </div>
  );
}

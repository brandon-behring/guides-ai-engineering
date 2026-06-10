/**
 * BudgetExplorer — an ICAP demo for guide-2 Chapter 7 (RAG in production).
 *
 * Four levers (answer length, context chunks k, model tier, cache hit rate)
 * over one support bot at 10K queries/day; every cell's latency split and
 * monthly bill precomputed via mini_rag.budget with stated API-class
 * constants. Predict-before-reveal: commit to which single lever change cuts
 * the bill most from the default. Latency bar splits TTFT (what streaming
 * users feel) from decode (what the SLA feels).
 */
import { useState } from 'preact/hooks';

type Combo = {
  output: number; k: number; model: string; cache: number;
  input_tokens: number; ttft_ms: number; decode_ms: number; total_ms: number;
  sla_ok: boolean; cost_q: number; eff_cost_q: number; cost_month: number;
};
type Data = {
  name: string; note: string; qpd: number; sla_ms: number;
  levers: { output: number[]; k: number[]; model: { key: string; label: string }[]; cache: number[] };
  defaults: { output: number; k: number; model: string; cache: number };
  combos: Combo[];
};

const fmt$ = (x: number) => '$' + x.toLocaleString('en-US', { maximumFractionDigits: 0 });

export default function BudgetExplorer({ data }: { data: Data }) {
  const [revealed, setRevealed] = useState(false);
  const [output, setOutput] = useState(data.defaults.output);
  const [k, setK] = useState(data.defaults.k);
  const [model, setModel] = useState(data.defaults.model);
  const [cache, setCache] = useState(data.defaults.cache);

  const combo = data.combos.find(
    (c) => c.output === output && c.k === k && c.model === model && c.cache === cache,
  )!;
  const def = data.combos.find(
    (c) => c.output === data.defaults.output && c.k === data.defaults.k
      && c.model === data.defaults.model && c.cache === data.defaults.cache,
  )!;
  const ttftPct = (combo.ttft_ms / combo.total_ms) * 100;

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
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
    <div style={{ padding: '6px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)', minWidth: 100 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: accent ?? 'inherit' }}>{val}</div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Production budget explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.qpd.toLocaleString()} queries/day · SLA: total ≤ {data.sla_ms / 1000}s</span>
      </div>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '10px 0' }}>
            <strong>Predict first:</strong> the default config is a frontier model, 4 context chunks,
            200-token answers, no cache — {fmt$(def.cost_month)}/month and it misses the 2s SLA.
            Which <em>single</em> lever change cuts the monthly bill the most: shorter answers,
            fewer chunks, a 70/30 cascade, or a 60% cache?
          </p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed(true)}>
            Reveal the levers
          </button>
        </div>
      ) : (
        <div>
          {lever('answer length', data.levers.output.map((o) => (
            <button key={o} style={btn(o === output)} onClick={() => setOutput(o)}>{o} tok</button>
          )))}
          {lever('context chunks k', data.levers.k.map((kk) => (
            <button key={kk} style={btn(kk === k)} onClick={() => setK(kk)}>{kk}</button>
          )))}
          {lever('model tier', data.levers.model.map((m) => (
            <button key={m.key} style={btn(m.key === model)} onClick={() => setModel(m.key)}>{m.label}</button>
          )))}
          {lever('cache hit rate', data.levers.cache.map((c) => (
            <button key={c} style={btn(c === cache)} onClick={() => setCache(c)}>{(c * 100).toFixed(0)}%</button>
          )))}

          <div style={{ margin: '12px 0 6px' }}>
            <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 3 }}>
              latency — TTFT {combo.ttft_ms}ms (felt, when streaming) + decode {combo.decode_ms}ms = {combo.total_ms}ms total
            </div>
            <div style={{ display: 'flex', height: 18, borderRadius: 5, overflow: 'hidden', border: '1px solid var(--color-border,#ddd)' }}>
              <div style={{ width: `${ttftPct}%`, background: '#93c5fd' }} title="TTFT" />
              <div style={{ flex: 1, background: combo.sla_ok ? '#86efac' : '#fca5a5' }} title="decode" />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
            {metric('SLA (≤2s total)', combo.sla_ok ? 'PASS' : 'MISS', combo.sla_ok ? '#16a34a' : '#dc2626')}
            {metric('input tokens', String(combo.input_tokens))}
            {metric('cost / query', '$' + combo.eff_cost_q.toFixed(4))}
            {metric('cost / month', fmt$(combo.cost_month),
              combo.cost_month < def.cost_month ? '#16a34a' : undefined)}
            {metric('vs default', (combo.cost_month <= def.cost_month ? '−' : '+')
              + Math.abs(100 - (combo.cost_month / def.cost_month) * 100).toFixed(0) + '%')}
          </div>

          <p style={{ margin: '8px 0 0', fontSize: 13, opacity: 0.85 }}>{data.note}</p>
        </div>
      )}
    </div>
  );
}

/**
 * LatencyExplorer — an ICAP demo for guide-3 Chapter 2 (latency anatomy).
 *
 * One 8B-class served model under a seeded Poisson load. Three levers (offered
 * load qps, serving slots = batch width, answer length) over a grid whose every
 * cell's latency distribution is precomputed by mini_prod.simulate_queue; the SLA
 * is p99 <= 2s. Predict-before-reveal: from the broken promo default (6 qps, 2
 * slots, 200-token answers) commit to the single lever that rescues p99. The
 * capacity gauge (offered load vs slots / service_ms) is *why* it works: a load
 * spike is a queue, not a slower model.
 */
import { useState } from 'preact/hooks';

type Combo = {
  qps: number; servers: number; output: number;
  service_ms: number; capacity_qps: number; overloaded: boolean;
  p50: number; p95: number; p99: number; max: number; sla_ok: boolean;
};
type Data = {
  name: string; note: string; sla_ms: number; seconds: number;
  params_b: number; input_tokens: number;
  levers: { qps: number[]; servers: number[]; output: number[] };
  defaults: { qps: number; servers: number; output: number };
  combos: Combo[];
};

const fmtMs = (x: number) =>
  x >= 10000 ? Math.round(x / 1000).toLocaleString() + 's' : Math.round(x).toLocaleString() + 'ms';

export default function LatencyExplorer({ data }: { data: Data }) {
  const [revealed, setRevealed] = useState(false);
  const [qps, setQps] = useState(data.defaults.qps);
  const [servers, setServers] = useState(data.defaults.servers);
  const [output, setOutput] = useState(data.defaults.output);

  const find = (q: number, s: number, o: number) =>
    data.combos.find((c) => c.qps === q && c.servers === s && c.output === o)!;
  const combo = find(qps, servers, output);
  const def = find(data.defaults.qps, data.defaults.servers, data.defaults.output);
  const loadPct = Math.min(100, (combo.qps / combo.capacity_qps) * 100);

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });
  const lever = (label: string, children: any) => (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexWrap: 'wrap', margin: '4px 0' }}>
      <span style={{ fontSize: 12, opacity: 0.7, minWidth: 130 }}>{label}</span>
      {children}
    </div>
  );
  const metric = (label: string, val: string, accent?: string) => (
    <div style={{ padding: '6px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)', minWidth: 92 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: accent ?? 'inherit' }}>{val}</div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Latency under load</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          8B-class model · SLA: p99 ≤ {data.sla_ms / 1000}s · {data.seconds}s simulated
        </span>
      </div>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '10px 0' }}>
            <strong>Predict first:</strong> a promo has 6×'d traffic to {data.defaults.qps} qps.
            On {data.defaults.servers} serving slots with {data.defaults.output}-token answers, p99
            is <strong>{fmtMs(def.p99)}</strong> — the SLA is 2s. Which <em>single</em> lever
            rescues p99: more serving slots, shorter answers, or less traffic?
          </p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed(true)}>
            Reveal the levers
          </button>
        </div>
      ) : (
        <div>
          {lever('offered load', data.levers.qps.map((q) => (
            <button key={q} style={btn(q === qps)} onClick={() => setQps(q)}>{q} qps</button>
          )))}
          {lever('serving slots (batch)', data.levers.servers.map((s) => (
            <button key={s} style={btn(s === servers)} onClick={() => setServers(s)}>{s}</button>
          )))}
          {lever('answer length', data.levers.output.map((o) => (
            <button key={o} style={btn(o === output)} onClick={() => setOutput(o)}>{o} tok</button>
          )))}

          <div style={{ margin: '12px 0 6px' }}>
            <div style={{ fontSize: 12, opacity: 0.7, marginBottom: 3 }}>
              offered {combo.qps} qps vs capacity {combo.capacity_qps} qps (= slots ÷ {combo.service_ms}ms service)
              {combo.overloaded && <strong style={{ color: '#dc2626' }}> — overloaded, queue grows without bound</strong>}
            </div>
            <div style={{ display: 'flex', height: 16, borderRadius: 5, overflow: 'hidden', border: '1px solid var(--color-border,#ddd)', background: 'var(--color-bg-subtle,#f0f0f0)' }}>
              <div style={{ width: `${loadPct}%`, background: combo.overloaded ? '#fca5a5' : '#86efac' }} title="offered load ÷ capacity" />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
            {metric('p50', fmtMs(combo.p50))}
            {metric('p95', fmtMs(combo.p95))}
            {metric('p99', fmtMs(combo.p99), combo.sla_ok ? '#16a34a' : '#dc2626')}
            {metric('SLA (p99 ≤ 2s)', combo.sla_ok ? 'PASS' : 'MISS', combo.sla_ok ? '#16a34a' : '#dc2626')}
          </div>

          <p style={{ margin: '8px 0 0', fontSize: 13, opacity: 0.85 }}>{data.note}</p>
        </div>
      )}
    </div>
  );
}

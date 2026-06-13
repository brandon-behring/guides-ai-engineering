/**
 * SpanWaterfallExplorer — an ICAP demo for guide-3 Chapter 5 (the observability stack).
 *
 * One support-bot request rendered as a span waterfall (precomputed by mini_prod.trace):
 * each span a bar positioned by its start offset and sized by duration, nested by depth,
 * colored by stage. Below it, the self-time rollup by stage — where the work actually
 * happened. Predict-before-reveal: commit to which stage owns the request's time before
 * the waterfall shows it. The point a trace makes that a metric can't: the 868ms total
 * is one number; the trace says *which stage* to optimize.
 */
import { useState } from 'preact/hooks';

type Row = {
  name: string; start_ms: number; duration_ms: number;
  self_ms: number; depth: number; stage: string;
};
type Roll = { stage: string; ms: number; pct: number };
type Data = {
  name: string; note: string; total_ms: number;
  rows: Row[]; rollup: Roll[]; slowest: { name: string; self_ms: number };
};

const STAGE_COLOR: Record<string, string> = {
  request: '#cbd5e1', retrieve: '#93c5fd', generate: '#fca5a5',
};
const colorFor = (stage: string) => STAGE_COLOR[stage] ?? '#a7f3d0';

export default function SpanWaterfallExplorer({ data }: { data: Data }) {
  const [revealed, setRevealed] = useState(false);
  const T = data.total_ms;

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Request trace — span waterfall</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>total {data.total_ms} ms</span>
      </div>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '10px 0' }}>
            <strong>Predict first:</strong> this one request took {data.total_ms} ms across
            retrieve (embed → search → rerank) and generate. Which stage owns most of the
            time — and within retrieve, which step?
          </p>
          <button
            style={{ padding: '6px 14px', borderRadius: 6, cursor: 'pointer', fontSize: 13, border: '1px solid var(--color-border,#ccc)', background: 'var(--color-accent,#6366f1)', color: 'white' }}
            onClick={() => setRevealed(true)}
          >
            Reveal the waterfall
          </button>
        </div>
      ) : (
        <div>
          {/* waterfall */}
          <div style={{ margin: '12px 0' }}>
            {data.rows.map((r) => (
              <div key={r.name} style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '3px 0' }}>
                <span style={{ minWidth: 150, fontSize: 12, paddingLeft: r.depth * 14, fontVariantNumeric: 'tabular-nums', opacity: r.depth === 0 ? 1 : 0.85 }}>
                  {r.name}
                </span>
                <div style={{ position: 'relative', flex: 1, height: 18, background: 'var(--color-bg-subtle,#f3f4f6)', borderRadius: 4 }}>
                  <div
                    title={`${r.name}: ${r.duration_ms}ms (self ${r.self_ms}ms)`}
                    style={{
                      position: 'absolute', left: `${(r.start_ms / T) * 100}%`,
                      width: `${Math.max(1, (r.duration_ms / T) * 100)}%`,
                      height: '100%', background: colorFor(r.stage), borderRadius: 4,
                    }}
                  />
                </div>
                <span style={{ minWidth: 56, textAlign: 'right', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{r.duration_ms}ms</span>
              </div>
            ))}
          </div>

          {/* self-time rollup by stage */}
          <div style={{ fontSize: 12, opacity: 0.7, margin: '10px 0 4px' }}>self-time by stage (where the work happened)</div>
          {data.rollup.map((r) => (
            <div key={r.stage} style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '3px 0' }}>
              <span style={{ minWidth: 90, fontSize: 12 }}>{r.stage}</span>
              <div style={{ flex: 1, height: 16, background: 'var(--color-bg-subtle,#f3f4f6)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${r.pct}%`, height: '100%', background: colorFor(r.stage) }} />
              </div>
              <span style={{ minWidth: 78, textAlign: 'right', fontSize: 12, fontVariantNumeric: 'tabular-nums' }}>{r.ms}ms · {r.pct}%</span>
            </div>
          ))}

          <p style={{ margin: '10px 0 0', fontSize: 13 }}>
            <strong>Slowest span:</strong> <code>{data.slowest.name}</code> at {data.slowest.self_ms}ms
            of self-time — the one place worth optimizing first.
          </p>
          <p style={{ margin: '6px 0 0', fontSize: 13, opacity: 0.85 }}>{data.note}</p>
        </div>
      )}
    </div>
  );
}

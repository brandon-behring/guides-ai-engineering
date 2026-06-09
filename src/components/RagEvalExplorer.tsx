/**
 * RagEvalExplorer — an ICAP demo for Chapter 9 (RAG evaluation).
 *
 * Two halves of a RAG eval, precomputed (dump -> JSON -> island; retrieval metrics
 * from mini_eval.retrieval, grounding labels authored):
 *  1. "Retrieval" — drag k and watch which top-k chunks are relevant, with
 *     precision@k / recall@k / NDCG@k moving (the precision–recall tension over k).
 *  2. "Faithfulness" — the generated answer split into claims, each grounded or not
 *     in the retrieved context; the unsupported one is a Type-I hallucination.
 * Predict/explain prompts live in the chapter prose.
 */
import { useState } from 'preact/hooks';

type Chunk = { rank: number; id: string; relevant: boolean; snippet: string };
type SweepRow = { k: number; precision: number; recall: number; ndcg: number };
type Claim = { text: string; supported: boolean; note: string };
type Data = {
  name: string; note: string;
  retrieval: { query: string; n_relevant: number; chunks: Chunk[]; sweep: SweepRow[] };
  faithfulness: { answer: string; claims: Claim[]; score: number; note: string };
};

const pct = (x: number) => (x * 100).toFixed(0) + '%';

export default function RagEvalExplorer({ data }: { data: Data }) {
  const [tab, setTab] = useState<'retrieval' | 'faithfulness'>('retrieval');
  const chunks = data.retrieval.chunks;
  const [k, setK] = useState(3);
  const row = data.retrieval.sweep[k - 1];

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });
  const metric = (label: string, val: string) => (
    <div style={{ padding: '6px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)', minWidth: 92 }}>
      <div style={{ fontSize: 11, opacity: 0.7 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{val}</div>
    </div>
  );

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>RAG eval explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>query: “{data.retrieval.query}”</span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0' }}>
        <button style={btn(tab === 'retrieval')} onClick={() => setTab('retrieval')}>Retrieval</button>
        <button style={btn(tab === 'faithfulness')} onClick={() => setTab('faithfulness')}>Faithfulness</button>
      </div>

      {tab === 'retrieval' ? (
        <div>
          <label style={{ display: 'block', margin: '6px 0 4px' }}>
            Cutoff k = <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{k}</strong> — score the top {k} of {chunks.length} retrieved ({data.retrieval.n_relevant} are relevant)
          </label>
          <input type="range" min={1} max={chunks.length} step={1} value={k}
            onInput={(e) => setK(parseInt((e.target as HTMLInputElement).value))}
            style={{ width: '100%' }} aria-label="retrieval cutoff k" />
          <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
            {metric('Precision@k', pct(row.precision))}
            {metric('Recall@k', pct(row.recall))}
            {metric('NDCG@k', row.ndcg.toFixed(3))}
          </div>
          <ol style={{ margin: '6px 0 0', paddingLeft: 22 }}>
            {chunks.map((c) => {
              const inK = c.rank <= k;
              return (
                <li key={c.id} style={{
                  margin: '3px 0', padding: '3px 8px', borderRadius: 5, fontSize: 13,
                  background: inK ? (c.relevant ? '#dcfce7' : '#fee2e2') : 'transparent',
                  opacity: inK ? 1 : 0.45,
                }}>
                  {c.relevant ? '✓ ' : '· '}{c.snippet}
                </li>
              );
            })}
          </ol>
        </div>
      ) : (
        <div>
          <p style={{ fontSize: 13, opacity: 0.8, margin: '2px 0 8px' }}>Generated answer, split into atomic claims — each checked against the retrieved context:</p>
          {data.faithfulness.claims.map((c, i) => (
            <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', margin: '6px 0', padding: '6px 8px', borderRadius: 6, background: c.supported ? '#dcfce7' : '#fee2e2' }}>
              <span style={{ fontWeight: 700, color: c.supported ? '#16a34a' : '#dc2626' }}>{c.supported ? '✓' : '✗'}</span>
              <span>{c.text} <span style={{ opacity: 0.6, fontSize: 12 }}>— {c.note}</span></span>
            </div>
          ))}
          <p style={{ margin: '10px 0 0', fontSize: 14 }}>
            Faithfulness = grounded claims / total = <strong>{pct(data.faithfulness.score)}</strong>.{' '}
            <span style={{ opacity: 0.8 }}>{data.faithfulness.note}</span>
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * RetrievalExplorer — an ICAP demo for guide-2 Chapter 2 (Retrieval 101).
 *
 * One TF-IDF index over a 10-doc support corpus, four queries with four lessons
 * (exact-vocabulary success, paraphrase zero-hit, stopword junk tail, morphology
 * miss). Predict-before-reveal per query: the reader commits to a guess about
 * which document ranks first, then reveals the computed ranking and slides k to
 * watch precision@k / recall@k move. All rankings precomputed offline by
 * mini_rag (dump -> JSON -> island; no model, no server).
 */
import { useState } from 'preact/hooks';

type Doc = { id: string; text: string };
type Hit = { id: string; score: number; relevant: boolean };
type SweepRow = { k: number; precision: number; recall: number };
type Query = {
  label: string; query: string; relevant: string[]; lesson: string;
  hits: Hit[]; sweep: SweepRow[];
};
type Data = { name: string; note: string; corpus: Doc[]; queries: Query[] };

const pct = (x: number) => (x * 100).toFixed(0) + '%';

export default function RetrievalExplorer({ data }: { data: Data }) {
  const [qi, setQi] = useState(0);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [k, setK] = useState(3);

  const q = data.queries[qi];
  const isRevealed = !!revealed[qi];
  const maxK = Math.max(1, q.hits.length);
  const kEff = Math.min(k, maxK);
  const row = q.sweep[kEff - 1];
  const docText = (id: string) => data.corpus.find((d) => d.id === id)?.text ?? id;
  const missed = q.relevant.filter((id) => !q.hits.slice(0, kEff).some((h) => h.id === id));

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
        <strong>Retrieval explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.queries.length} queries · one TF-IDF index · {data.corpus.length} documents</span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0', flexWrap: 'wrap' }}>
        {data.queries.map((qq, i) => (
          <button key={qq.label} style={btn(i === qi)} onClick={() => { setQi(i); setK(3); }}>{qq.label}</button>
        ))}
      </div>

      <p style={{ margin: '6px 0' }}>
        Query: <strong>“{q.query}”</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}> — ground truth: {q.relevant.length} relevant document{q.relevant.length > 1 ? 's' : ''}</span>
      </p>

      {!isRevealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '8px 0' }}>
            <strong>Predict first:</strong> which document ranks #1 — and how many match at all?
            (Remember: TF-IDF only sees shared tokens.)
          </p>
          <ul style={{ margin: '6px 0 10px', paddingLeft: 20, fontSize: 13, opacity: 0.85 }}>
            {data.corpus.map((d) => (
              <li key={d.id} style={{ margin: '2px 0' }}><code style={{ fontSize: 12 }}>{d.id}</code> {d.text}</li>
            ))}
          </ul>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed({ ...revealed, [qi]: true })}>
            Reveal the ranking
          </button>
        </div>
      ) : q.hits.length === 0 ? (
        <div>
          <div style={{ padding: '10px 12px', borderRadius: 8, background: '#fee2e2', margin: '8px 0', fontWeight: 600 }}>
            0 documents matched — every TF-IDF score is 0.
          </div>
          <p style={{ fontSize: 13, margin: '6px 0' }}>The documents that <em>should</em> have been retrieved:</p>
          {q.relevant.map((id) => (
            <div key={id} style={{ margin: '4px 0', padding: '4px 8px', borderRadius: 5, background: 'var(--color-bg-subtle,#f6f6f6)', fontSize: 13 }}>
              <code style={{ fontSize: 12 }}>{id}</code> {docText(id)}
            </div>
          ))}
          <p style={{ margin: '10px 0 0', fontSize: 13 }}><strong>Why:</strong> {q.lesson}</p>
        </div>
      ) : (
        <div>
          <label style={{ display: 'block', margin: '6px 0 4px' }}>
            Keep the top k = <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{kEff}</strong> of {q.hits.length} hit{q.hits.length > 1 ? 's' : ''} (only documents with score &gt; 0 are returned)
          </label>
          <input type="range" min={1} max={maxK} step={1} value={kEff}
            onInput={(e) => setK(parseInt((e.target as HTMLInputElement).value))}
            style={{ width: '100%' }} aria-label="retrieval cutoff k" />
          <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
            {metric('Precision@k', pct(row.precision))}
            {metric('Recall@k', pct(row.recall))}
          </div>
          <ol style={{ margin: '6px 0 0', paddingLeft: 22 }}>
            {q.hits.map((h, i) => {
              const inK = i < kEff;
              return (
                <li key={h.id} style={{
                  margin: '3px 0', padding: '3px 8px', borderRadius: 5, fontSize: 13,
                  background: inK ? (h.relevant ? '#dcfce7' : '#fee2e2') : 'transparent',
                  opacity: inK ? 1 : 0.45,
                }}>
                  {h.relevant ? '✓ ' : '✗ '}<code style={{ fontSize: 12 }}>{h.id}</code> {docText(h.id)}
                  <span style={{ opacity: 0.6, fontSize: 12, fontVariantNumeric: 'tabular-nums' }}> — cos {h.score.toFixed(3)}</span>
                </li>
              );
            })}
          </ol>
          {missed.length > 0 && (
            <p style={{ margin: '8px 0 0', fontSize: 13 }}>
              <strong>Missed:</strong>{' '}
              {missed.map((id) => <span key={id}><code style={{ fontSize: 12 }}>{id}</code> ({docText(id)}) </span>)}
              — relevant, but outside the top {kEff}{q.hits.every((h) => h.id !== missed[0]) ? ' (never retrieved at all)' : ''}.
            </p>
          )}
          <p style={{ margin: '10px 0 0', fontSize: 13 }}><strong>Lesson:</strong> {q.lesson}</p>
        </div>
      )}
    </div>
  );
}

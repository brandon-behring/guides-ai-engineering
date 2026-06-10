/**
 * RagPipelineExplorer — an ICAP demo for guide-2 Chapter 4 (RAG end-to-end).
 *
 * Three scenarios over the same paragraph-chunked policy doc, each a real
 * mini_rag RagPipeline.run() precomputed offline: a happy path, a retrieval
 * failure (junk stopword hits vs a similarity floor), and a context-window
 * failure (the answer retrieved at rank #3, then excluded by the word budget).
 * Predict-before-reveal per scenario; variants toggle the knob that matters
 * (floor / budget). The full grounded prompt is inspectable — the trace is
 * the debugging surface.
 */
import { useState } from 'preact/hooks';

type HitRow = { chunk: number; score: number; status: 'included' | 'excluded' | 'floored' };
type Variant = {
  label: string; k: number; budget: number; floor: number;
  hits: HitRow[]; prompt: string;
  answer: { text: string; supported: boolean; source_chunk: number };
  verdict: string;
};
type Scenario = { key: string; label: string; question: string; predict: string; variants: Variant[] };
type ChunkRow = { id: number; words: number; text: string };
type Data = { name: string; note: string; chunks: ChunkRow[]; scenarios: Scenario[] };

const STATUS: Record<HitRow['status'], { bg: string; note: string }> = {
  included: { bg: '#dcfce7', note: 'in context' },
  excluded: { bg: '#fee2e2', note: 'over budget — never reaches the model' },
  floored: { bg: '#fef9c3', note: 'below the similarity floor — filtered' },
};

export default function RagPipelineExplorer({ data }: { data: Data }) {
  const [si, setSi] = useState(0);
  const [vi, setVi] = useState(0);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [showPrompt, setShowPrompt] = useState(false);

  const sc = data.scenarios[si];
  const v = sc.variants[Math.min(vi, sc.variants.length - 1)];
  const chunkText = (id: number) => data.chunks.find((c) => c.id === id)?.text ?? '';

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>RAG pipeline explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>{data.chunks.length} chunks · real pipeline traces</span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0', flexWrap: 'wrap' }}>
        {data.scenarios.map((s, i) => (
          <button key={s.key} style={btn(i === si)} onClick={() => { setSi(i); setVi(0); setShowPrompt(false); }}>
            {s.label}
          </button>
        ))}
      </div>

      <p style={{ margin: '6px 0' }}>Question: <strong>“{sc.question}”</strong></p>

      {!revealed[si] ? (
        <div>
          <p style={{ fontSize: 13, margin: '8px 0' }}><strong>Predict first:</strong> {sc.predict}</p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed({ ...revealed, [si]: true })}>
            Reveal the trace
          </button>
        </div>
      ) : (
        <div>
          {sc.variants.length > 1 && (
            <div style={{ display: 'flex', gap: 4, margin: '8px 0', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ fontSize: 12, opacity: 0.7 }}>toggle the knob:</span>
              {sc.variants.map((vv, i) => (
                <button key={vv.label} style={btn(i === vi)} onClick={() => { setVi(i); setShowPrompt(false); }}>{vv.label}</button>
              ))}
            </div>
          )}

          <div style={{ fontSize: 12, opacity: 0.75, margin: '8px 0 4px' }}>
            ① Retrieve (k={v.k}{v.floor > 0 ? `, floor ${v.floor}` : ''}) → ② Assemble (budget {v.budget} words) → ③ Grounded prompt → ④ Answer
          </div>

          {v.hits.length === 0 ? (
            <div style={{ padding: '8px 10px', borderRadius: 6, background: '#fee2e2', fontSize: 13 }}>
              0 chunks retrieved.
            </div>
          ) : (
            <ol style={{ margin: '4px 0', paddingLeft: 22 }}>
              {v.hits.map((h) => (
                <li key={h.chunk} style={{
                  margin: '3px 0', padding: '4px 8px', borderRadius: 5, fontSize: 13,
                  background: STATUS[h.status].bg,
                  opacity: h.status === 'included' ? 1 : 0.8,
                }}>
                  <span style={{ fontVariantNumeric: 'tabular-nums' }}>cos {h.score.toFixed(3)}</span>
                  {' — '}{chunkText(h.chunk).slice(0, 90)}…
                  <span style={{ fontSize: 11, opacity: 0.7 }}> [{STATUS[h.status].note}]</span>
                </li>
              ))}
            </ol>
          )}

          <button style={{ ...btn(showPrompt), margin: '6px 0' }} onClick={() => setShowPrompt(!showPrompt)}>
            {showPrompt ? 'hide' : 'show'} the exact prompt
          </button>
          {showPrompt && (
            <pre style={{
              fontSize: 11.5, lineHeight: 1.45, padding: 10, borderRadius: 6, overflowX: 'auto',
              background: 'var(--color-bg-subtle,#f6f6f6)', whiteSpace: 'pre-wrap',
            }}>{v.prompt}</pre>
          )}

          <div style={{
            margin: '8px 0', padding: '8px 10px', borderRadius: 6,
            background: v.answer.supported ? '#dcfce7' : '#fef9c3',
          }}>
            <div style={{ fontSize: 11, opacity: 0.7 }}>
              answer{v.answer.supported ? ` — quoted from chunk ${v.answer.source_chunk + 1}` : ' — abstained'}
            </div>
            <div style={{ fontSize: 14 }}>{v.answer.text}</div>
          </div>

          <p style={{ margin: '8px 0 0', fontSize: 13 }}><strong>Verdict:</strong> {v.verdict}</p>
        </div>
      )}
    </div>
  );
}

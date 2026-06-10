/**
 * ChunkingExplorer — an ICAP demo for guide-2 Chapter 3 (Chunking).
 *
 * One refund-policy document, one question, a strategy × size grid (12 configs).
 * For each config: the actual chunks (cut by mini_rag.chunk), boundary
 * coherence, and a retrieval check computed by mini_rag.search — does the
 * top-ranked chunk still contain the 30-day limit, or did the cut orphan it?
 * Predict-before-reveal: the reader commits to which configs break the fact,
 * then explores. All data precomputed offline (dump -> JSON -> island).
 */
import { useState } from 'preact/hooks';

type Chunk = { text: string; has_request: boolean; has_limit: boolean; is_top: boolean };
type Combo = {
  strategy: string; size: number; n_chunks: number; avg_words: number;
  coherence: number; top_index: number; fact_intact: boolean; chunks: Chunk[];
};
type Data = {
  name: string; note: string; query: string; fact: string; limit_phrase: string;
  strategies: { key: string; label: string }[]; sizes: number[]; combos: Combo[];
};

export default function ChunkingExplorer({ data }: { data: Data }) {
  const [strategy, setStrategy] = useState(data.strategies[0].key);
  const [size, setSize] = useState(data.sizes[0]);
  const [revealed, setRevealed] = useState(false);

  const combo = data.combos.find((c) => c.strategy === strategy && c.size === size)!;

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
        <strong>Chunking explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>question: “{data.query}”</span>
      </div>
      <p style={{ fontSize: 13, margin: '8px 0 4px' }}>
        The answer lives in one sentence: <em>“{data.fact}…”</em>. Cut the document, retrieve the
        top chunk for the question, and check: did <strong>“{data.limit_phrase}”</strong> survive in it?
      </p>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '8px 0' }}>
            <strong>Predict first:</strong> of the four strategies — fixed, fixed + overlap, sentence
            packing, paragraph packing — which ones break the fact at <em>some</em> size? Commit to a
            guess, then explore the grid.
          </p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed(true)}>
            Reveal the grid
          </button>
        </div>
      ) : (
        <div>
          <div style={{ display: 'flex', gap: 4, margin: '10px 0 6px', flexWrap: 'wrap' }}>
            {data.strategies.map((s) => (
              <button key={s.key} style={btn(s.key === strategy)} onClick={() => setStrategy(s.key)}>{s.label}</button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 4, margin: '0 0 10px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{ fontSize: 12, opacity: 0.7 }}>target size (words):</span>
            {data.sizes.map((s) => (
              <button key={s} style={btn(s === size)} onClick={() => setSize(s)}>{s}</button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 8, margin: '10px 0', flexWrap: 'wrap' }}>
            {metric('Chunks', String(combo.n_chunks))}
            {metric('Avg words', String(combo.avg_words))}
            {metric('Boundary coherence', (combo.coherence * 100).toFixed(0) + '%')}
            <div style={{
              padding: '6px 10px', borderRadius: 6, minWidth: 140,
              background: combo.fact_intact ? '#dcfce7' : '#fee2e2',
            }}>
              <div style={{ fontSize: 11, opacity: 0.7 }}>Top chunk has “{data.limit_phrase}”?</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: combo.fact_intact ? '#16a34a' : '#dc2626' }}>
                {combo.fact_intact ? 'fact intact' : 'fact broken'}
              </div>
            </div>
          </div>

          <div>
            {combo.chunks.map((c, i) => (
              <div key={i} style={{
                margin: '6px 0', padding: '6px 9px', borderRadius: 6, fontSize: 13, lineHeight: 1.45,
                border: c.is_top ? '2px solid var(--color-accent,#6366f1)' : '1px solid var(--color-border,#e5e5e5)',
                background: c.has_limit ? '#dcfce7' : c.has_request ? '#fef9c3' : 'var(--color-bg-subtle,#fafafa)',
              }}>
                <div style={{ fontSize: 11, opacity: 0.75, marginBottom: 2 }}>
                  chunk {i + 1}{c.is_top ? ' — retrieved #1 for the question' : ''}
                  {c.has_request && !c.has_limit ? ' — has “request a refund” but NOT the limit' : ''}
                  {c.has_limit ? ` — contains “${data.limit_phrase}”` : ''}
                </div>
                {c.text}
              </div>
            ))}
          </div>

          <p style={{ margin: '10px 0 0', fontSize: 13 }}>
            {combo.fact_intact ? (
              <span><strong>Intact:</strong> the retrieved chunk carries the limit. {combo.coherence === 1
                ? 'Boundaries fell on sentence ends, so no fact could be cut.'
                : 'This config got lucky — the cut happened to miss the fact. Luck is not a strategy: change the size and watch.'}</span>
            ) : (
              <span><strong>Broken:</strong> the cut split “request a refund” from “{data.limit_phrase}”
                {combo.strategy === 'fixed_overlap'
                  ? ' — and even with overlap, the refund-heavy run-up chunk outranks the one carrying the limit. Overlap is mitigation, not a guarantee.'
                  : ', so the top-ranked chunk tells the generator a refund exists but not its deadline. No embedding model can repair this — the cut happened before any vector was computed.'}</span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

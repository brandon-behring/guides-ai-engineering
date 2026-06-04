/**
 * JudgeBiasExplorer — an ICAP demo for Chapter 7 (LLM-as-judge).
 *
 * Reads precomputed judge verdicts (dump -> JSON -> island; no live LLM) for a
 * handful of pairs where the *shorter* answer is the *better* one. Toggle the
 * presentation order to watch the naive judge's verdict flip on the close pair
 * (position bias); flip on "debias" to see the swap-and-require-agreement
 * mitigation turn that flip into an honest "tie". Predict/explain prompts live
 * in the chapter prose.
 */
import { useState } from 'preact/hooks';

type Resp = { id: string; text: string; quality: number; len: number };
type Pair = {
  label: string; a: Resp; b: Resp; truth: string;
  position: { order_ab: string; order_ba: string; debiased: string };
  verbosity: { order_ab: string };
};
type Data = { pairs: Pair[]; position_flip_rate: number; note: string };

export default function JudgeBiasExplorer({ data }: { data: Data }) {
  const [order, setOrder] = useState<'ab' | 'ba'>('ab');
  const [debiased, setDebiased] = useState(false);

  const verdictOf = (p: Pair): string =>
    debiased ? p.position.debiased : order === 'ab' ? p.position.order_ab : p.position.order_ba;

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <strong>LLM-as-judge: bias explorer</strong>
      <p style={{ margin: '6px 0', opacity: 0.8 }}>
        In every pair, <strong>A is the better answer</strong> (higher latent quality) but is <em>shorter</em>. The judge has a mild position bias. Watch its verdict.
      </p>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center', margin: '10px 0' }}>
        <span>Presentation order:</span>
        <div style={{ display: 'flex', gap: 4 }}>
          <button style={btn(order === 'ab' && !debiased)} disabled={debiased} onClick={() => setOrder('ab')}>A first, B second</button>
          <button style={btn(order === 'ba' && !debiased)} disabled={debiased} onClick={() => setOrder('ba')}>B first, A second</button>
        </div>
        <label style={{ marginLeft: 'auto', cursor: 'pointer' }}>
          <input type="checkbox" checked={debiased} onChange={(e) => setDebiased((e.target as HTMLInputElement).checked)} />{' '}
          Debias (judge both orders, require agreement)
        </label>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ textAlign: 'left', opacity: 0.7 }}>
            <th style={{ padding: 4 }}>A (better, shorter)</th>
            <th style={{ padding: 4 }}>B (worse, longer)</th>
            <th style={{ padding: 4 }}>Verdict</th>
          </tr>
        </thead>
        <tbody>
          {data.pairs.map((p) => {
            const v = verdictOf(p);
            const correct = v === p.truth;
            const tie = v === 'tie';
            return (
              <tr style={{ borderTop: '1px solid var(--color-border,#eee)' }}>
                <td style={{ padding: 4 }}>{p.a.text} <span style={{ opacity: 0.5 }}>(q={p.a.quality}, {p.a.len} ch)</span></td>
                <td style={{ padding: 4 }}>{p.b.text} <span style={{ opacity: 0.5 }}>(q={p.b.quality}, {p.b.len} ch)</span></td>
                <td style={{ padding: 4, fontWeight: 600, color: tie ? '#a16207' : correct ? '#16a34a' : '#dc2626' }}>
                  {tie ? 'tie (caught it)' : `${v === p.a.id ? 'A' : 'B'} wins`} {tie ? '⚖' : correct ? '✓' : '✗ wrong'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p style={{ margin: '10px 0 0', fontSize: 13, opacity: 0.8 }}>
        Naive position-flip rate across these pairs: <strong>{(data.position_flip_rate * 100).toFixed(0)}%</strong> — the close pair's verdict depends on <em>order</em>, not quality. Verbosity bias is just as easy to provoke: under a length bonus the judge prefers <strong>B</strong> (the longer, worse answer) on the first pair.
      </p>
    </div>
  );
}

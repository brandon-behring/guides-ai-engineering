/**
 * PipelineCompareExplorer — an ICAP demo for guide-2 Chapter 5 (Evaluating RAG).
 *
 * Two pipeline configs (A "ship-it" vs B "hardened") judged on one six-question
 * golden set — every cell a real mini_rag RagPipeline.run(), categorized against
 * authored ground truth and mapped to Chapter 4's failure points; context recall
 * via mini_eval.recall_at_k. Predict-before-reveal: commit to which config wins
 * (and where both lose) before seeing the table. Expand a row for the actual
 * answers and the per-config failure reason.
 */
import { useState } from 'preact/hooks';

type Run = {
  outcome: string; why: string; answer: string; supported: boolean;
  included: number[]; context_recall: number | null;
};
type QuestionRow = { q: string; relevant: number[]; fact: string | null; note: string; runs: Record<string, Run> };
type Config = { key: string; label: string; detail: string };
type Agg = { correct: number; harmful: number; safe_abstain: number; missed_abstain: number; avg_context_recall: number };
type Data = {
  name: string; note: string; predict: string; verdict: string;
  chunks: { id: number; text: string }[];
  configs: Config[]; questions: QuestionRow[]; aggregates: Record<string, Agg>;
};

const OUTCOME: Record<string, { label: string; bg: string; fg: string }> = {
  'correct': { label: 'correct', bg: '#dcfce7', fg: '#16a34a' },
  'junk': { label: 'junk answer', bg: '#fee2e2', fg: '#dc2626' },
  'retrieval-miss': { label: 'retrieval miss', bg: '#fee2e2', fg: '#dc2626' },
  'lost-in-assembly': { label: 'lost in assembly', bg: '#fee2e2', fg: '#dc2626' },
  'extraction-miss': { label: 'answer-extraction miss', bg: '#fee2e2', fg: '#dc2626' },
  'abstain-safe': { label: 'abstained (safe)', bg: '#fef9c3', fg: '#a16207' },
  'abstain-unreachable': { label: 'abstained (unreachable)', bg: '#fef9c3', fg: '#a16207' },
  'abstain-missed': { label: 'abstained (missed)', bg: '#fee2e2', fg: '#dc2626' },
};

export default function PipelineCompareExplorer({ data }: { data: Data }) {
  const [revealed, setRevealed] = useState(false);
  const [open, setOpen] = useState<number | null>(null);

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });
  const chip = (outcome: string) => {
    const o = OUTCOME[outcome] ?? { label: outcome, bg: '#eee', fg: '#333' };
    return (
      <span style={{
        display: 'inline-block', padding: '2px 8px', borderRadius: 10, fontSize: 12,
        background: o.bg, color: o.fg, fontWeight: 600, whiteSpace: 'nowrap',
      }}>{o.label}</span>
    );
  };

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Config comparison — one golden set</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          {data.configs.map((c) => `${c.label} (${c.detail})`).join('  vs  ')}
        </span>
      </div>

      {!revealed ? (
        <div>
          <p style={{ fontSize: 13, margin: '10px 0' }}>
            <strong>Predict first:</strong> {data.predict}
          </p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed(true)}>
            Reveal the table
          </button>
        </div>
      ) : (
        <div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '2px solid var(--color-border,#ddd)', textAlign: 'left' }}>
                  <th style={{ padding: '6px 8px' }}>question</th>
                  {data.configs.map((c) => <th key={c.key} style={{ padding: '6px 8px' }}>{c.label}</th>)}
                </tr>
              </thead>
              <tbody>
                {data.questions.map((q, i) => (
                  <>
                    <tr key={q.q} style={{ borderBottom: '1px solid var(--color-border,#eee)', cursor: 'pointer' }}
                        onClick={() => setOpen(open === i ? null : i)}>
                      <td style={{ padding: '6px 8px' }}>
                        {q.q} <span style={{ opacity: 0.5, fontSize: 11 }}>{open === i ? '▾' : '▸'}</span>
                      </td>
                      {data.configs.map((c) => (
                        <td key={c.key} style={{ padding: '6px 8px' }}>{chip(q.runs[c.key].outcome)}</td>
                      ))}
                    </tr>
                    {open === i && (
                      <tr key={q.q + '-detail'} style={{ borderBottom: '1px solid var(--color-border,#eee)' }}>
                        <td colSpan={1 + data.configs.length} style={{ padding: '6px 12px', background: 'var(--color-bg-subtle,#fafafa)' }}>
                          {q.note && <p style={{ margin: '4px 0', fontSize: 12, opacity: 0.8 }}><em>{q.note}</em></p>}
                          {data.configs.map((c) => {
                            const r = q.runs[c.key];
                            return (
                              <p key={c.key} style={{ margin: '4px 0', fontSize: 12.5 }}>
                                <strong>{c.label}:</strong> “{r.answer}”
                                {r.why && <span style={{ opacity: 0.75 }}> — {r.why}</span>}
                                {r.context_recall !== null && (
                                  <span style={{ opacity: 0.6 }}> · context recall {r.context_recall}</span>
                                )}
                              </p>
                            );
                          })}
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: '2px solid var(--color-border,#ddd)', fontWeight: 600 }}>
                  <td style={{ padding: '6px 8px' }}>aggregate (of {data.questions.length})</td>
                  {data.configs.map((c) => {
                    const a = data.aggregates[c.key];
                    return (
                      <td key={c.key} style={{ padding: '6px 8px', fontSize: 12.5 }}>
                        {a.correct} correct · {a.harmful} harmful · {a.safe_abstain} safe abstain
                        <div style={{ fontWeight: 400, opacity: 0.7 }}>avg context recall {a.avg_context_recall}</div>
                      </td>
                    );
                  })}
                </tr>
              </tfoot>
            </table>
          </div>
          <p style={{ margin: '10px 0 0', fontSize: 13 }}><strong>Verdict:</strong> {data.verdict}</p>
        </div>
      )}
    </div>
  );
}

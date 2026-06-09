/**
 * MetricMatchExplorer — an ICAP demo for Chapter 1 (the evaluation mindset).
 *
 * For each system the reader predicts which metric matches how the output is
 * actually used, picks one, and then sees what the tempting wrong choices hide.
 * Pure committed JSON (src/data/mindset_demo.json) — no model, no computation;
 * the point is judgment, not arithmetic. Predict/explain prompts live in the prose.
 */
import { useState } from 'preact/hooks';

type System = {
  id: string; system: string; candidates: string[];
  correct: string; failure: string; why: string;
};
type Data = { name: string; note: string; systems: System[] };

export default function MetricMatchExplorer({ data }: { data: Data }) {
  const [picks, setPicks] = useState<Record<string, string>>({});

  const choose = (id: string, candidate: string) =>
    setPicks((prev) => (prev[id] ? prev : { ...prev, [id]: candidate }));

  const optStyle = (sys: System, c: string): any => {
    const picked = picks[sys.id];
    const isPick = picked === c;
    const isAnswer = c === sys.correct;
    let bg = 'transparent', border = 'var(--color-border,#ccc)', color = 'inherit';
    if (picked) {
      if (isAnswer) { bg = '#dcfce7'; border = '#16a34a'; }
      else if (isPick) { bg = '#fee2e2'; border = '#dc2626'; }
    }
    return {
      display: 'block', width: '100%', textAlign: 'left', margin: '4px 0',
      padding: '7px 10px', borderRadius: 6, fontSize: 13.5,
      cursor: picked ? 'default' : 'pointer',
      border: `1px solid ${border}`, background: bg, color,
    };
  };

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <strong>{data.name}</strong>
      <p style={{ margin: '6px 0 12px', opacity: 0.8, fontSize: 13 }}>{data.note}</p>

      {data.systems.map((sys) => {
        const picked = picks[sys.id];
        const right = picked === sys.correct;
        return (
          <div key={sys.id} style={{ borderTop: '1px solid var(--color-border,#eee)', paddingTop: 12, marginTop: 12 }}>
            <p style={{ margin: '0 0 8px' }}>{sys.system}</p>
            {sys.candidates.map((c) => (
              <button key={c} style={optStyle(sys, c)} disabled={!!picked} onClick={() => choose(sys.id, c)}>
                {picked && c === sys.correct ? '✓ ' : picked === c ? '✗ ' : ''}{c}
              </button>
            ))}
            {picked && (
              <div style={{ margin: '8px 0 2px', fontSize: 13, padding: '8px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)' }}>
                <span style={{ fontWeight: 600, color: right ? '#16a34a' : '#a16207' }}>
                  {right ? 'Matches the use. ' : 'Not the metric the use demands. '}
                </span>
                {sys.failure}
                <div style={{ marginTop: 6, opacity: 0.85 }}><em>{sys.why}</em></div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * ScenarioQuiz — a reusable "spot the issue" ICAP demo for the prose-heavy chapters
 * (Ch 8 benchmark literacy, Ch 5 data integrity, Ch 6 reference-based vs free).
 *
 * Pure committed JSON (no model): each item is a scenario, a set of candidate
 * diagnoses, the best one, and the explanation + principle revealed after the
 * reader commits. The reader predicts (picks), then sees why. Drive it with a
 * different src/data/*.json per chapter. Predict/explain framing lives in the prose.
 */
import { useState } from 'preact/hooks';

type Item = {
  id: string; prompt: string; candidates: string[];
  correct: string; explanation: string; principle: string;
};
type Data = { name: string; note: string; items: Item[] };

export default function ScenarioQuiz({ data }: { data: Data }) {
  const [picks, setPicks] = useState<Record<string, string>>({});
  const choose = (id: string, c: string) =>
    setPicks((prev) => (prev[id] ? prev : { ...prev, [id]: c }));

  const optStyle = (item: Item, c: string): any => {
    const picked = picks[item.id];
    const isPick = picked === c;
    const isAnswer = c === item.correct;
    let bg = 'transparent', border = 'var(--color-border,#ccc)';
    if (picked) {
      if (isAnswer) { bg = '#dcfce7'; border = '#16a34a'; }
      else if (isPick) { bg = '#fee2e2'; border = '#dc2626'; }
    }
    return {
      display: 'block', width: '100%', textAlign: 'left', margin: '4px 0',
      padding: '7px 10px', borderRadius: 6, fontSize: 13.5,
      cursor: picked ? 'default' : 'pointer',
      border: `1px solid ${border}`, background: bg, color: 'inherit',
    };
  };

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <strong>{data.name}</strong>
      <p style={{ margin: '6px 0 12px', opacity: 0.8, fontSize: 13 }}>{data.note}</p>

      {data.items.map((item) => {
        const picked = picks[item.id];
        const right = picked === item.correct;
        return (
          <div key={item.id} style={{ borderTop: '1px solid var(--color-border,#eee)', paddingTop: 12, marginTop: 12 }}>
            <p style={{ margin: '0 0 8px', fontStyle: 'italic' }}>“{item.prompt}”</p>
            {item.candidates.map((c) => (
              <button key={c} style={optStyle(item, c)} disabled={!!picked} onClick={() => choose(item.id, c)}>
                {picked && c === item.correct ? '✓ ' : picked === c ? '✗ ' : ''}{c}
              </button>
            ))}
            {picked && (
              <div style={{ margin: '8px 0 2px', fontSize: 13, padding: '8px 10px', borderRadius: 6, background: 'var(--color-bg-subtle,#f6f6f6)' }}>
                <span style={{ fontWeight: 600, color: right ? '#16a34a' : '#a16207' }}>
                  {right ? 'Right. ' : 'The sharper catch: '}
                </span>
                {item.explanation}
                <div style={{ marginTop: 6, opacity: 0.85 }}><em>{item.principle}</em></div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

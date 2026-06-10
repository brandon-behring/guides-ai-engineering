/**
 * AgentTraceExplorer — an ICAP demo for guide-2 Chapter 8 (Agents & tool use).
 *
 * Four frozen traces from mini_agent.run_agent (scripted policies — honest,
 * deterministic stand-ins for the LLM in the reasoning seat). Predict the
 * outcome per scenario, then step through the loop one turn at a time:
 * Thought → Action (write-tools badged) → Observation. Guards visible where
 * they fire (loop detection, unknown-tool observations).
 */
import { useState } from 'preact/hooks';

type StepRow = {
  n: number; thought: string; tool: string | null; args: string;
  writes: boolean; observation: string;
};
type Scenario = {
  key: string; label: string; goal: string; predict: string; lesson: string;
  status: string; answer: string; steps: StepRow[];
};
type ToolRow = { name: string; description: string; writes: boolean };
type Data = { name: string; note: string; tools: ToolRow[]; scenarios: Scenario[] };

export default function AgentTraceExplorer({ data }: { data: Data }) {
  const [si, setSi] = useState(0);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [shown, setShown] = useState(1);

  const sc = data.scenarios[si];
  const done = shown >= sc.steps.length;

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Agent trace explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          tools: {data.tools.map((t) => t.name + (t.writes ? ' ✍' : '')).join(' · ')}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0', flexWrap: 'wrap' }}>
        {data.scenarios.map((s, i) => (
          <button key={s.key} style={btn(i === si)} onClick={() => { setSi(i); setShown(1); }}>
            {s.label}
          </button>
        ))}
      </div>

      <p style={{ margin: '6px 0' }}>Goal: <strong>“{sc.goal}”</strong></p>

      {!revealed[si] ? (
        <div>
          <p style={{ fontSize: 13, margin: '8px 0' }}><strong>Predict first:</strong> {sc.predict}</p>
          <button style={{ ...btn(true), padding: '6px 14px' }}
            onClick={() => { setRevealed({ ...revealed, [si]: true }); setShown(1); }}>
            Step through the loop
          </button>
        </div>
      ) : (
        <div>
          {sc.steps.slice(0, shown).map((st) => (
            <div key={st.n} style={{
              margin: '8px 0', padding: '8px 10px', borderRadius: 8,
              border: '1px solid var(--color-border,#e5e5e5)',
              background: 'var(--color-bg-subtle,#fafafa)',
            }}>
              <div style={{ fontSize: 11, opacity: 0.6, marginBottom: 3 }}>step {st.n}</div>
              <div style={{ fontSize: 13, margin: '2px 0' }}>
                <span style={{ opacity: 0.6 }}>💭 thought:</span> {st.thought}
              </div>
              {st.tool ? (
                <div style={{ fontSize: 13, margin: '4px 0', fontFamily: 'monospace' }}>
                  <span style={{
                    padding: '1px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600,
                    background: st.writes ? '#fee2e2' : '#dbeafe',
                    color: st.writes ? '#dc2626' : '#1d4ed8',
                  }}>
                    {st.writes ? '✍ WRITE' : 'read'}
                  </span>{' '}
                  {st.tool}({st.args})
                </div>
              ) : (
                <div style={{ fontSize: 13, margin: '4px 0', fontWeight: 600 }}>■ finish</div>
              )}
              <div style={{
                fontSize: 13, margin: '4px 0 0', padding: '4px 8px', borderRadius: 5,
                background: st.observation.startsWith('Tool error') ? '#fef9c3'
                  : st.observation.includes('aborted') ? '#fee2e2' : '#fff',
                border: '1px dashed var(--color-border,#ddd)',
              }}>
                <span style={{ opacity: 0.6 }}>👁 observation:</span> {st.observation}
              </div>
            </div>
          ))}

          {!done ? (
            <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setShown(shown + 1)}>
              Next step ({shown}/{sc.steps.length})
            </button>
          ) : (
            <div>
              <div style={{
                margin: '8px 0', padding: '8px 10px', borderRadius: 6,
                background: sc.status === 'complete' ? '#dcfce7' : '#fee2e2',
              }}>
                <div style={{ fontSize: 11, opacity: 0.7 }}>status: {sc.status}</div>
                <div style={{ fontSize: 14 }}>{sc.answer}</div>
              </div>
              <p style={{ margin: '8px 0 0', fontSize: 13 }}><strong>Lesson:</strong> {sc.lesson}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

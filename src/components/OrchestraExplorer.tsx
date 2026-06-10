/**
 * OrchestraExplorer — an ICAP demo for guide-2 Chapter 9 (multi-agent).
 *
 * Two real run_supervisor traces (scripted router + policies): the triage day
 * and the sick day where the refund worker loops and the failure is isolated.
 * The supervisor's lane shows each handoff (thought → worker ← status);
 * expanding a handoff reveals the worker's inner loop — whose context
 * contains only its own ticket. Predict-before-reveal per scenario.
 */
import { useState } from 'preact/hooks';

type InnerStep = { thought: string; tool: string | null; args: string; observation: string };
type Handoff = {
  n: number; thought: string; worker: string; goal: string;
  worker_status: string; worker_answer: string; inner_steps: InnerStep[];
};
type Scenario = {
  key: string; label: string; task: string; predict: string; lesson: string;
  status: string; summary: string; handoffs: Handoff[];
};
type Data = {
  name: string; note: string;
  workers: { name: string; description: string; n_tools: number }[];
  scenarios: Scenario[];
};

export default function OrchestraExplorer({ data }: { data: Data }) {
  const [si, setSi] = useState(0);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [open, setOpen] = useState<number | null>(null);

  const sc = data.scenarios[si];

  const btn = (active: boolean): any => ({
    padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
    border: '1px solid var(--color-border,#ccc)',
    background: active ? 'var(--color-accent,#6366f1)' : 'transparent',
    color: active ? 'white' : 'inherit',
  });

  return (
    <div style={{ border: '1px solid var(--color-border,#ddd)', borderRadius: 10, padding: 16, margin: '1.25rem 0', fontSize: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
        <strong>Supervisor &amp; crew explorer</strong>
        <span style={{ opacity: 0.65, fontSize: 12 }}>
          crew: {data.workers.map((w) => `${w.name} (${w.n_tools} tool${w.n_tools === 1 ? '' : 's'})`).join(' · ')}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 4, margin: '10px 0', flexWrap: 'wrap' }}>
        {data.scenarios.map((s, i) => (
          <button key={s.key} style={btn(i === si)} onClick={() => { setSi(i); setOpen(null); }}>
            {s.label}
          </button>
        ))}
      </div>

      <p style={{ margin: '6px 0' }}>Task: <strong>{sc.task}</strong></p>

      {!revealed[si] ? (
        <div>
          <p style={{ fontSize: 13, margin: '8px 0' }}><strong>Predict first:</strong> {sc.predict}</p>
          <button style={{ ...btn(true), padding: '6px 14px' }} onClick={() => setRevealed({ ...revealed, [si]: true })}>
            Reveal the supervisor's lane
          </button>
        </div>
      ) : (
        <div>
          {sc.handoffs.map((h, i) => {
            const failed = h.worker_status !== 'complete';
            return (
              <div key={i} style={{
                margin: '8px 0', padding: '8px 10px', borderRadius: 8,
                border: `1px solid ${failed ? '#fca5a5' : 'var(--color-border,#e5e5e5)'}`,
                background: 'var(--color-bg-subtle,#fafafa)',
              }}>
                <div style={{ fontSize: 11, opacity: 0.6 }}>handoff {h.n}</div>
                <div style={{ fontSize: 13, margin: '2px 0' }}>
                  <span style={{ opacity: 0.6 }}>🧭 supervisor:</span> {h.thought}
                </div>
                <div style={{ fontSize: 13, margin: '4px 0' }}>
                  → <strong>{h.worker}</strong>
                  <span style={{
                    marginLeft: 8, padding: '1px 8px', borderRadius: 10, fontSize: 12, fontWeight: 600,
                    background: failed ? '#fee2e2' : '#dcfce7',
                    color: failed ? '#dc2626' : '#16a34a',
                  }}>{h.worker_status}</span>
                </div>
                <div style={{ fontSize: 12.5, opacity: 0.8, margin: '2px 0' }}>goal: “{h.goal}”</div>
                <div style={{ fontSize: 13, margin: '4px 0' }}>
                  <span style={{ opacity: 0.6 }}>↩ returned:</span> {h.worker_answer}
                </div>
                {h.inner_steps.length > 0 && (
                  <button style={{ ...btn(open === i), fontSize: 12, padding: '2px 8px' }}
                    onClick={() => setOpen(open === i ? null : i)}>
                    {open === i ? 'hide' : 'open'} the worker's inner loop ({h.inner_steps.length} steps)
                  </button>
                )}
                {open === i && h.inner_steps.map((s, j) => (
                  <div key={j} style={{
                    margin: '6px 0 0 14px', padding: '5px 8px', borderRadius: 6, fontSize: 12.5,
                    borderLeft: '3px solid var(--color-accent,#6366f1)', background: '#fff',
                  }}>
                    <div>💭 {s.thought}</div>
                    {s.tool && <div style={{ fontFamily: 'monospace' }}>⚙ {s.tool}({s.args})</div>}
                    <div style={{ opacity: 0.8 }}>👁 {s.observation}</div>
                  </div>
                ))}
              </div>
            );
          })}

          <div style={{
            margin: '10px 0 0', padding: '8px 10px', borderRadius: 6,
            background: sc.status === 'complete' ? '#dcfce7' : '#fee2e2',
          }}>
            <div style={{ fontSize: 11, opacity: 0.7 }}>queue status: {sc.status}</div>
            <div style={{ fontSize: 13.5 }}>{sc.summary}</div>
          </div>
          <p style={{ margin: '8px 0 0', fontSize: 13 }}><strong>Lesson:</strong> {sc.lesson}</p>
        </div>
      )}
    </div>
  );
}

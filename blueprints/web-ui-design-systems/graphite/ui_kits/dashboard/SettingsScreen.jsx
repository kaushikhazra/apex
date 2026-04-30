/* global React, Ico, Button, Input, Card, Eyebrow, Badge */
const { useState: useStateS } = React;

function SettingsScreen() {
  const [name, setName] = useStateS('graphite-web');
  const [domain, setDomain] = useStateS('graphite.acme.dev');
  const [framework, setFramework] = useStateS('Next.js');

  return (
    <div style={{ padding: '24px 32px', maxWidth: '820px' }}>
      <Eyebrow>graphite-web</Eyebrow>
      <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 500, letterSpacing: '-0.02em', margin: '6px 0 28px', color: 'var(--fg-1)' }}>Settings</h1>

      <Section title="General" desc="Basic project identity.">
        <Field label="Project name"><Input value={name} onChange={setName} /></Field>
        <Field label="Production domain"><Input value={domain} onChange={setDomain} leading="globe" /></Field>
        <Field label="Framework preset"><Input value={framework} onChange={setFramework} /></Field>
      </Section>

      <Section title="Deployments" desc="Control how this project builds and ships.">
        <Field label="Build command"><Input value="pnpm run build" onChange={() => {}} /></Field>
        <Field label="Output directory"><Input value="dist" onChange={() => {}} /></Field>
        <Field label="Auto-deploy on push" inline>
          <Toggle defaultOn />
        </Field>
      </Section>

      <Section title="Danger zone" danger desc="Irreversible and destructive actions.">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', fontWeight: 500, color: 'var(--fg-1)' }}>Transfer project</div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--fg-3)', marginTop: '2px' }}>Move graphite-web to another workspace.</div>
          </div>
          <Button variant="secondary">Transfer…</Button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 0', borderTop: '1px solid var(--border-subtle)' }}>
          <div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', fontWeight: 500, color: 'var(--fg-1)' }}>Delete project</div>
            <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--fg-3)', marginTop: '2px' }}>Permanently delete graphite-web and all deployments. This can't be undone.</div>
          </div>
          <Button variant="destructive">Delete…</Button>
        </div>
      </Section>

      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '20px' }}>
        <Button variant="ghost">Discard</Button>
        <Button variant="primary">Save changes</Button>
      </div>
    </div>
  );
}

function Section({ title, desc, danger, children }) {
  return (
    <Card padding="0" style={{ marginBottom: '16px', borderColor: danger ? 'var(--stone-700)' : 'var(--border-default)' }}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 500, color: danger ? 'var(--status-danger)' : 'var(--fg-1)' }}>{title}</div>
        {desc && <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--fg-3)', marginTop: '2px' }}>{desc}</div>}
      </div>
      <div style={{ padding: '8px 18px' }}>{children}</div>
    </Card>
  );
}

function Field({ label, children, inline }) {
  return (
    <div style={{ padding: '12px 0', borderBottom: '1px solid var(--border-subtle)', display: inline ? 'flex' : 'block', alignItems: 'center', justifyContent: 'space-between' }}>
      <label style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--fg-3)', display: 'block', marginBottom: inline ? 0 : '6px' }}>{label}</label>
      <div style={{ maxWidth: inline ? 'none' : '400px' }}>{children}</div>
    </div>
  );
}

function Toggle({ defaultOn }) {
  const [on, setOn] = useStateS(defaultOn);
  return (
    <button onClick={() => setOn(!on)} style={{
      width: '32px', height: '18px', borderRadius: '999px',
      background: on ? 'var(--accent-500)' : 'var(--stone-800)',
      border: '1px solid ' + (on ? 'var(--accent-500)' : 'var(--border-default)'),
      position: 'relative', transition: 'background 100ms var(--ease-out)',
      cursor: 'pointer',
    }}>
      <span style={{
        position: 'absolute', top: '1px', left: on ? '15px' : '1px',
        width: '14px', height: '14px', borderRadius: '999px',
        background: on ? '#1a1205' : 'var(--stone-400)',
        transition: 'left 100ms var(--ease-out)',
      }} />
    </button>
  );
}

Object.assign(window, { SettingsScreen });

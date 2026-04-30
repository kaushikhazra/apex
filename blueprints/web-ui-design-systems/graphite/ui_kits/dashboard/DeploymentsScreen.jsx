/* global React, Ico, Badge, Card, Eyebrow, Button */
const { useState: useStateD, useEffect: useEffectD, useRef: useRefD } = React;

function DeploymentsScreen() {
  const [selected, setSelected] = useStateD(0);
  const deployments = [
    { sha: 'a3f9e2c', msg: 'fix: stream backpressure on slow consumers', author: 'a.chen', branch: 'main', status: 'success', statusLabel: 'Ready', when: '2m ago', dur: '1m 42s', env: 'production' },
    { sha: 'b1d44e0', msg: 'feat: streaming token deltas in the composer', author: 'r.patel', branch: 'feat/streaming', status: 'warning', statusLabel: 'Building', when: 'just now', dur: '—', env: 'preview' },
    { sha: '9fe2110', msg: 'chore: bump lockfile', author: 'a.chen', branch: 'main', status: 'success', statusLabel: 'Ready', when: '4h ago', dur: '58s', env: 'production' },
    { sha: '3aa8c21', msg: 'docs: correct deployment env var example', author: 'm.suzuki', branch: 'docs/update', status: 'danger', statusLabel: 'Failed', when: '1d ago', dur: '12s', env: 'preview' },
    { sha: '7cc0d32', msg: 'feat: add retry with jitter to worker queue', author: 'r.patel', branch: 'main', status: 'success', statusLabel: 'Ready', when: '2d ago', dur: '2m 11s', env: 'production' },
    { sha: '1de90aa', msg: 'refactor: extract auth middleware', author: 'a.chen', branch: 'main', status: 'success', statusLabel: 'Ready', when: '3d ago', dur: '1m 20s', env: 'production' },
  ];

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1400px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <Eyebrow>graphite-web</Eyebrow>
          <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 500, letterSpacing: '-0.02em', margin: '6px 0 0', color: 'var(--fg-1)' }}>Deployments</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="secondary" icon="git-branch">main</Button>
          <Button variant="primary" icon="rocket">Deploy</Button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '16px' }}>
        {/* Deployments list */}
        <Card padding="0">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', background: 'var(--bg-raised)', borderBottom: '1px solid var(--border-default)', padding: '10px 16px' }}>
            <Eyebrow>History · {deployments.length}</Eyebrow>
          </div>
          {deployments.map((d, i) => <DeployRow key={d.sha} d={d} selected={selected === i} onClick={() => setSelected(i)} />)}
        </Card>

        {/* Log stream */}
        <Card padding="0" style={{ height: '560px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-default)', background: 'var(--bg-raised)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Ico name="terminal" size={14} style={{ color: 'var(--fg-2)' }} />
            <Eyebrow style={{ color: 'var(--fg-1)' }}>Build log</Eyebrow>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--fg-3)', marginLeft: 'auto' }}>{deployments[selected].sha}</span>
          </div>
          <LogStream />
        </Card>
      </div>
    </div>
  );
}

function DeployRow({ d, selected, onClick }) {
  const [hover, setHover] = useStateD(false);
  const bg = selected ? 'var(--bg-hover)' : hover ? 'var(--bg-hover)' : 'transparent';
  return (
    <div onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} style={{
      padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)',
      background: bg, cursor: 'pointer',
      borderLeft: selected ? '2px solid var(--accent-500)' : '2px solid transparent',
      paddingLeft: selected ? '14px' : '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
        <Badge status={d.status}>{d.statusLabel}</Badge>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--fg-3)' }}>{d.env}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--fg-3)', marginLeft: 'auto' }}>{d.when} · {d.dur}</span>
      </div>
      <div style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--fg-1)', marginBottom: '4px' }}>{d.msg}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--fg-3)' }}>
        {d.branch} · {d.sha} · <span>{d.author}</span>
      </div>
    </div>
  );
}

function LogStream() {
  const [lines, setLines] = useStateD([
    { t: '14:32:01', level: 'info', text: 'Resolving project dependencies…' },
    { t: '14:32:03', level: 'info', text: 'Installed 482 packages in 2.4s' },
    { t: '14:32:04', level: 'info', text: 'Running build command: pnpm run build' },
    { t: '14:32:12', level: 'info', text: 'vite v5.4.1 building for production…' },
    { t: '14:32:18', level: 'warn', text: 'Module "legacy-polyfill" is deprecated' },
    { t: '14:32:24', level: 'info', text: '✓ 1243 modules transformed' },
    { t: '14:32:28', level: 'info', text: 'dist/assets/index-a3f9e2c.js   842.12 kB │ gzip: 267.44 kB' },
    { t: '14:32:29', level: 'info', text: 'Uploading build artifacts…' },
    { t: '14:32:41', level: 'info', text: 'Deployed to production @ a3f9e2c' },
    { t: '14:32:42', level: 'ok', text: 'Ready · 142ms first byte' },
  ]);
  const bodyRef = useRefD(null);
  useEffectD(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [lines]);

  const levelColor = { info: 'var(--fg-2)', warn: 'var(--status-warning)', err: 'var(--status-danger)', ok: 'var(--status-success)' };

  return (
    <div ref={bodyRef} style={{
      flex: 1, overflow: 'auto', padding: '10px 14px',
      fontFamily: 'var(--font-mono)', fontSize: '12px', lineHeight: 1.6,
      background: 'var(--bg-surface)',
    }}>
      {lines.map((l, i) => (
        <div key={i} style={{ display: 'flex', gap: '12px' }}>
          <span style={{ color: 'var(--fg-4)', flexShrink: 0 }}>{l.t}</span>
          <span style={{ color: levelColor[l.level] || 'var(--fg-2)', flexShrink: 0, textTransform: 'uppercase', fontSize: '10px', letterSpacing: '0.08em', width: '36px' }}>{l.level}</span>
          <span style={{ color: 'var(--fg-1)' }}>{l.text}</span>
        </div>
      ))}
      <div style={{ color: 'var(--fg-4)', marginTop: '4px' }}>_</div>
    </div>
  );
}

Object.assign(window, { DeploymentsScreen });

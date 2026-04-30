/* global React, Ico, Badge, Card, MetricCard, Eyebrow, Button */
const { useState: useStateO } = React;

function OverviewScreen({ onOpenProject }) {
  const projects = [
    { name: 'graphite-web', env: 'production', status: 'success', statusLabel: 'Ready', branch: 'main', sha: 'a3f9e2c', deployed: '2m ago', latency: '142ms' },
    { name: 'graphite-api', env: 'production', status: 'warning', statusLabel: 'Building', branch: 'feat/streaming', sha: 'b1d44e0', deployed: 'just now', latency: '—' },
    { name: 'graphite-worker', env: 'production', status: 'success', statusLabel: 'Ready', branch: 'main', sha: '9fe2110', deployed: '4h ago', latency: '38ms' },
    { name: 'graphite-docs', env: 'preview', status: 'danger', statusLabel: 'Failed', branch: 'docs/update', sha: '3aa8c21', deployed: '1d ago', latency: '—' },
    { name: 'graphite-cli', env: 'production', status: 'info', statusLabel: 'Idle', branch: 'main', sha: '7cc0d32', deployed: '6d ago', latency: '—' },
  ];

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1200px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <Eyebrow>Workspace · acme</Eyebrow>
          <h1 style={{ fontFamily: 'var(--font-mono)', fontSize: '28px', fontWeight: 500, letterSpacing: '-0.02em', margin: '6px 0 0', color: 'var(--fg-1)' }}>Overview</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button variant="secondary" icon="filter" size="md">Filter</Button>
          <Button variant="primary" icon="plus">New project</Button>
        </div>
      </div>

      {/* Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
        <MetricCard label="Deployments · 7d" value="48" delta="↑ 12 vs last week" deltaType="up" />
        <MetricCard label="Avg latency" value="142ms" delta="↓ 18ms vs last week" deltaType="up" />
        <MetricCard label="Error rate" value="0.02%" delta="steady" deltaType="neutral" />
        <MetricCard label="Uptime · 30d" value="99.98%" accent delta="SLA 99.9%" deltaType="neutral" />
      </div>

      {/* Projects table */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
        <Eyebrow>Projects · 5</Eyebrow>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--fg-3)' }}>Sorted by last deploy</div>
      </div>

      <Card padding="0" style={{ overflow: 'hidden' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1.5fr 1fr 80px', padding: '10px 16px', background: 'var(--bg-raised)', borderBottom: '1px solid var(--border-default)' }}>
          {['Project', 'Status', 'Branch', 'Latency', ''].map((h, i) => (
            <span key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--fg-3)' }}>{h}</span>
          ))}
        </div>
        {projects.map((p, i) => <ProjectRow key={p.name} project={p} onClick={() => onOpenProject?.(p.name)} />)}
      </Card>
    </div>
  );
}

function ProjectRow({ project, onClick }) {
  const [hover, setHover] = useStateO(false);
  return (
    <div onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)} style={{
      display: 'grid', gridTemplateColumns: '2fr 1fr 1.5fr 1fr 80px',
      padding: '12px 16px', alignItems: 'center',
      borderBottom: '1px solid var(--border-subtle)',
      background: hover ? 'var(--bg-hover)' : 'transparent',
      fontFamily: 'var(--font-mono)', fontSize: '13px',
      cursor: 'pointer',
    }}>
      <div>
        <div style={{ color: 'var(--fg-1)' }}>{project.name}</div>
        <div style={{ color: 'var(--fg-3)', fontSize: '11px', marginTop: '2px' }}>{project.env} · {project.deployed}</div>
      </div>
      <div><Badge status={project.status}>{project.statusLabel}</Badge></div>
      <div style={{ color: 'var(--fg-2)' }}>
        {project.branch}
        <span style={{ color: 'var(--fg-4)' }}> · </span>
        <span style={{ color: 'var(--fg-3)' }}>{project.sha}</span>
      </div>
      <div style={{ color: 'var(--fg-1)' }}>{project.latency}</div>
      <div style={{ textAlign: 'right', color: 'var(--fg-3)' }}><Ico name="chevron-right" size={14} /></div>
    </div>
  );
}

Object.assign(window, { OverviewScreen });

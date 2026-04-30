/* global React, Ico, Button, Badge */
function TopBar({ crumbs = [], tabs, activeTab, onTab, right }) {
  return (
    <header style={{
      height: '48px',
      background: 'var(--bg-app)',
      borderBottom: '1px solid var(--border-default)',
      display: 'flex', alignItems: 'center',
      padding: '0 20px', gap: '16px',
      position: 'sticky', top: 0, zIndex: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}>
        {crumbs.map((c, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span style={{ color: 'var(--fg-4)' }}>/</span>}
            <span style={{ color: i === crumbs.length - 1 ? 'var(--fg-1)' : 'var(--fg-3)' }}>{c}</span>
          </React.Fragment>
        ))}
      </div>
      {tabs && (
        <nav style={{ display: 'flex', gap: 0, alignSelf: 'stretch', marginLeft: '16px' }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => onTab?.(t.id)} style={{
              padding: '0 14px',
              fontFamily: 'var(--font-mono)', fontSize: '11px',
              textTransform: 'uppercase', letterSpacing: '0.08em',
              color: activeTab === t.id ? 'var(--fg-1)' : 'var(--fg-3)',
              borderBottom: `2px solid ${activeTab === t.id ? 'var(--accent-500)' : 'transparent'}`,
              marginBottom: '-1px',
              cursor: 'pointer',
            }}>{t.label}</button>
          ))}
        </nav>
      )}
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '10px' }}>
        {right}
      </div>
    </header>
  );
}

Object.assign(window, { TopBar });

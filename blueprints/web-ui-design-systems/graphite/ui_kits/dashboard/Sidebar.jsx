/* global React, Ico, Eyebrow */
const { useState: useStateShell } = React;

function Sidebar({ current, onNavigate, onOpenPalette }) {
  const items = [
    { section: 'Workspace' },
    { id: 'overview', label: 'Overview', icon: 'layout-dashboard' },
    { id: 'deployments', label: 'Deployments', icon: 'rocket', count: 12 },
    { id: 'logs', label: 'Logs', icon: 'terminal' },
    { id: 'activity', label: 'Activity', icon: 'activity' },
    { section: 'Project' },
    { id: 'settings', label: 'Settings', icon: 'settings' },
    { id: 'members', label: 'Members', icon: 'users' },
    { id: 'billing', label: 'Billing', icon: 'credit-card' },
  ];
  return (
    <aside style={{
      width: '240px', flexShrink: 0,
      background: 'var(--bg-surface)',
      borderRight: '1px solid var(--border-default)',
      display: 'flex', flexDirection: 'column',
      height: '100vh', position: 'sticky', top: 0,
    }}>
      {/* Logo / workspace switcher */}
      <div style={{
        height: '48px', padding: '0 14px',
        display: 'flex', alignItems: 'center', gap: '10px',
        borderBottom: '1px solid var(--border-default)',
        cursor: 'pointer',
      }}>
        <span style={{ color: 'var(--fg-1)', display: 'inline-flex' }}>
          <svg viewBox="0 0 40 40" width="20" height="20" fill="none">
            <g stroke="currentColor" strokeWidth="3" strokeLinecap="square"><path d="M6 8 L30 8 L30 16"/><path d="M6 20 L22 20"/><path d="M6 32 L30 32 L30 20"/></g>
          </svg>
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: 500, color: 'var(--fg-1)' }}>graphite-web</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-3)' }}>acme / production</div>
        </div>
        <Ico name="chevrons-up-down" size={14} style={{ color: 'var(--fg-3)' }} />
      </div>

      {/* Palette trigger */}
      <div style={{ padding: '10px 10px 6px' }}>
        <button onClick={onOpenPalette} style={{
          width: '100%', height: '28px', padding: '0 10px',
          display: 'flex', alignItems: 'center', gap: '8px',
          background: 'var(--bg-raised)',
          border: '1px solid var(--border-default)',
          borderRadius: '4px',
          fontFamily: 'var(--font-sans)', fontSize: '12px',
          color: 'var(--fg-3)',
          cursor: 'pointer',
        }}>
          <Ico name="search" size={13} style={{ color: 'var(--fg-3)' }} />
          <span>Find anything…</span>
          <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: '10px' }}>⌘K</span>
        </button>
      </div>

      <nav style={{ flex: 1, overflow: 'auto', padding: '4px 8px 16px' }}>
        {items.map((it, i) => it.section ? (
          <div key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--fg-3)', padding: '14px 10px 4px' }}>{it.section}</div>
        ) : (
          <NavItem key={it.id} {...it} selected={current === it.id} onClick={() => onNavigate(it.id)} />
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        borderTop: '1px solid var(--border-default)',
        padding: '10px 14px',
        display: 'flex', alignItems: 'center', gap: '10px',
      }}>
        <div style={{ width: '24px', height: '24px', borderRadius: '999px', background: 'var(--stone-750)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-1)' }}>AC</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--fg-1)' }}>a.chen</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-3)' }}>Owner</div>
        </div>
        <Ico name="more-horizontal" size={14} style={{ color: 'var(--fg-3)' }} />
      </div>
    </aside>
  );
}

function NavItem({ label, icon, count, selected, onClick }) {
  const [hover, setHover] = useStateShell(false);
  const bg = selected || hover ? 'var(--bg-hover)' : 'transparent';
  const color = selected || hover ? 'var(--fg-1)' : 'var(--fg-2)';
  return (
    <div onClick={onClick}
      onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: '10px',
        padding: '6px 10px', borderRadius: '3px',
        fontFamily: 'var(--font-sans)', fontSize: '13px',
        color, background: bg,
        position: 'relative', cursor: 'pointer',
      }}>
      {selected && <span style={{ position: 'absolute', left: 0, top: '4px', bottom: '4px', width: '2px', background: 'var(--accent-500)', borderRadius: '2px' }} />}
      <Ico name={icon} size={14} style={{ color: selected ? 'var(--fg-1)' : 'var(--fg-3)' }} />
      <span style={{ flex: 1 }}>{label}</span>
      {count != null && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-3)' }}>{count}</span>}
    </div>
  );
}

Object.assign(window, { Sidebar, NavItem });

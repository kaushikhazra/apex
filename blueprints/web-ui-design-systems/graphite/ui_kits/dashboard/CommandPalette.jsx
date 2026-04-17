/* global React, Ico */
const { useState: useStateCP, useEffect: useEffectCP } = React;

function CommandPalette({ open, onClose, onCommand }) {
  const [q, setQ] = useStateCP('');
  const [sel, setSel] = useStateCP(0);
  const cmds = [
    { id: 'go-overview', label: 'Go to Overview', icon: 'layout-dashboard', group: 'Navigation', kbd: '⌘1' },
    { id: 'go-deployments', label: 'Go to Deployments', icon: 'rocket', group: 'Navigation', kbd: '⌘2' },
    { id: 'go-settings', label: 'Go to Settings', icon: 'settings', group: 'Navigation', kbd: '⌘,' },
    { id: 'new-project', label: 'Create new project', icon: 'plus', group: 'Actions' },
    { id: 'deploy', label: 'Deploy main to production', icon: 'rocket', group: 'Actions' },
    { id: 'invite', label: 'Invite teammate', icon: 'user-plus', group: 'Actions' },
    { id: 'theme', label: 'Toggle theme', icon: 'moon', group: 'Preferences' },
    { id: 'docs', label: 'Open documentation', icon: 'book-open', group: 'Help' },
  ];
  const filtered = cmds.filter(c => c.label.toLowerCase().includes(q.toLowerCase()));

  useEffectCP(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => Math.min(s + 1, filtered.length - 1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => Math.max(s - 1, 0)); }
      if (e.key === 'Enter') { e.preventDefault(); if (filtered[sel]) onCommand?.(filtered[sel].id); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, sel, filtered, onClose, onCommand]);

  useEffectCP(() => { setSel(0); }, [q]);

  if (!open) return null;

  let lastGroup = null;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 100,
      background: 'rgba(13,12,10,0.6)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      paddingTop: '15vh',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: '560px', maxWidth: '90vw',
        background: 'var(--bg-raised)',
        border: '1px solid var(--border-strong)',
        borderRadius: '8px',
        overflow: 'hidden',
        display: 'flex', flexDirection: 'column',
        animation: 'gr-fade-up 160ms var(--ease-out)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', borderBottom: '1px solid var(--border-subtle)' }}>
          <Ico name="search" size={16} style={{ color: 'var(--fg-3)' }} />
          <input autoFocus value={q} onChange={e => setQ(e.target.value)} placeholder="Type a command or search…" style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            fontFamily: 'var(--font-sans)', fontSize: '14px', color: 'var(--fg-1)',
          }} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-3)', padding: '2px 6px', border: '1px solid var(--border-default)', borderRadius: '3px' }}>ESC</span>
        </div>
        <div style={{ maxHeight: '420px', overflow: 'auto', padding: '4px' }}>
          {filtered.length === 0 && (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--fg-3)', fontFamily: 'var(--font-sans)', fontSize: '13px' }}>No results</div>
          )}
          {filtered.map((c, i) => {
            const showGroup = c.group !== lastGroup;
            lastGroup = c.group;
            const isSel = i === sel;
            return (
              <React.Fragment key={c.id}>
                {showGroup && <div style={{ fontFamily: 'var(--font-mono)', fontSize: '9px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--fg-3)', padding: '10px 12px 4px' }}>{c.group}</div>}
                <div onClick={() => onCommand?.(c.id)} onMouseEnter={() => setSel(i)} style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '8px 12px', borderRadius: '3px',
                  background: isSel ? 'var(--bg-hover)' : 'transparent',
                  fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--fg-1)',
                  cursor: 'pointer',
                  position: 'relative',
                }}>
                  {isSel && <span style={{ position: 'absolute', left: 0, top: '6px', bottom: '6px', width: '2px', background: 'var(--accent-500)', borderRadius: '2px' }} />}
                  <Ico name={c.icon} size={14} style={{ color: 'var(--fg-3)' }} />
                  <span style={{ flex: 1 }}>{c.label}</span>
                  {c.kbd && <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-3)' }}>{c.kbd}</span>}
                </div>
              </React.Fragment>
            );
          })}
        </div>
        <div style={{ borderTop: '1px solid var(--border-subtle)', padding: '8px 14px', display: 'flex', gap: '14px', fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--fg-3)' }}>
          <span>↑↓ navigate</span>
          <span>↵ select</span>
          <span>esc close</span>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { CommandPalette });

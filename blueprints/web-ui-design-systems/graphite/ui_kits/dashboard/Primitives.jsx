/* global React */
const { useState: useStateP, useEffect: useEffectP, useRef: useRefP } = React;

// ============================================================
// Button
// ============================================================
function Button({ variant = 'secondary', size = 'md', children, onClick, disabled, icon, trailing, style }) {
  const bstyle = {
    fontFamily: 'var(--font-sans)',
    fontSize: size === 'sm' ? '12px' : '13px',
    fontWeight: 500,
    height: size === 'sm' ? '24px' : '32px',
    padding: size === 'sm' ? '0 10px' : '0 14px',
    borderRadius: '4px',
    border: '1px solid transparent',
    display: 'inline-flex', alignItems: 'center', gap: '6px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.4 : 1,
    transition: 'background 100ms var(--ease-out), border-color 100ms var(--ease-out)',
    whiteSpace: 'nowrap',
  };
  const variants = {
    primary: { background: 'var(--accent-500)', color: '#1a1205', borderColor: 'var(--accent-500)' },
    secondary: { background: 'var(--bg-raised)', color: 'var(--fg-1)', borderColor: 'var(--border-default)' },
    ghost: { background: 'transparent', color: 'var(--fg-1)' },
    destructive: { background: 'transparent', color: 'var(--status-danger)', borderColor: 'var(--border-default)' },
  };
  return (
    <button onClick={disabled ? undefined : onClick} style={{ ...bstyle, ...variants[variant], ...style }}>
      {icon && <Ico name={icon} size={14} />}
      {children}
      {trailing}
    </button>
  );
}

// ============================================================
// Icon wrapper — renders Lucide via data-lucide attr
// ============================================================
function Ico({ name, size = 16, color, style }) {
  const ref = useRefP(null);
  useEffectP(() => {
    if (window.lucide && ref.current) {
      ref.current.innerHTML = '';
      const i = document.createElement('i');
      i.setAttribute('data-lucide', name);
      ref.current.appendChild(i);
      window.lucide.createIcons({ attrs: { width: size, height: size, 'stroke-width': 1.75 } });
    }
  }, [name, size]);
  return <span ref={ref} style={{ display: 'inline-flex', width: size, height: size, color: color || 'currentColor', ...style }} />;
}

// ============================================================
// Input
// ============================================================
function Input({ value, onChange, placeholder, leading, trailing, focused, disabled, style }) {
  const [isFocus, setFocus] = useStateP(focused);
  const borderColor = isFocus ? 'var(--accent-500)' : 'var(--border-default)';
  return (
    <label style={{
      display: 'flex', alignItems: 'center', gap: '6px',
      height: '32px', padding: '0 10px',
      background: 'var(--bg-app)',
      border: `1px solid ${borderColor}`,
      borderRadius: '4px',
      fontFamily: 'var(--font-sans)', fontSize: '13px',
      opacity: disabled ? 0.4 : 1,
      ...style,
    }}>
      {leading && <Ico name={leading} size={14} style={{ color: 'var(--fg-3)' }} />}
      <input
        value={value} onChange={e => onChange?.(e.target.value)}
        placeholder={placeholder} disabled={disabled}
        onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
        style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: 'var(--fg-1)', minWidth: 0 }}
      />
      {trailing}
    </label>
  );
}

// ============================================================
// Badge (status pill)
// ============================================================
function Badge({ status = 'info', children }) {
  const colors = {
    success: 'var(--status-success)', warning: 'var(--status-warning)',
    danger: 'var(--status-danger)', info: 'var(--status-info)',
    accent: 'var(--accent-500)',
  };
  return (
    <span style={{
      fontFamily: 'var(--font-mono)', fontSize: '10px', fontWeight: 500,
      textTransform: 'uppercase', letterSpacing: '0.08em',
      padding: '3px 8px', borderRadius: '999px',
      border: '1px solid var(--border-default)',
      color: 'var(--fg-1)', background: 'var(--bg-raised)',
      display: 'inline-flex', alignItems: 'center', gap: '6px',
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '999px', background: colors[status] }} />
      {children}
    </span>
  );
}

// ============================================================
// Card
// ============================================================
function Card({ children, padding = '16px', style, onClick }) {
  return (
    <div onClick={onClick} style={{
      background: 'var(--bg-surface)',
      border: '1px solid var(--border-default)',
      borderRadius: '6px',
      padding,
      cursor: onClick ? 'pointer' : 'default',
      ...style,
    }}>{children}</div>
  );
}

function MetricCard({ label, value, delta, deltaType = 'neutral', accent }) {
  const deltaColor = {
    up: 'var(--status-success)', down: 'var(--status-danger)', neutral: 'var(--fg-3)'
  }[deltaType];
  return (
    <Card padding="14px 16px">
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--fg-3)' }}>{label}</div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 500, color: accent ? 'var(--fg-accent)' : 'var(--fg-1)', marginTop: '6px', letterSpacing: '-0.01em' }}>{value}</div>
      {delta && <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: deltaColor, marginTop: '4px' }}>{delta}</div>}
    </Card>
  );
}

// ============================================================
// Eyebrow label helper
// ============================================================
function Eyebrow({ children, style }) {
  return <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--fg-3)', ...style }}>{children}</div>;
}

// ============================================================
// Export to window
// ============================================================
Object.assign(window, { Button, Ico, Input, Badge, Card, MetricCard, Eyebrow });

/* global React, Ico */
const { useState: useStateT, useEffect: useEffectT } = React;

function ToastStack({ toasts, onDismiss }) {
  return (
    <div style={{ position: 'fixed', bottom: '20px', right: '20px', display: 'flex', flexDirection: 'column', gap: '8px', zIndex: 200, maxWidth: '360px' }}>
      {toasts.map(t => <Toast key={t.id} toast={t} onDismiss={() => onDismiss(t.id)} />)}
    </div>
  );
}

function Toast({ toast, onDismiss }) {
  useEffectT(() => {
    const h = setTimeout(onDismiss, 4000);
    return () => clearTimeout(h);
  }, []);
  const colors = { success: 'var(--status-success)', danger: 'var(--status-danger)', info: 'var(--accent-500)' };
  return (
    <div style={{
      background: 'var(--bg-raised)',
      border: '1px solid var(--border-strong)',
      borderRadius: '6px',
      padding: '10px 14px',
      display: 'flex', alignItems: 'center', gap: '10px',
      fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--fg-1)',
      animation: 'gr-fade-up 160ms var(--ease-out)',
    }}>
      <span style={{ width: '6px', height: '6px', borderRadius: '999px', background: colors[toast.kind] || colors.info, flexShrink: 0 }} />
      <span style={{ flex: 1 }}>{toast.text}</span>
      <button onClick={onDismiss} style={{ color: 'var(--fg-3)', display: 'inline-flex' }}><Ico name="x" size={12} /></button>
    </div>
  );
}

Object.assign(window, { ToastStack });

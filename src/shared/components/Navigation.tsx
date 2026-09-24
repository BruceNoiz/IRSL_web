import { useEffect, useRef, useState } from 'react';

type Props = { items: { href: string; label: string }[]; current: string;
  labels: { navigation: string; openMenu: string; closeMenu: string } };

export default function Navigation({ items, current, labels }: Props) {
  const [enhanced, setEnhanced] = useState(false);
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  useEffect(() => setEnhanced(true), []);

  return (
    <nav className="navigation" aria-label={labels.navigation} onKeyDown={(event) => {
      if (event.key === 'Escape' && open) {
        setOpen(false);
        toggle.current?.focus();
      }
    }}>
      <button ref={toggle} type="button" className="menu-toggle" hidden={!enhanced}
        aria-expanded={open} aria-controls="main-navigation" onClick={() => setOpen(!open)}>
        {open ? labels.closeMenu : labels.openMenu}
      </button>
      <ul id="main-navigation" data-expanded={!enhanced || open}>
        {items.map(({ href, label }) => <li key={href}>
          <a href={href} aria-current={current === href ? 'page' : undefined}>{label}</a>
        </li>)}
      </ul>
    </nav>
  );
}

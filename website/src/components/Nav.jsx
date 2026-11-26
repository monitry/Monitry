import { useState } from "react";
import styles from "./Nav.module.css";

const TABS = [
  { id: "home", label: "Home", href: "#/" },
  { id: "fullfocus", label: "Full Focus", href: "#/fullfocus" },
  { id: "classwatch", label: "ClassWatch", href: "#/classwatch" },
  { id: "docs", label: "Documentation", href: "#/docs" },
  { id: "about", label: "About", href: "#/about" },
];

export default function Nav({ current }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const close = () => setMobileOpen(false);

  return (
    <nav className={styles.nav} aria-label="Main">
      <div className={styles.bar}>
        <a className={styles.logo} href="#/" onClick={close}>
          Onit<span>ry</span>
        </a>

        <ul className={styles.tabs}>
          {TABS.map((tab) => (
            <li key={tab.id}>
              <a
                className={`${styles.tab} ${current === tab.id ? styles.active : ""}`}
                href={tab.href}
                aria-current={current === tab.id ? "page" : undefined}
              >
                {tab.label}
              </a>
            </li>
          ))}
        </ul>

        <a className={styles.cta} href="#/docs/install">
          Get Onitry — free
        </a>

        <button
          className={styles.menuToggle}
          onClick={() => setMobileOpen((open) => !open)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
          aria-expanded={mobileOpen}
        >
          <span />
          <span />
          <span />
        </button>
      </div>

      {mobileOpen && (
        <div className={styles.mobileMenu}>
          {TABS.map((tab) => (
            <a
              key={tab.id}
              className={`${styles.mobileLink} ${current === tab.id ? styles.active : ""}`}
              href={tab.href}
              onClick={close}
            >
              {tab.label}
            </a>
          ))}
          <a className={styles.mobileCta} href="#/docs/install" onClick={close}>
            Get Onitry — free
          </a>
        </div>
      )}
    </nav>
  );
}

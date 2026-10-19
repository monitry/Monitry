import { useState } from "react";
import styles from "./Nav.module.css";

const TABS = [
  { id: "home",       label: "Home" },
  { id: "fullfocus",  label: "Full Focus" },
  { id: "classwatch", label: "ClassWatch" },
  { id: "docs",       label: "Documentation" },
  { id: "about",      label: "About" },
];

export default function Nav({ current, onNav }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navigate = (id) => {
    onNav(id);
    setMobileOpen(false);
  };

  return (
    <nav className={styles.nav}>
      <div className={styles.bar}>
        <button className={styles.logo} onClick={() => navigate("home")}>
          Onit<span>ry</span>
        </button>

        <ul className={styles.tabs}>
          {TABS.map((tab) => (
            <li key={tab.id}>
              <button
                className={`${styles.tab} ${current === tab.id ? styles.active : ""}`}
                onClick={() => navigate(tab.id)}
              >
                {tab.label}
              </button>
            </li>
          ))}
        </ul>

        <button className={styles.cta} onClick={() => navigate("docs")}>
          Get started
        </button>

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
            <button
              key={tab.id}
              className={`${styles.mobileLink} ${current === tab.id ? styles.active : ""}`}
              onClick={() => navigate(tab.id)}
            >
              {tab.label}
            </button>
          ))}
          <button className={styles.mobileCta} onClick={() => navigate("docs")}>
            Get started
          </button>
        </div>
      )}
    </nav>
  );
}

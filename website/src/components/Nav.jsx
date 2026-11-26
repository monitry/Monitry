import styles from "./Nav.module.css";

const TABS = [
  { id: "home", label: "Home", href: "#/" },
  { id: "docs", label: "Documentation", href: "#/docs" },
  { id: "about", label: "About", href: "#/about" },
];

export default function Nav({ current }) {
  return (
    <nav className={styles.nav} aria-label="Main">
      <a className={styles.logo} href="#/">
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

      <a className={styles.cta} href="#/docs">
        Get Onitry — free
      </a>
    </nav>
  );
}

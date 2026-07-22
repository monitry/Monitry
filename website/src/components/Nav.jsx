import styles from "./Nav.module.css";

const TABS = [
  { id: "home",  label: "Home" },
  { id: "docs",  label: "Documentation" },
  { id: "about", label: "About" },
];

export default function Nav({ current, onNav }) {
  return (
    <nav className={styles.nav}>
      <button className={styles.logo} onClick={() => onNav("home")}>
        Onit<span>ry</span>
      </button>

      <ul className={styles.tabs}>
        {TABS.map((tab) => (
          <li key={tab.id}>
            <button
              className={`${styles.tab} ${current === tab.id ? styles.active : ""}`}
              onClick={() => onNav(tab.id)}
            >
              {tab.label}
            </button>
          </li>
        ))}
      </ul>

      <button className={styles.cta} onClick={() => onNav("home")}>
        Get started
      </button>
    </nav>
  );
}

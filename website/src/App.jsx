import { useEffect, useState } from "react";
import Nav from "./components/Nav.jsx";
import Home from "./pages/Home.jsx";
import FullFocus from "./pages/FullFocus.jsx";
import ClassWatch from "./pages/ClassWatch.jsx";
import Docs from "./pages/Docs.jsx";
import About from "./pages/About.jsx";
import Privacy from "./pages/Privacy.jsx";
import Terms from "./pages/Terms.jsx";

// Pages live at #/docs, #/about, … so every page has a shareable link and the browser's back button works.
// (A hash router needs no server rewrites, so it also works on GitHub Pages and any static host.)
export const PAGES = { home: Home, fullfocus: FullFocus, classwatch: ClassWatch, docs: Docs, about: About, privacy: Privacy, terms: Terms };

const TITLES = {
  home: "Stay on task. Automatically.",
  fullfocus: "Full Focus",
  classwatch: "ClassWatch",
  docs: "Documentation",
  about: "About",
  privacy: "Privacy",
  terms: "Terms",
};

export const hrefFor = (id) => (id === "home" ? "#/" : `#/${id}`);

function pageFromHash() {
  const id = window.location.hash.replace(/^#\/?/, "").split(/[?#]/)[0] || "home";
  return PAGES[id] ? id : "home";
}

// Pages call onNav("docs") to move around; it just changes the URL.
const onNav = (id) => {
  window.location.hash = hrefFor(id);
};

export default function App() {
  const [page, setPage] = useState(pageFromHash);

  useEffect(() => {
    const onHash = () => {
      setPage(pageFromHash());
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    document.title = page === "home" ? `Onitry — ${TITLES.home}` : `${TITLES[page]} — Onitry`;
  }, [page]);

  const Page = PAGES[page];
  return (
    <>
      <Nav current={page} />
      <Page onNav={onNav} />
    </>
  );
}

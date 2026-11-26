import { useEffect, useState } from "react";
import Nav from "./components/Nav.jsx";
import Home from "./pages/Home.jsx";
import Docs from "./pages/Docs.jsx";
import About from "./pages/About.jsx";
import Privacy from "./pages/Privacy.jsx";
import Terms from "./pages/Terms.jsx";

// Pages live at #/docs, #/about, … so every page has a shareable link and the browser's back button works.
// (A hash router needs no server rewrites, so it also works on GitHub Pages and any static host.)
export const PAGES = { home: Home, docs: Docs, about: About, privacy: Privacy, terms: Terms };

function pageFromHash() {
  const id = window.location.hash.replace(/^#\/?/, "").split(/[?#]/)[0] || "home";
  return PAGES[id] ? id : "home";
}

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
    const names = { home: "Stay on task. Automatically.", docs: "Documentation", about: "About", privacy: "Privacy", terms: "Terms" };
    document.title = page === "home" ? `Onitry — ${names.home}` : `${names[page]} — Onitry`;
  }, [page]);

  const Page = PAGES[page];
  return (
    <>
      <Nav current={page} />
      <Page />
    </>
  );
}

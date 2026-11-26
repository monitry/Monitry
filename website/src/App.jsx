import { useEffect, useState } from "react";
import Nav from "./components/Nav.jsx";
import Home, { SiteFooter } from "./pages/Home.jsx";
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

// "#/docs/install" is the docs page, scrolled to its Install section.
function routeFromHash() {
  const [id = "", section = ""] = window.location.hash.replace(/^#\/?/, "").split(/[?#]/)[0].split("/");
  const page = PAGES[id] ? id : "home";
  return { page, section: page === "docs" ? section : "" };
}

// Pages call onNav("docs") to move around; it just changes the URL.
const onNav = (id) => {
  window.location.hash = hrefFor(id);
};

export default function App() {
  const [route, setRoute] = useState(routeFromHash);
  const { page, section } = route;

  useEffect(() => {
    const onHash = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  // After every route change: top of the page, or the requested docs section.
  useEffect(() => {
    const target = section && document.getElementById(`sec-${section}`);
    if (target) target.scrollIntoView({ behavior: "instant" });
    else window.scrollTo({ top: 0, behavior: "instant" });
  }, [page, section]);

  useEffect(() => {
    document.title = page === "home" ? `Onitry — ${TITLES.home}` : `${TITLES[page]} — Onitry`;
  }, [page]);

  const Page = PAGES[page];
  return (
    <>
      <Nav current={page} />
      <Page onNav={onNav} />
      <SiteFooter />
    </>
  );
}

import { useState } from "react";
import Nav from "./components/Nav.jsx";
import Home from "./pages/Home.jsx";
import Docs from "./pages/Docs.jsx";
import About from "./pages/About.jsx";

const PAGES = { home: Home, docs: Docs, about: About };

export default function App() {
  const [page, setPage] = useState("home");
  const Page = PAGES[page];

  return (
    <>
      <Nav current={page} onNav={setPage} />
      <Page />
    </>
  );
}

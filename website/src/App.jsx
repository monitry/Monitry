import { useState } from "react";
import Nav from "./components/Nav.jsx";
import Home from "./pages/Home.jsx";
import FullFocus from "./pages/FullFocus.jsx";
import ClassWatch from "./pages/ClassWatch.jsx";
import Docs from "./pages/Docs.jsx";
import About from "./pages/About.jsx";

export default function App() {
  const [page, setPage] = useState("home");

  const pageProps = { onNav: setPage };

  return (
    <>
      <Nav current={page} onNav={setPage} />
      {page === "home" && <Home {...pageProps} />}
      {page === "fullfocus" && <FullFocus {...pageProps} />}
      {page === "classwatch" && <ClassWatch {...pageProps} />}
      {page === "docs" && <Docs {...pageProps} />}
      {page === "about" && <About {...pageProps} />}
    </>
  );
}

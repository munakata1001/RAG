import React from "react";
import { Outlet, Link } from "react-router-dom";

function App() {
  return (
    <div className="app">
      <header className="header">
        <h1>社内RAG PoC</h1>
        <nav>
          <Link to="/">Search</Link> | <Link to="/admin">Admin</Link>
        </nav>
      </header>

      <main className="container">
        <Outlet />
      </main>

      <footer className="footer">RAG PoC - Demo</footer>
    </div>
  );
}

export default App;


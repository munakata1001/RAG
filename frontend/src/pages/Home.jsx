import React, { useState } from "react";
import SearchBox from "../components/SearchBox";
import SearchResults from "../components/SearchResults";
import AnswerBox from "../components/AnswerBox";

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleResults = (q, res) => {
    setQuery(q);
    setResults(res);
    setLoading(false);
  };

  return (
    <div>
      <h2>検索</h2>
      <SearchBox onSearchStart={() => setLoading(true)} onResults={handleResults} />
      {loading && <p>検索中...</p>}
      <SearchResults results={results} />
      {results.length > 0 && <AnswerBox query={query} contexts={results} />}
    </div>
  );
}



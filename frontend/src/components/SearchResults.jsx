import React from "react";

export default function SearchResults({ results = [] }) {
  if (!results?.length) return null;

  return (
    <div className="card">
      <h3>検索結果（上位 {results.length} 件）</h3>
      <ol>
        {results.map((r) => (
          <li key={r.id} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 14 }}>
              {r.text?.slice(0, 300)}
              {r.text?.length > 300 ? "..." : ""}
            </div>
            <div style={{ fontSize: 12, color: "#666" }}>
              source: {r.filename} — score: {typeof r.score === "number" ? r.score.toFixed(3) : "-"}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}


import React, { useState } from "react";
import { api } from "../api/client";

export default function SearchBox({ onResults, onSearchStart }) {
  const [q, setQ] = useState("");

  const doSearch = async () => {
    if (!q) return;
    onSearchStart?.();
    try {
      const res = await api.post("/search", { query: q, top_k: 5 });
      onResults?.(q, res.data);
    } catch (err) {
      console.error(err);
      onResults?.(q, []);
    }
  };

  return (
    <div className="card">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="質問（日本語）を入力"
        style={{ width: "80%" }}
      />
      <button onClick={doSearch}>検索</button>
    </div>
  );
}


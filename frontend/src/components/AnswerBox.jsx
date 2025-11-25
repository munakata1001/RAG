import React, { useState } from "react";
import { api } from "../api/client";

export default function AnswerBox({ query, contexts }) {
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    if (!query || !contexts?.length) return;
    setLoading(true);
    try {
      const payload = {
        query,
        contexts: contexts.map((c) => ({
          text: c.text,
          score: c.score,
          filename: c.filename,
          chunk_id: c.chunk_id,
        })),
      };
      const res = await api.post("/generate", payload);
      setAnswer(res.data.answer || "");
    } catch (err) {
      console.error(err);
      setAnswer("生成エラー: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async () => {
    if (!answer) return;
    await navigator.clipboard.writeText(answer);
    alert("コピーしました");
  };

  return (
    <div className="card">
      <h3>回答生成</h3>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button onClick={generate} disabled={loading || !contexts?.length}>
          {loading ? "生成中..." : "回答を生成"}
        </button>
        <button onClick={copyToClipboard} disabled={!answer}>
          コピー
        </button>
      </div>
      <pre style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>{answer}</pre>
    </div>
  );
}


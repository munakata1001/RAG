import React, { useState, useEffect } from "react";
import { api } from "../api/client";

export default function AnswerBox({ query, contexts, answer: initialAnswer }) {
  const [answer, setAnswer] = useState(initialAnswer || "");
  const [loading, setLoading] = useState(false);

  // initialAnswerが変更されたら更新
  useEffect(() => {
    if (initialAnswer) {
      setAnswer(initialAnswer);
    }
  }, [initialAnswer]);

  const generate = async () => {
    if (!query || !contexts?.length) return;
    setLoading(true);
    try {
      const payload = {
        query,
        contexts: contexts.map((c) => ({
          text: c.text || c.metadata?.text || "",
          score: c.score,
          filename: c.filename || c.metadata?.filename || "",
          chunk_id: c.chunk_id || c.metadata?.chunk_id,
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
    try {
      await navigator.clipboard.writeText(answer);
      alert("コピーしました");
    } catch (err) {
      console.error("コピーに失敗しました", err);
    }
  };

  return (
    <div className="card" style={{ backgroundColor: "#f9f9f9", border: "2px solid #4CAF50" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <h3 style={{ margin: 0, color: "#4CAF50" }}>🤖 AI回答</h3>
        {answer && (
          <button 
            onClick={copyToClipboard} 
            disabled={!answer}
            style={{ padding: "4px 12px", fontSize: "0.9em" }}
          >
            📋 コピー
          </button>
        )}
      </div>
      
      {answer ? (
        <div style={{ 
          whiteSpace: "pre-wrap", 
          padding: "16px", 
          backgroundColor: "white",
          borderRadius: "4px",
          border: "1px solid #ddd",
          lineHeight: "1.6"
        }}>
          {answer}
        </div>
      ) : (
        <div>
          {contexts?.length > 0 ? (
            <div>
              <p style={{ color: "#666", marginBottom: "12px" }}>
                検索結果を基に回答を生成します
              </p>
              <button 
                onClick={generate} 
                disabled={loading || !contexts?.length || !query}
                style={{ 
                  padding: "8px 16px", 
                  fontSize: "1em",
                  backgroundColor: loading || !contexts?.length || !query ? "#ccc" : "#4CAF50",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: loading || !contexts?.length || !query ? "not-allowed" : "pointer"
                }}
              >
                {loading ? "生成中..." : "回答を生成"}
              </button>
            </div>
          ) : (
            <p style={{ color: "#999" }}>検索結果がありません</p>
          )}
        </div>
      )}
      
      {contexts?.length > 0 && (
        <div style={{ marginTop: "12px", fontSize: "0.9em", color: "#666" }}>
          <strong>参考:</strong> {contexts.length}件のドキュメントから生成
          {contexts[0]?.score && (
            <span>（最高スコア: {contexts[0].score.toFixed(3)}）</span>
          )}
        </div>
      )}
    </div>
  );
}


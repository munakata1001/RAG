import React, { useState } from "react";
import { api } from "../api/client";

export default function SearchBox({ onResults, onSearchStart, onRAGResult, useRAG = true }) {
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);

  const doSearch = async () => {
    if (!q) return;
    setLoading(true);
    onSearchStart?.();
    
    try {
      if (useRAG) {
        // RAGエンドポイントを使用（検索+生成）
        const res = await api.post("/rag", { 
          query: q, 
          top_k: 5,
          max_tokens: 3000,  // より詳細な回答を生成
          temperature: 0.2   // より一貫性と正確性を重視
        });
        onRAGResult?.(q, res.data);
        // 検索結果も返す（後方互換性のため）
        onResults?.(q, res.data.contexts || []);
      } else {
        // 検索のみ
        const res = await api.post("/search", { query: q, top_k: 5 });
        onResults?.(q, res.data);
      }
    } catch (err) {
      console.error("検索エラー:", err);
      let errorMessage = "検索に失敗しました";
      
      if (err.response) {
        // サーバーからのレスポンスがある場合
        errorMessage = err.response.data?.detail || err.response.statusText || `HTTP ${err.response.status}`;
        if (err.response.status === 404) {
          errorMessage = "エンドポイントが見つかりません。バックエンドサーバーが起動しているか確認してください。";
        }
      } else if (err.request) {
        // リクエストは送信されたが、レスポンスがない場合
        errorMessage = "バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。";
      } else {
        // リクエストの設定中にエラーが発生した場合
        errorMessage = err.message || "検索に失敗しました";
      }
      
      const errorDetails = {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        statusText: err.response?.statusText,
        url: err.config?.url,
        baseURL: err.config?.baseURL,
        fullURL: err.config?.baseURL ? `${err.config.baseURL}${err.config.url}` : err.config?.url,
        method: err.config?.method?.toUpperCase(),
      };
      console.error("詳細エラー情報:", errorDetails);
      
      // デバッグ用: エンドポイントの確認
      if (err.response?.status === 404) {
        console.error("404エラーの可能性:");
        console.error("- リクエストURL:", errorDetails.fullURL);
        console.error("- バックエンドサーバーが起動しているか確認してください");
        console.error("- http://localhost:8000/docs でエンドポイント一覧を確認できます");
      }
      
      alert(`エラー: ${errorMessage}`);
      onResults?.(q, []);
      onRAGResult?.(q, null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      doSearch();
    }
  };

  return (
    <div className="card">
      <div style={{ display: "flex", gap: "8px", alignItems: "center", marginBottom: "8px" }}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="質問（日本語）を入力"
          style={{ flex: 1, padding: "8px" }}
          disabled={loading}
        />
        <button onClick={doSearch} disabled={loading || !q}>
          {loading ? "検索中..." : useRAG ? "RAG検索" : "検索"}
        </button>
      </div>
      <div style={{ fontSize: "0.9em", color: "#666" }}>
        {useRAG ? "💡 RAGモード: 検索結果を基にAIが回答を生成します" : "🔍 検索モード: 関連ドキュメントのみ表示します"}
      </div>
    </div>
  );
}


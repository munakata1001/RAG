import React, { useState } from "react";
import SearchBox from "../components/SearchBox";
import SearchResults from "../components/SearchResults";
import AnswerBox from "../components/AnswerBox";

export default function Home() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [ragResult, setRagResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useRAG, setUseRAG] = useState(true);

  const handleResults = (q, res) => {
    setQuery(q);
    setResults(res);
    setLoading(false);
  };

  const handleRAGResult = (q, ragData) => {
    setQuery(q);
    if (ragData) {
      setRagResult(ragData);
      setResults(ragData.contexts || []);
    } else {
      setRagResult(null);
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h2>S3Vectors RAG検索</h2>
        <label style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            type="checkbox"
            checked={useRAG}
            onChange={(e) => setUseRAG(e.target.checked)}
          />
          <span>RAGモード（AI回答生成）</span>
        </label>
      </div>
      
      <SearchBox 
        onSearchStart={() => setLoading(true)} 
        onResults={handleResults}
        onRAGResult={handleRAGResult}
        useRAG={useRAG}
      />
      
      {loading && <p style={{ textAlign: "center", color: "#666" }}>検索・生成中...</p>}
      
      {/* RAG結果がある場合は回答を表示 */}
      {ragResult && useRAG && (
        <div style={{ marginBottom: "24px" }}>
          <AnswerBox 
            query={ragResult.query} 
            answer={ragResult.answer || ""}
            contexts={ragResult.contexts || []} 
          />
        </div>
      )}
      
      {/* エラーメッセージ表示 */}
      {!loading && useRAG && !ragResult && query && (
        <div style={{ padding: "16px", backgroundColor: "#fff3cd", border: "1px solid #ffc107", borderRadius: "4px", marginBottom: "16px" }}>
          <p style={{ margin: 0, color: "#856404" }}>
            ⚠️ 回答を生成できませんでした。ドキュメントがアップロードされているか確認してください。
          </p>
        </div>
      )}
      
      {/* 検索結果を表示 */}
      {results.length > 0 && (
        <div>
          <h3>関連ドキュメント（{results.length}件）</h3>
          <SearchResults results={results} />
        </div>
      )}
      
      {/* RAGモードでない場合、従来のAnswerBoxも表示 */}
      {results.length > 0 && !useRAG && (
        <AnswerBox query={query} contexts={results} />
      )}
    </div>
  );
}







import React, { useEffect, useState } from "react";
import { adminApi } from "../api/adminClient";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const res = await adminApi.get("/dashboard");
      setData(res.data);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (error) {
    return (
      <div className="card">
        <h3>ダッシュボード</h3>
        <p className="error">{error}</p>
        <button onClick={load}>再読み込み</button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="card">
        <h3>ダッシュボード</h3>
        <p>読み込み中...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>📊 RAG 管理ダッシュボード</h3>
        <button onClick={load}>更新</button>
      </div>
      <div style={{ display: "grid", gap: "8px" }}>
        <p>
          <b>📁 登録文書数：</b> {data.documents}
        </p>
        <p>
          <b>🧩 総チャンク数：</b> {data.chunks}
        </p>
        <p>
          <b>⏱ 最新アップロード：</b> {data.latest_upload || "なし"}
        </p>
        <p>
          <b>🧠 Embeddingモデル：</b> {data.embedding_model}
        </p>
        <p>
          <b>📐 ベクトル次元：</b> {data.vector_dimension}
        </p>
        <p>
          <b>📦 ベクトルインデックス：</b> {data.vector_index}
        </p>
        <p>
          <b>⚙️ APIステータス：</b>{" "}
          <span style={{ color: "green" }}>{data.status}</span>
        </p>
      </div>
    </div>
  );
}


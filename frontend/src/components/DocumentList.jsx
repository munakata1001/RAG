import React, { useEffect, useState } from "react";
import { adminApi } from "../api/adminClient";

export default function DocumentList() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDocs = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await adminApi.get("/documents");
      setDocs(res.data || []);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteDoc = async (filename) => {
    if (!window.confirm(`${filename} を削除しますか？`)) return;
    try {
      await adminApi.delete(`/documents/${encodeURIComponent(filename)}`);
      setDocs((prev) => prev.filter((doc) => doc.filename !== filename));
    } catch (err) {
      console.error(err);
      alert("削除に失敗しました: " + (err.response?.data?.detail || err.message));
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <h3>登録文書一覧</h3>
        <button onClick={fetchDocs}>再読み込み</button>
      </div>
      {loading && <p>読み込み中...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !docs.length && <p>登録済みの文書がありません。</p>}
      {!loading && docs.length > 0 && (
        <table className="doc-table">
          <thead>
            <tr>
              <th>タイトル</th>
              <th>ファイル名</th>
              <th>カテゴリ</th>
              <th>更新日時</th>
              <th>アクション</th>
            </tr>
          </thead>
          <tbody>
            {docs.map((doc) => (
              <tr key={doc.filename}>
                <td>{doc.title || doc.filename}</td>
                <td>{doc.filename}</td>
                <td>{doc.category || "未分類"}</td>
                <td>{doc.last_updated || doc.last_modified || "-"}</td>
                <td>
                  <button onClick={() => deleteDoc(doc.filename)}>削除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


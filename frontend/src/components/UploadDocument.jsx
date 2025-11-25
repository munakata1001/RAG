import React, { useState } from "react";
import { adminApi } from "../api/adminClient";

const categories = ["設計書", "インフラ", "手順書", "その他"];

export default function UploadDocument() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");
  const [meta, setMeta] = useState({
    title: "",
    category: "",
    project: "",
    notes: "",
  });

  const onFieldChange = (e) => {
    const { name, value } = e.target;
    setMeta((prev) => ({ ...prev, [name]: value }));
  };

  const upload = async () => {
    if (!file) {
      setStatus("ファイルを選択してください");
      return;
    }
    setStatus("アップロード中...");
    try {
      const fd = new FormData();
      fd.append("file", file);
      Object.entries(meta).forEach(([key, value]) => {
        if (value) {
          fd.append(key, value);
        }
      });
      const res = await adminApi.post("/upload_and_register", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus(`登録完了：${res.data.chunks} チャンク（index: ${res.data.index}）`);
      setFile(null);
    } catch (err) {
      console.error(err);
      setStatus("エラー: " + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="card">
      <h3>文書アップロード</h3>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <div className="form-grid">
        <label>
          タイトル
          <input
            name="title"
            value={meta.title}
            onChange={onFieldChange}
            placeholder="例: 認証方式ガイド"
          />
        </label>
        <label>
          カテゴリ
          <select name="category" value={meta.category} onChange={onFieldChange}>
            <option value="">選択してください</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </label>
        <label>
          プロジェクト
          <input
            name="project"
            value={meta.project}
            onChange={onFieldChange}
            placeholder="任意"
          />
        </label>
        <label>
          備考
          <textarea
            name="notes"
            value={meta.notes}
            onChange={onFieldChange}
            rows={2}
            placeholder="キーワードなど"
          />
        </label>
      </div>
      <div style={{ marginTop: 8 }}>
        <button onClick={upload}>アップロード & 登録</button>
      </div>
      <p>{status}</p>
    </div>
  );
}

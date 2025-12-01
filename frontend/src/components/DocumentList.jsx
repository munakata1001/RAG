import React, { useEffect, useState } from "react";

const DocumentList = () => {
  const [docs, setDocs] = useState([]); // 初期値を配列に
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docContent, setDocContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const fetchDocs = async () => {
    try {
      const res = await fetch("/api/list_docs");
      const data = await res.json();
      // 配列であることを保証
      setDocs(Array.isArray(data.docs) ? data.docs : []);
    } catch (err) {
      console.error("ドキュメント取得エラー:", err);
      setDocs([]);
    }
  };

  useEffect(() => {
    fetchDocs();
    // 定期的に一覧を更新（30秒ごと）
    const interval = setInterval(fetchDocs, 30000);
    
    // アップロード成功時に一覧を更新
    const handleDocumentUploaded = () => {
      fetchDocs();
    };
    window.addEventListener("documentUploaded", handleDocumentUploaded);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener("documentUploaded", handleDocumentUploaded);
    };
  }, []);

  const handleDocClick = async (doc) => {
    setSelectedDoc(doc);
    setLoading(true);
    setShowModal(true);
    try {
      const res = await fetch(`/api/document/${encodeURIComponent(doc.filename)}`);
      const data = await res.json();
      setDocContent(data.content || "内容が取得できませんでした");
    } catch (err) {
      console.error("ドキュメント内容取得エラー:", err);
      setDocContent("エラー: ドキュメント内容の取得に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedDoc(null);
    setDocContent("");
  };

  const handleDelete = async (doc, e) => {
    e.stopPropagation(); // クリックイベントの伝播を止める
    
    if (!window.confirm(`「${doc.filename}」を削除してもよろしいですか？\nこの操作は取り消せません。`)) {
      return;
    }
    
    try {
      const res = await fetch(`/api/document/${encodeURIComponent(doc.filename)}`, {
        method: "DELETE",
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "削除に失敗しました");
      }
      
      const data = await res.json();
      alert(`削除完了: ${data.deleted_items.join(", ")}`);
      
      // 一覧を更新
      fetchDocs();
      
      // モーダルが開いていたら閉じる
      if (selectedDoc && selectedDoc.filename === doc.filename) {
        closeModal();
      }
    } catch (err) {
      console.error("ドキュメント削除エラー:", err);
      alert("エラー: " + (err.message || "ドキュメントの削除に失敗しました"));
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h2>ドキュメント一覧</h2>
        <button onClick={fetchDocs} style={{ padding: "8px 16px", cursor: "pointer" }}>
          更新
        </button>
      </div>
      {docs.length === 0 ? (
        <p>ドキュメントが存在しません</p>
      ) : (
        docs.map((doc, index) => (
          <div
            key={doc.filename || index}
            onClick={() => handleDocClick(doc)}
            style={{
              marginBottom: "16px",
              padding: "12px",
              border: "1px solid #ddd",
              borderRadius: "4px",
              cursor: "pointer",
              transition: "background-color 0.2s",
              position: "relative",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#f5f5f5")}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "transparent")}
          >
            <button
              onClick={(e) => handleDelete(doc, e)}
              style={{
                position: "absolute",
                top: "8px",
                right: "8px",
                padding: "6px 16px",
                backgroundColor: "#dc3545",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.9em",
                fontWeight: "bold",
                boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = "#c82333";
                e.currentTarget.style.transform = "scale(1.05)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = "#dc3545";
                e.currentTarget.style.transform = "scale(1)";
              }}
              title="このドキュメントを削除します"
            >
              🗑️ 削除
            </button>
            <p><strong>ファイル名:</strong> {doc.filename}</p>
            {doc.title && <p><strong>タイトル:</strong> {doc.title}</p>}
            {doc.category && <p><strong>カテゴリ:</strong> {doc.category}</p>}
            {doc.project && <p><strong>プロジェクト:</strong> {doc.project}</p>}
            {doc.notes && <p><strong>備考:</strong> {doc.notes}</p>}
            <p><strong>ファイル形式:</strong> {doc.file_type}</p>
            {doc.last_modified && <p><strong>最終更新:</strong> {new Date(doc.last_modified).toLocaleString("ja-JP")}</p>}
            <p style={{ marginTop: "8px", color: "#666", fontSize: "0.9em" }}>クリックして内容を表示</p>
          </div>
        ))
      )}

      {/* モーダル */}
      {showModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
          onClick={closeModal}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "24px",
              borderRadius: "8px",
              maxWidth: "80%",
              maxHeight: "80%",
              overflow: "auto",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0 }}>
                {selectedDoc?.title || selectedDoc?.filename}
              </h3>
              <div style={{ display: "flex", gap: "8px" }}>
                {selectedDoc && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(selectedDoc, e);
                    }}
                    style={{
                      padding: "6px 16px",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: "4px",
                      cursor: "pointer",
                      fontSize: "0.9em",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = "#c82333")}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = "#dc3545")}
                  >
                    🗑️ 削除
                  </button>
                )}
                <button
                  onClick={closeModal}
                  style={{
                    padding: "6px 16px",
                    cursor: "pointer",
                    border: "1px solid #ddd",
                    borderRadius: "4px",
                    backgroundColor: "#f5f5f5",
                  }}
                >
                  × 閉じる
                </button>
              </div>
            </div>
            {selectedDoc && (
              <div style={{ marginBottom: "16px", color: "#666", fontSize: "0.9em" }}>
                <p><strong>ファイル名:</strong> {selectedDoc.filename}</p>
                {selectedDoc.category && <p><strong>カテゴリ:</strong> {selectedDoc.category}</p>}
                {selectedDoc.project && <p><strong>プロジェクト:</strong> {selectedDoc.project}</p>}
              </div>
            )}
            <div
              style={{
                border: "1px solid #ddd",
                borderRadius: "4px",
                padding: "16px",
                backgroundColor: "#f9f9f9",
                whiteSpace: "pre-wrap",
                maxHeight: "60vh",
                overflow: "auto",
              }}
            >
              {loading ? (
                <p>読み込み中...</p>
              ) : (
                <p style={{ margin: 0 }}>{docContent}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentList;

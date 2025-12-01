import React, { useEffect, useState } from "react";

const UsageLog = () => {
  const [logs, setLogs] = useState([]); // 初期値を配列に

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("/api/usage_logs"); // 適切なAPIに変更
        const data = await res.json();
        // 配列であることを保証
        setLogs(Array.isArray(data.logs) ? data.logs : []);
      } catch (err) {
        console.error("使用ログ取得エラー:", err);
        setLogs([]);
      }
    };

    fetchLogs();
  }, []);

  return (
    <div>
      <h2>使用ログ</h2>
      {logs.length === 0 ? (
        <p>ログはありません</p>
      ) : (
        logs.map((log) => (
          <div key={log.id}>
            <p>アクション: {log.action}</p>
            <p>日時: {log.timestamp}</p>
          </div>
        ))
      )}
    </div>
  );
};

export default UsageLog;

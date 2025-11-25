import React, { useEffect, useState } from "react";
import { adminApi } from "../api/adminClient";

const POLLING_INTERVAL = 60_000;

export default function UsageLog() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchLogs = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await adminApi.get("/logs", { params: { limit: 50 } });
      setLogs(res.data || []);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const timer = setInterval(fetchLogs, POLLING_INTERVAL);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <h3>利用ログ</h3>
        <button onClick={fetchLogs}>更新</button>
      </div>
      {loading && <p>読み込み中...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !logs.length && <p>まだログはありません。</p>}
      {!loading && logs.length > 0 && (
        <table className="log-table">
          <thead>
            <tr>
              <th>日時</th>
              <th>アクション</th>
              <th>詳細</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, idx) => (
              <tr key={`${log.timestamp}-${idx}`}>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.action}</td>
                <td>
                  <pre className="log-detail">{JSON.stringify(log.detail, null, 2)}</pre>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}


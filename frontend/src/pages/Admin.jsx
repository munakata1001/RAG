import React from "react";
import UploadDocument from "../components/UploadDocument";
import DocumentList from "../components/DocumentList";
import AdminDashboard from "../components/AdminDashboard";
import UsageLog from "../components/UsageLog";

export default function Admin() {
  return (
    <div className="admin-page">
      <h2>文書管理コンソール</h2>
      <div className="admin-grid">
        <AdminDashboard />
        <UploadDocument />
        <DocumentList />
        <UsageLog />
      </div>
    </div>
  );
}

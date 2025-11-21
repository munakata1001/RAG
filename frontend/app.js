document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://127.0.0.1:8000/api';
    const tableBody = document.querySelector('#documents-table tbody');
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadStatus = document.getElementById('upload-status');

    // --- 関数定義 ---

    /**
     * 登録済みの文書一覧を取得してテーブルに表示する
     */
    async function fetchDocuments() {
        try {
            const response = await fetch(`${API_BASE_URL}/documents`);
            if (!response.ok) {
                throw new Error('文書一覧の取得に失敗しました');
            }
            const documents = await response.json();
            
            tableBody.innerHTML = ''; // テーブルをクリア

            documents.forEach(doc => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${doc.filename}</td>
                    <td>${doc.file_type}</td>
                    <td>${new Date(doc.last_modified).toLocaleString()}</td>
                    <td><button class="delete-btn" data-filename="${doc.filename}">削除</button></td>
                `;
                tableBody.appendChild(row);
            });

        } catch (error) {
            console.error(error);
            tableBody.innerHTML = '<tr><td colspan="4">データの読み込みに失敗しました。</td></tr>';
        }
    }

    /**
     * 指定された文書を削除する
     * @param {string} filename - 削除するファイル名
     */
    async function deleteDocument(filename) {
        if (!confirm(`本当に「${filename}」を削除しますか？`)) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/documents/${filename}`, {
                method: 'DELETE',
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '削除に失敗しました');
            }
            
            alert('削除しました。');
            fetchDocuments(); // 一覧を再読み込み

        } catch (error) {
            console.error(error);
            alert(`エラー: ${error.message}`);
        }
    }

    /**
     * ファイルをアップロードする
     */
    async function uploadDocument() {
        const file = fileInput.files[0];
        if (!file) {
            alert('ファイルを選択してください。');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        uploadStatus.textContent = 'アップロード中...';
        uploadBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'アップロードに失敗しました');
            }
            
            const result = await response.json();
            uploadStatus.textContent = `アップロード成功: ${result.filename}`;
            fileInput.value = ''; // ファイル選択をクリア
            fetchDocuments(); // 一覧を再読み込み

        } catch (error) {
            console.error(error);
            uploadStatus.textContent = `エラー: ${error.message}`;
        } finally {
            uploadBtn.disabled = false;
        }
    }


    // --- イベントリスナー ---

    // 削除ボタンのクリックイベント（イベント委任）
    tableBody.addEventListener('click', (event) => {
        if (event.target.classList.contains('delete-btn')) {
            const filename = event.target.dataset.filename;
            deleteDocument(filename);
        }
    });

    // アップロードボタンのクリックイベント
    uploadBtn.addEventListener('click', uploadDocument);

    // --- 初期表示 ---
    fetchDocuments();
});

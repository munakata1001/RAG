import re
from typing import List


def clean_text(text: str) -> str:
    """不要な空白や改行を整える"""
    if not text:
        return ""

    # 連続改行 → 1つに圧縮
    text = re.sub(r"\n\s*\n", "\n", text)

    # 前後の空白削除
    text = text.strip()

    return text


def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    テキストをチャンク化する処理。
    overlap をつけることで文脈の繋がりを保つ。

    chunk_size: 1チャンクの最大文字数
    overlap: チャンク間の重複（文脈保持）
    """

    text = clean_text(text)
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = start + chunk_size

        # 範囲が長すぎると文途中で切れるので調整
        if end < length:
            # 「文章の切れ目（句点・改行）」を探す
            cut_pos = max(
                text.rfind("。", start, end),
                text.rfind("、", start, end),
                text.rfind("\n", start, end)
            )

            # 見つかったらそこまでをチャンクとする
            if cut_pos != -1 and cut_pos > start:
                end = cut_pos + 1  # 句点を含む
        # チャンク追加
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # オーバーラップ分戻して次へ
        start = end - overlap
        if start < 0:
            start = 0

    return chunks


def split_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    従来の関数名との互換用ラッパー。
    """
    return split_into_chunks(text, chunk_size=chunk_size, overlap=overlap)
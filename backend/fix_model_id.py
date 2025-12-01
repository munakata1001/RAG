"""
BedrockモデルIDを標準版に修正するスクリプト
"""
import os
from pathlib import Path

def fix_model_id():
    """`.env`ファイルのBEDROCK_MODEL_IDを標準版に修正"""
    script_dir = Path(__file__).parent
    env_path = script_dir / ".env"
    
    if not env_path.exists():
        print("⚠️  .envファイルが見つかりません")
        print(f"   パス: {env_path}")
        print()
        print("手動で.envファイルを作成し、以下を追加してください:")
        print("BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0")
        return False
    
    # .envファイルを読み込む
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # BEDROCK_MODEL_IDを探して更新
    updated = False
    new_lines = []
    
    for line in lines:
        if line.strip().startswith("BEDROCK_MODEL_ID"):
            # 既存の値を確認
            if ":28k" in line or ":200k" in line:
                # 標準版に変更
                new_line = "BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0\n"
                new_lines.append(new_line)
                updated = True
                print(f"✓ モデルIDを更新しました:")
                print(f"  変更前: {line.strip()}")
                print(f"  変更後: {new_line.strip()}")
            else:
                # 既に標準版の場合はそのまま
                new_lines.append(line)
                print(f"✓ モデルIDは既に標準版です: {line.strip()}")
        else:
            new_lines.append(line)
    
    # 更新があった場合はファイルに書き込む
    if updated:
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print()
        print("✓ .envファイルを更新しました")
        return True
    else:
        # BEDROCK_MODEL_IDが見つからない場合は追加
        if not any("BEDROCK_MODEL_ID" in line for line in lines):
            print("⚠️  BEDROCK_MODEL_IDが見つかりません。追加します...")
            new_lines.append("\n# Bedrock Model ID\n")
            new_lines.append("BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            print("✓ BEDROCK_MODEL_IDを追加しました")
            return True
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("BedrockモデルID修正スクリプト")
    print("=" * 60)
    print()
    
    fix_model_id()
    
    print()
    print("=" * 60)
    print("完了")
    print("=" * 60)
    print()
    print("次のステップ:")
    print("1. python test_bedrock.py を実行して確認")
    print("2. エラーが解消されない場合は、python list_bedrock_models.py で利用可能なモデルを確認")


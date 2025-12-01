"""
Bedrockで利用可能なモデル一覧を取得するスクリプト
"""
import boto3
import os
import json
import sys

# .envファイルを読み込む
try:
    from dotenv import load_dotenv
    # スクリプトのディレクトリを基準に.envファイルを探す
    if getattr(sys, 'frozen', False):
        # PyInstallerでパッケージ化された場合
        script_dir = os.path.dirname(sys.executable)
    else:
        # 通常の実行
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    env_path = os.path.join(script_dir, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"✓ .envファイルを読み込みました: {env_path}")
    else:
        # カレントディレクトリからも探す
        load_dotenv(override=True)
except ImportError:
    print("⚠️  python-dotenvがインストールされていません")
    print("   pip install python-dotenv でインストールしてください")
except Exception as e:
    print(f"⚠️  .envファイルの読み込みに失敗: {e}")

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
# デフォルトモデルID: 28kコンテキストウィンドウ版を使用
DEFAULT_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0:28k"

def list_bedrock_models():
    """利用可能なBedrockモデル一覧を取得"""
    print("=" * 60)
    print("Bedrockモデル一覧")
    print("=" * 60)
    print(f"リージョン: {AWS_REGION}")
    print()
    
    try:
        bedrock = boto3.client("bedrock", region_name=AWS_REGION)
        
        print("モデル一覧を取得中...")
        response = bedrock.list_foundation_models()
        
        models = response.get("modelSummaries", [])
        
        if not models:
            print("⚠️  モデルが見つかりませんでした")
            return
        
        print(f"✓ {len(models)}件のモデルが見つかりました")
        print()
        
        # モデルをプロバイダーごとに分類
        by_provider = {}
        for model in models:
            provider = model.get("providerName", "Unknown")
            if provider not in by_provider:
                by_provider[provider] = []
            by_provider[provider].append(model)
        
        # 各プロバイダーのモデルを表示
        for provider, provider_models in sorted(by_provider.items()):
            print(f"\n【{provider}】")
            print("-" * 60)
            
            for model in provider_models:
                model_id = model.get("modelId", "Unknown")
                model_name = model.get("modelName", "Unknown")
                input_modalities = model.get("inputModalities", [])
                output_modalities = model.get("outputModalities", [])
                
                print(f"モデルID: {model_id}")
                print(f"  名前: {model_name}")
                print(f"  入力: {', '.join(input_modalities) if input_modalities else 'N/A'}")
                print(f"  出力: {', '.join(output_modalities) if output_modalities else 'N/A'}")
                print()
        
        # Claude 3モデルを強調表示
        print("\n" + "=" * 60)
        print("Claude 3モデル（推奨）")
        print("=" * 60)
        claude_models = [m for m in models if "claude-3" in m.get("modelId", "").lower()]
        
        if claude_models:
            # 通常版と28k版を分類
            standard_models = []
            extended_models = []
            
            for model in claude_models:
                model_id = model.get("modelId", "Unknown")
                if ":28k" in model_id or ":200k" in model_id:
                    extended_models.append(model)
                else:
                    standard_models.append(model)
            
            if standard_models:
                print("【標準版モデル（推奨）】")
                for model in standard_models:
                    model_id = model.get("modelId", "Unknown")
                    model_name = model.get("modelName", "Unknown")
                    print(f"✓ {model_id}")
                    print(f"  名前: {model_name}")
                    print()
            
            if extended_models:
                print("【拡張コンテキスト版モデル】")
                for model in extended_models:
                    model_id = model.get("modelId", "Unknown")
                    model_name = model.get("modelName", "Unknown")
                    print(f"  {model_id}")
                    print(f"  名前: {model_name}")
                    print("  ⚠️  拡張コンテキスト版は、通常のモデルIDとは異なる形式です")
                    print()
        else:
            print("⚠️  Claude 3モデルが見つかりませんでした")
            print("   モデルアクセスが有効化されていない可能性があります")
        
        # 現在の設定を確認
        print("\n" + "=" * 60)
        print("現在の設定")
        print("=" * 60)
        current_model_id = os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID)
        print(f"BEDROCK_MODEL_ID: {current_model_id}")
        
        # 現在のモデルIDが利用可能か確認
        available_model_ids = [m.get("modelId") for m in models]
        if current_model_id in available_model_ids:
            print(f"✓ 現在のモデルIDは利用可能です")
        else:
            print(f"⚠️  現在のモデルIDは利用可能なモデル一覧にありません")
            print(f"   利用可能なClaude 3モデル:")
            for model_id in [m.get("modelId") for m in claude_models]:
                print(f"     - {model_id}")
        
    except Exception as e:
        error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "Unknown")
        error_message = getattr(e, "response", {}).get("Error", {}).get("Message", str(e))
        
        print(f"✗ モデル一覧の取得に失敗しました")
        print(f"  エラーコード: {error_code}")
        print(f"  エラーメッセージ: {error_message}")
        print()
        
        if error_code == "UnrecognizedClientException":
            print("解決方法:")
            print("1. AWS認証情報が正しく設定されているか確認")
            print("2. IAMユーザーにBedrock権限があるか確認")
            print("3. リージョンが正しいか確認")
        elif error_code == "AccessDeniedException":
            print("解決方法:")
            print("1. IAMユーザーにbedrock:ListFoundationModels権限を付与")
            print("2. または、AmazonBedrockFullAccessポリシーをアタッチ")

if __name__ == "__main__":
    list_bedrock_models()


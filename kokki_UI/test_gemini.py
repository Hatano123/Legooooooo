import os
import google.generativeai as genai

print("--- 最小構成でのテストを開始 ---")

try:
    # 1. 環境変数からAPIキーを読み込む
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("エラー: 環境変数 'GEMINI_API_KEY' が設定されていません。")
    
    print("APIキーを正常に読み込みました。")

    # 2. APIキーを設定
    genai.configure(api_key=api_key)

    # 3. モデルを準備
    print("モデル 'gemini-1.5-flash-001' を準備します...")
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # 4. テキストを生成
    print("テキスト生成をリクエストします...")
    response = model.generate_content("こんにちは")

    # 5. 結果を表示
    print("\n--- 成功！AIからの応答 ---")
    print(response.text)
    print("--------------------------")

except Exception as e:
    print(f"\n--- テスト中にエラーが発生しました ---")
    print(f"エラー内容: {e}")
    print("------------------------------------")
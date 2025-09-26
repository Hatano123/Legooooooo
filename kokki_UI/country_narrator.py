import google.generativeai as genai
from google.api_core import exceptions

def narrate_country_info(country_name, api_key):
    """
    国名を受け取り、その国の豆知識を生成して「テキスト」を返します。
    """
    if not country_name or not api_key:
        print("エラー: 国名とAPIキーは必須です。")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"{country_name}について、親しみやすい口調で、面白い豆知識を交えながら紹介してください。最初の挨拶は無し。文字数は100字以内。"
        
        print(f"「{country_name}」についてAIが文章を生成中です...")
        response = model.generate_content(prompt)
        print("文章の生成が完了しました。")
        
        # 不要な文字を削除してテキストを返す
        cleaned_text = response.text.replace('\n', ' ').replace('\r', '').strip()
        return cleaned_text

    # 具体的なエラーごとに対処を追加
    except exceptions.NotFound as e:
        print(f"モデルが見つかりませんでした。モデル名を確認してください: {e}")
        return None
    except exceptions.PermissionDenied as e:
        print(f"APIキーが無効か、APIが有効になっていません。キーとプロジェクト設定を確認してください: {e}")
        return None
    except Exception as e:
        print(f"AIからのテキスト生成中に予期せぬエラーが発生しました: {e}")
        return None
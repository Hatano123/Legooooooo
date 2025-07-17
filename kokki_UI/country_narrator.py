import google.generativeai as genai

def narrate_country_info(country_name, api_key):
    """
    国名を受け取り、その国の豆知識を生成して「テキスト」を返します。
    """
    if not country_name or not api_key:
        print("エラー: 国名とAPIキーは必須です。")
        return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"{country_name}について、VOICEVOXのキャラクターが読み上げることを想定して、150文字程度の面白い豆知識を交えながら紹介してください。最初の挨拶は必要ありません。"
        
        print(f"「{country_name}」についてAIが文章を生成中です...")
        response = model.generate_content(prompt)
        print("文章の生成が完了しました。")
        
        # 不要な文字を削除してテキストを返す
        cleaned_text = response.text.replace('\n', ' ').replace('\r', '').strip()
        return cleaned_text

    except Exception as e:
        print(f"AIからのテキスト生成中にエラーが発生しました: {e}")
        return None
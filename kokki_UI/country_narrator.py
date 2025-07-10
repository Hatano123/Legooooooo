import google.generativeai as genai
import requests
import json
import io
import simpleaudio as sa

# --- AIによるテキスト生成関数 (内部ヘルパー) ---
def _generate_country_info(country_name, api_key):
    """
    Gemini APIを使用して、指定された国に関する情報を生成します。(内部でのみ使用)
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"{country_name}について、VOICEVOXのキャラクターが読み上げることを想定して、150文字程度の面白い豆知識を交えながら紹介してください。最初の挨拶は必要ありません。"
        
        print(f"「{country_name}」についてAIが文章を生成中です...")
        response = model.generate_content(prompt)
        print("文章の生成が完了しました。")
        return response.text

    except Exception as e:
        print(f"AIからのテキスト生成中にエラーが発生しました: {e}")
        return None

# --- VOICEVOXによる音声合成・再生関数 (内部ヘルパー) ---
def _speak_with_voicevox(text, speaker_id, voicevox_url):
    """
    VOICEVOX APIを使用してテキストを音声に変換し、再生します。(内部でのみ使用)
    """
    try:
        # 1. audio_query
        params = {"text": text, "speaker": speaker_id}
        res_query = requests.post(f"{voicevox_url}/audio_query", params=params, timeout=10)
        res_query.raise_for_status() # エラーがあれば例外を発生させる
        query_data = res_query.json()

        # 2. synthesis
        headers = {"Content-Type": "application/json"}
        res_synth = requests.post(f"{voicevox_url}/synthesis", headers=headers, params={"speaker": speaker_id}, data=json.dumps(query_data), timeout=10)
        res_synth.raise_for_status() # エラーがあれば例外を発生させる
        wav_data = res_synth.content

        # 3. 再生
        print("\n--- 再生開始 ---")
        print(f"キャラクター (ID:{speaker_id}): 『{text}』")
        wave_obj = sa.WaveObject.from_wave_file(io.BytesIO(wav_data))
        play_obj = wave_obj.play()
        play_obj.wait_done()
        print("--- 再生完了 ---")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\nエラー: VOICEVOXに接続できません。")
        print(f"VOICEVOXソフトウェアが起動しているか、アドレス({voicevox_url})が正しいか確認してください。")
        print(f"詳細: {e}")
        return False
    except Exception as e:
        print(f"音声の再生中にエラーが発生しました: {e}")
        return False

# --- メインとなる統合関数 ---
def narrate_country_info(country_name, api_key, speaker_id=3, voicevox_url="http://127.0.0.1:50021"):
    """
    国名を受け取り、その国の豆知識を生成してVOICEVOXで読み上げます。

    Args:
        country_name (str): 情報を知りたい国名。
        api_key (str): Google AI (Gemini) のAPIキー。
        speaker_id (int, optional): VOICEVOXのキャラクターID。デフォルトは3 (ずんだもん)。
        voicevox_url (str, optional): VOICEVOXエンジンのURL。デフォルトは "http://127.0.0.1:50021"。
    """
    if not country_name or not api_key:
        print("エラー: 国名とAPIキーは必須です。")
        return

    # 1. 国の情報をAIに生成させる
    info_text = _generate_country_info(country_name, api_key)

    # 2. 生成されたテキストをVOICEVOXに喋らせる
    if info_text:
        # AIが生成したテキストから改行などの不要な文字を削除
        cleaned_text = info_text.replace('\n', ' ').replace('\r', '').strip()
        
        _speak_with_voicevox(cleaned_text, speaker_id, voicevox_url)


# --- このスクリプトを直接実行した場合の処理 ---
# if __name__ == '__main__':
#     # --- 設定項目 ---
#     # ご自身のGoogle AI (Gemini) APIキーに書き換えてください
#     GEMINI_API_KEY = "AIzaSyCBapA6ViIAj6xc9Yau4zf294PBK1_bi7I" # ★ここにAPIキーを設定してください

#     # VOICEVOXの設定
#     VOICEVOX_URL = "http://127.0.0.1:50021"
#     SPEAKER_ID = 3 # 例: 1=四国めたん(ノーマル), 3=ずんだもん(ノーマル)

#     try:
#         # 情報を知りたい国名を入力
#         target_country = input("情報を知りたい国名を入力してください (例: フランス): ")

#         if target_country:
#             # ★新しく作成した関数を呼び出す
#             narrate_country_info(
#                 country_name=target_country,
#                 api_key=GEMINI_API_KEY,
#                 speaker_id=SPEAKER_ID,
#                 voicevox_url=VOICEVOX_URL
#             )
    
#     except KeyboardInterrupt:
#         print("\nプログラムを終了します。")
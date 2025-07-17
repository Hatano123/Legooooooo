# main_application_simple.py
import os
# simple_video_player_module から動画再生関数をインポート
from videomodu import play_video_once

def run_simple_video_player_app(video_file_path):
    """
    simple_video_player_module を呼び出して動画を再生するアプリケーション。
    """
    print("動画再生アプリケーションを開始します。")

    # 再生したい動画ファイルのパスを指定
    # このスクリプトと同じディレクトリにある 'video' フォルダ内の 'ryugaku.mp4' を想定
    #video_file_path = r'.\video\ryugaku.mp4'

    # 動画ファイルが存在するか確認
    if not os.path.exists(video_file_path):
        print(f"エラー: 指定された動画ファイルが見つかりません。パスを確認してください: {video_file_path}")
        print("動画ファイルはスクリプトと同じディレクトリの 'video' フォルダ内にある必要があります。")
        return # ファイルが見つからない場合は処理を終了

    print(f"動画 '{video_file_path}' の再生を準備中...")

    try:
        # play_video_once 関数を呼び出して動画再生を開始
        # この呼び出しは、動画が終了するか、ウィンドウが閉じられるまでブロックされます。
        play_video_once(video_file_path)

    except Exception as e:
        print(f"動画再生中に予期せぬエラーが発生しました: {e}")
    
    print("動画再生アプリケーションが終了しました。")

if __name__ == '__main__':
    # このスクリプトが直接実行された場合に、動画再生アプリケーションを開始
    run_simple_video_player_app()
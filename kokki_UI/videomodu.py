# simple_video_player_module.py
import pyglet
import os

# このモジュール内で状態を管理するための変数
_player = None
_window = None
_event_loop = None

def run_simple_video_player_app(video_path):
    """
    simple_video_player_module を呼び出して動画を再生するアプリケーション。
    """
    print("動画再生アプリケーションを開始します。")

    # 動画ファイルが存在するか確認
    if not os.path.exists(video_path):
        print(f"エラー: 指定された動画ファイルが見つかりません。パスを確認してください: {video_path}")
        return

    print(f"動画 '{video_path}' の再生を準備中...")

    try:
        play_video_once(video_path)
    except Exception as e:
        print(f"動画再生中に予期せぬエラーが発生しました: {e}")
    
    print("動画再生アプリケーションが終了しました。")

def play_video_once(video_path):
    """
    指定された動画ファイルを再生し、終了したらウィンドウを閉じます。
    このスレッド専用のイベントループを使用して、他のプロセスへの影響を防ぎます。
    """
    global _player, _window, _event_loop

    # このスレッド専用のイベントループを新規に作成
    _event_loop = pyglet.app.EventLoop()

    try:
        _window = pyglet.window.Window(caption='Simple Video Player')
        _player = pyglet.media.Player()
        source = pyglet.media.load(video_path)
        _player.queue(source)

        @_window.event
        def on_draw():
            _window.clear()
            if _player.texture:
                video_width = _player.source.video_format.width
                video_height = _player.source.video_format.height
                aspect_ratio = video_width / video_height
                window_aspect_ratio = _window.width / _window.height

                if aspect_ratio > window_aspect_ratio:
                    display_width = _window.width
                    display_height = int(_window.width / aspect_ratio)
                else:
                    display_height = _window.height
                    display_width = int(_window.height * aspect_ratio)

                offset_x = (_window.width - display_width) / 2
                offset_y = (_window.height - display_height) / 2

                _player.texture.blit(offset_x, offset_y, width=display_width, height=display_height)

        @_player.event
        def on_eos(): # End of Stream (動画の終端) イベント
            print("動画の再生が終了しました。")
            stop_video()

        # ユーザーがウィンドウの[x]ボタンで閉じた場合の処理を追加
        @_window.event
        def on_close():
            print("ウィンドウが閉じられました。")
            stop_video()

        _player.play()
        print(f"動画 '{video_path}' を再生中...")
        _event_loop.run() # ★★★ 専用のイベントループを実行 ★★★

    except Exception as e:
        print(f"動画再生中にエラーが発生しました: {e}")
    finally:
        # ループが終了したら、念のためリソースをクリーンアップ
        if _player or _window:
            stop_video()

def stop_video():
    """再生中の動画を停止し、リソースを解放して、専用イベントループを終了します。"""
    global _player, _window, _event_loop
    
    # 既に停止処理が実行中の場合は、二重に実行しない
    if _event_loop is None:
        return

    print("動画の再生を停止し、リソースを解放しました。")
    if _player:
        _player.pause()
        _player.delete()
        _player = None
    if _window:
        _window.close()
        _window = None
    
    # ★★★ 専用のイベントループを安全に終了させる ★★★
    if _event_loop:
        _event_loop.exit()
        _event_loop = None # 停止処理が終わったことを示す


if __name__ == '__main__':
    test_video_path = r'.\movie\ryugaku1.mp4' # あなたの動画ファイルのパスを指定
    if not os.path.exists(test_video_path):
        print(f"エラー: 動画ファイルが見つかりません: {test_video_path}")
    else:
        play_video_once(test_video_path)
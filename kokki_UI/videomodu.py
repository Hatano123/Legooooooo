# simple_video_player_module.py
import pyglet

_player = None # グローバル変数でプレイヤーを管理（推奨されないが、関数型の場合の一例）
_window = None

def play_video_once(video_path):
    """
    指定された動画ファイルを再生し、終了したらウィンドウを閉じます。
    この関数が呼び出されると、pygletのイベントループが開始され、ブロックされます。
    """
    global _player, _window

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
            stop_video() # 再生終了時に自動で停止処理を呼び出す

        _player.play()
        print(f"動画 '{video_path}' を再生中...")
        pyglet.app.run() # イベントループを開始し、ブロックする

    except Exception as e:
        print(f"動画再生中にエラーが発生しました: {e}")
    finally:
        stop_video()

def stop_video():
    """再生中の動画を停止し、リソースを解放します。"""
    global _player, _window
    if _player:
        _player.pause()
        _player.delete()
        _player = None
    if _window:
        _window.close()
        _window = None
    print("動画の再生を停止し、リソースを解放しました。")
    pyglet.app.exit() # pygletのイベントループを終了

if __name__ == '__main__':
    import os
    test_video_path = r'.\video\ryugaku.mp4' # あなたの動画ファイルのパスを指定
    if not os.path.exists(test_video_path):
        print(f"エラー: 動画ファイルが見つかりません: {test_video_path}")
    else:
        play_video_once(test_video_path)
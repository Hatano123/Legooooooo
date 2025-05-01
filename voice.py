import pyttsx3

engine = pyttsx3.init()

# 読み上げ速度をゆっくりに設定
engine.setProperty('rate', 125)

# 音量を調整
engine.setProperty('volume', 0.9)

# 音声の選択（声の質はシステムによる）
voices = engine.getProperty('voices')
for voice in voices:
    if "child" in voice.name.lower():  # 子供向け音声があれば選択
        engine.setProperty('voice', voice.id)
        break

text = "こんにちは、これは幼児向けの読み上げです。"
engine.say(text)
engine.runAndWait()

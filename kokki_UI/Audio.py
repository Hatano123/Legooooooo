import pygame

class Audio:
    def __init__(self, bgm_volume=0.1, voice_volume=1.0):
        pygame.mixer.init()
        self.bgm_volume = bgm_volume
        self.voice_volume = voice_volume

    def play_bgm(self, file):
        # music.load()は再生中でなくても呼べるため、get_busy()のチェックは不要
        pygame.mixer.music.load(file)
        pygame.mixer.music.set_volume(self.bgm_volume)
        pygame.mixer.music.play(-1)  # 無限ループ

    def stop_bgm(self):
        pygame.mixer.music.stop()

    def play_voice(self, file):
        pygame.mixer.stop()
        voice = pygame.mixer.Sound(file)
        voice.set_volume(self.voice_volume)
        voice.play()
    
    # ★★★ このメソッドを追加 ★★★
    def set_bgm_volume(self, volume):
        """
        再生中のBGMの音量を設定します。
        """
        # pygame.mixer.music.set_volumeは0.0から1.0の範囲の値を受け取ります
        if 0.0 <= volume <= 1.0:
            pygame.mixer.music.set_volume(volume)
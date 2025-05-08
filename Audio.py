import pygame

class Audio:
    def __init__(self, bgm_volume=0.09, voice_volume=1.0):
        pygame.mixer.init()
        self.bgm_volume = bgm_volume
        self.voice_volume = voice_volume

    def play_bgm(self, file):
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self.bgm_volume)
            pygame.mixer.music.load(file)
            pygame.mixer.music.play(-1)  # 無限ループ

    def stop_bgm(self):
        pygame.mixer.music.stop()

    def play_voice(self, file):
        pygame.mixer.stop()
        voice = pygame.mixer.Sound(file)
        voice.set_volume(self.voice_volume)
        voice.play()
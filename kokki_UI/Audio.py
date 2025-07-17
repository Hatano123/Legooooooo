import pygame

class Audio:
    def __init__(self):
        pass
    def play_bgm(self, file):
        if not pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.load(file)
            pygame.mixer.music.play(-1)  # 無限ループ

    def stop_bgm(self):
        pygame.mixer.music.stop()

    def play_voice(self, file):
        pygame.mixer.stop()
        voice = pygame.mixer.Sound(file)
        voice.set_volume(1.0)
        voice.play()
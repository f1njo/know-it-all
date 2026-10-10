import os
import sys
from pathlib import Path

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
try:
    import pygame
except ImportError:
    pygame = None


class Audio:
    def __init__(self, folder=None):
        self.available = False
        self.music_loaded = False
        self.music_muted = False
        self.sfx_muted = False
        self.volume = .5
        self.sounds = {}
        self.owns_mixer = False
        if pygame is None:
            return
        
        if folder:
            folder = Path(folder)
        elif getattr(sys, 'frozen', False):
            folder = Path(sys.executable).resolve().parent / 'media/music'
        else:
            folder = Path(__file__).resolve().parent / 'media/music'

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
                self.owns_mixer = True
            self.available = True
            music = folder / 'Relaxing music.mp3'
            if music.is_file():
                pygame.mixer.music.load(str(music))
                pygame.mixer.music.set_volume(self.volume)
                pygame.mixer.music.play(-1)
                self.music_loaded = True
            for key, filename in (('click', 'Standart btn.mp3'), ('start', 'Game start btn.mp3')):
                path = folder / filename
                if path.is_file():
                    try:
                        self.sounds[key] = pygame.mixer.Sound(str(path))
                    except (pygame.error, OSError):
                        pass
        except (pygame.error, OSError):
            self.close()

    def click(self, kind='click'):
        sound = self.sounds.get(kind)
        if self.available and not self.sfx_muted and sound:
            sound.play()

    def set_music_muted(self, muted):
        self.music_muted = bool(muted)
        if self.available and self.music_loaded:
            if self.music_muted:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def set_volume(self, value):
        self.volume = min(1, max(0, float(value)))
        if self.available and self.music_loaded:
            pygame.mixer.music.set_volume(self.volume)

    def close(self):
        if pygame is not None and self.owns_mixer:
            pygame.mixer.quit()
            self.owns_mixer = False
        self.available = False

import pygame # type: ignore

def stopAudioPlayback():
    pygame.mixer.init()  # Initialize the mixer module
    pygame.mixer.music.stop()  # Stop any currently playing music

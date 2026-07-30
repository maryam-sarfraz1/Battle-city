#!/usr/bin/env python3
"""Battle City (Tank 1990) - AL2002 AI Lab Project"""

import pygame
import sys
from game import Game

def main():
    pygame.init()
    pygame.display.set_caption("Battle City — AL2002 AI Lab")
    
    screen = pygame.display.set_mode((900, 700))
    clock = pygame.time.Clock()
    
    game = Game(screen, clock)
    game.run()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

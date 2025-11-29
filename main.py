# main.py - Punto de entrada del juego Yu-Gi-Oh! Forbidden Memories

"""
Yu-Gi-Oh! Forbidden Memories - Minimax AI Edition
Universidad del Valle
Escuela de Ingeniería de Sistemas y Computación
Introducción a la Inteligencia Artificial - Segundo Proyecto

Este juego implementa una versión simplificada de Yu-Gi-Oh! Forbidden Memories
con un oponente controlado por el algoritmo Minimax con poda alfa-beta.

Características principales:
- 80 cartas de monstruos (cargadas desde CSV)
- 42 combinaciones de fusión auténticas del juego original
- Sistema de Estrellas Guardianas con bonus de combate (+500/-500)
- Información perfecta (todas las cartas visibles para ambos jugadores)
- IA con Minimax y poda alfa-beta
- Interfaz gráfica con Pygame

Cómo jugar:
1. Selecciona una carta de tu mano
2. Elige la posición (ATK/DEF) y la estrella guardiana
3. Presiona "JUGAR" para colocar la carta en el campo
4. Si ambos jugadores tienen cartas en el campo, presiona "BATALLA"
5. Usa "FUSIONAR" para combinar cartas y obtener monstruos más fuertes
6. Reduce los puntos de vida del oponente a 0 para ganar

Controles:
- Click izquierdo: Seleccionar cartas y botones
- ESC: Volver al menú
- ESPACIO: Reiniciar (en pantalla de fin de juego)
"""

import os
import sys

# Asegurar que estamos en el directorio correcto
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def main():
    # Verificar que los archivos CSV existen
    data_dir = os.path.join(script_dir, "data")
    monsters_file = os.path.join(data_dir, "monsters.csv")
    fusions_file = os.path.join(data_dir, "fusions.csv")
    
    if not os.path.exists(monsters_file):
        print(f"ERROR: No se encontró el archivo de monstruos: {monsters_file}")
        sys.exit(1)
    
    if not os.path.exists(fusions_file):
        print(f"ERROR: No se encontró el archivo de fusiones: {fusions_file}")
        sys.exit(1)
    
    # Importar y mostrar información del dataset
    from cards import CARD_DATABASE, FUSIONS
    
    print("=" * 60)
    print("Yu-Gi-Oh! Forbidden Memories - Minimax AI Edition")
    print("=" * 60)
    print("Universidad del Valle")
    print("Introducción a la Inteligencia Artificial")
    print("=" * 60)
    print(f"\nDataset cargado:")
    print(f"  - Monstruos: {len(CARD_DATABASE)}")
    print(f"  - Fusiones:  {len(FUSIONS)}")
    print("\nIniciando interfaz gráfica...\n")
    
    # Iniciar el juego
    from gui import Game
    game = Game()
    game.run()

if __name__ == "__main__":
    main()

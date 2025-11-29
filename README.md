# Yu-Gi-Oh! Forbidden Memories - Minimax AI Edition

## Universidad del Valle
### Escuela de Ingeniería de Sistemas y Computación
### Introducción a la Inteligencia Artificial - Segundo Proyecto

---

## Descripción

Este proyecto implementa una versión simplificada del juego Yu-Gi-Oh! Forbidden Memories con un oponente controlado por el algoritmo **Minimax con poda alfa-beta**. El juego utiliza información perfecta, donde todas las cartas son visibles para ambos jugadores.

## Características

### Requisitos del Proyecto Cumplidos

- ✅ **Máximo 80 cartas**: Dataset con exactamente 80 monstruos
- ✅ **Mínimo 15 fusiones**: Implementadas 43 fusiones auténticas del juego original
- ✅ **Sistema de Estrellas Guardianas**: 10 estrellas con bonus de combate (+500/-500)
- ✅ **Tamaño de mazo configurable**: Entre 10 y 40 cartas
- ✅ **Información perfecta**: Todas las cartas visibles para ambos jugadores
- ✅ **El humano siempre inicia**: Implementado
- ✅ **Interfaz gráfica obligatoria**: Desarrollada con Pygame
- ✅ **Algoritmo Minimax con poda alfa-beta**: Implementado

### Características Adicionales

- Carga de datos desde archivos CSV
- Visualización de próximas cartas del mazo
- Sistema de fusiones basado en nombres de cartas
- Múltiples niveles de dificultad según profundidad del Minimax

## Estructura del Proyecto

```
AI_P2/
├── data/
│   ├── monsters.csv      # Base de datos de 80 monstruos
│   └── fusions.csv       # 43 combinaciones de fusión
├── cards.py              # Clases Card, Fusion y carga de datos
├── game_state.py         # Estado del juego y lógica de Player/GameState
├── minimax.py            # Algoritmo Minimax con poda alfa-beta
├── gui.py                # Interfaz gráfica con Pygame
├── main.py               # Punto de entrada
├── verify_fusions.py     # Script de verificación de fusiones
├── requirements.txt      # Dependencias
└── README.md             # Este archivo
```

## Requisitos del Sistema

- Python 3.8 o superior
- Pygame 2.5.0 o superior

## Instalación

1. Clonar o descargar el proyecto
2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Cómo Jugar

### Controles
- **Click izquierdo**: Seleccionar cartas y botones
- **ESC**: Volver al menú
- **ESPACIO**: Reiniciar (en pantalla de fin de juego)

### Flujo del Juego

1. **Seleccionar carta**: Haz click en una carta de tu mano
2. **Elegir posición**: Usa el botón "POS: ATK/DEF" para cambiar
3. **Elegir estrella**: Usa el botón "ESTRELLA 1/2" para seleccionar
4. **Jugar carta**: Presiona "JUGAR" para colocarla en el campo
5. **Batalla**: Si ambos tienen cartas, presiona "BATALLA"
6. **Fusionar**: Selecciona "FUSIONAR" y luego dos cartas de tu mano
7. **Fin de turno**: Presiona "FIN TURNO" cuando termines

### Sistema de Combate

- Las cartas en **ATK** atacan con su valor de ataque
- Las cartas en **DEF** defienden con su valor de defensa
- **Daño a LP**: Solo si la carta atacante tiene más ATK que la DEF del defensor
- **Estrellas Guardianas**: Bonus de +500 si tu estrella vence a la del oponente

### Sistema de Estrellas Guardianas

| Estrella | Fuerte contra | Débil contra |
|----------|---------------|--------------|
| Sol      | Luna          | Venus        |
| Luna     | Venus         | Sol          |
| Venus    | Sol           | Luna         |
| Mercurio | Neptuno       | Marte        |
| Marte    | Mercurio      | Urano        |
| Jupiter  | Pluton        | Saturno      |
| Saturno  | Jupiter       | Neptuno      |
| Urano    | Marte         | Pluton       |
| Pluton   | Urano         | Jupiter      |
| Neptuno  | Saturno       | Mercurio     |

## Algoritmo Minimax

### Implementación

El algoritmo Minimax evalúa todos los posibles estados del juego hasta una profundidad configurada, utilizando **poda alfa-beta** para optimizar la búsqueda y evitar explorar ramas innecesarias.

### Función de Evaluación Heurística

La IA considera múltiples factores:

1. **Diferencia de puntos de vida** (peso alto)
2. **Control del campo**: Tener carta en campo vs. no tenerla
3. **Calidad de cartas en mano**: Suma de ATK/DEF
4. **Número de cartas**: Ventaja de recursos
5. **Potencial de fusiones**: Combinaciones disponibles
6. **Próximas cartas del mazo**: Información perfecta
7. **Penalización por vida baja**

### Profundidad de Búsqueda

- **Profundidad 2**: Fácil
- **Profundidad 4**: Normal (predeterminado)
- **Profundidad 6**: Difícil
- **Profundidad 8+**: Experto

## Archivos de Datos

### monsters.csv

Contiene 80 monstruos con los siguientes campos:
- `id`: Identificador único
- `name`: Nombre del monstruo
- `type`: Tipo (Dragon, Warrior, Spellcaster, etc.)
- `atk`: Puntos de ataque
- `def`: Puntos de defensa
- `attribute`: Atributo (DARK, LIGHT, FIRE, WATER, EARTH, WIND)
- `level`: Nivel de estrellas

### fusions.csv

Contiene 43 fusiones con los campos:
- `Material1`: Primer material de fusión
- `Material2`: Segundo material de fusión
- `Result`: Monstruo resultante
- `Result_Attack`: ATK del resultado
- `Result_Defense`: DEF del resultado
- `Result_Attribute`: Atributo del resultado
- `Result_Type`: Tipo del resultado

## Ejemplos de Fusiones

| Material 1 | Material 2 | Resultado | ATK |
|------------|------------|-----------|-----|
| Summoned Skull | Red-Eyes B. Dragon | Black Skull Dragon | 3200 |
| Gaia The Fierce Knight | Curse of Dragon | Gaia the Dragon Champion | 2600 |
| Blue-Eyes White Dragon | Blue-Eyes White Dragon | Blue-Eyes Ultimate Dragon | 4500 |
| Dark Magician | Thunder Dragon | Dark Magician Knight | 2500 |

## Verificación

Para verificar que todas las fusiones funcionan correctamente:

```bash
python verify_fusions.py
```

## Créditos

Desarrollado para el curso de Introducción a la Inteligencia Artificial.
Universidad del Valle, Colombia.

## Licencia

Proyecto académico - Solo para uso educativo.
Yu-Gi-Oh! es una marca registrada de Konami.

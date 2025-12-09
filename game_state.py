# ============================================================================
# game_state.py - Estado del juego y lógica principal
# Yu-Gi-Oh! Forbidden Memories - Minimax AI Edition
# ============================================================================
#
# Este archivo contiene toda la lógica del juego:
# - Clase Player: Representa a cada jugador (humano o IA)
# - Clase GameState: Estado completo del juego y reglas
#
# REGLAS SIMPLIFICADAS DEL JUEGO:
# 1. Cada jugador empieza con 8000 LP y 5 cartas en mano
# 2. Cada turno: robar 1 carta, luego fusionar O jugar 1 carta
# 3. Al jugar, elegir posición (ATK/DEF) y estrella guardiana
# 4. Si ambos tienen carta en campo, se resuelve batalla
# 5. Gana quien reduce LP del oponente a 0 o lo deja sin cartas
#
# INFORMACIÓN PERFECTA:
# A diferencia del juego original, aquí TODAS las cartas son visibles
# para permitir que el Minimax funcione de manera determinista.
# ============================================================================

import random
from cards import (Card, get_card_by_id, get_card_by_name, check_fusion, 
                   check_fusion_by_cards, calculate_star_bonus, get_all_cards, 
                   get_random_deck, get_possible_fusions_for_hand, CARD_DATABASE)


class Player:
    """
    =========================================================================
    CLASE PLAYER (Jugador)
    =========================================================================
    
    Representa a un jugador del juego, ya sea humano o IA.
    Maneja todo lo relacionado con las cartas de un jugador.
    
    ATRIBUTOS:
    - name: Nombre del jugador ("Jugador" o "IA")
    - is_ai: True si es controlado por la IA
    - life_points: Puntos de vida (empieza en 8000)
    - deck: Lista de cartas en el mazo (se roban desde el inicio)
    - hand: Lista de cartas en la mano (máximo 5)
    - field: Carta actualmente en el campo de batalla (None o 1 carta)
    - graveyard: Cartas destruidas o usadas para fusiones
    - _last_sacrificed_card: Para la función "deshacer" jugada
    """
    
    def __init__(self, name, is_ai=False):
        self.name = name
        self.is_ai = is_ai
        self.life_points = 8000
        self.deck = []           # Cartas en el mazo (orden conocido y visible)
        self.hand = []           # Cartas en la mano (máx 5)
        self.field = None        # Carta en el campo (solo 1)
        self.graveyard = []      # Cartas destruidas
        self._last_sacrificed_card = None # Para deshacer jugada
    
    def draw_card(self):
        """
        =====================================================================
        ROBAR CARTA
        =====================================================================
        
        Saca la primera carta del mazo y la agrega a la mano.
        Solo funciona si:
        - Hay cartas en el mazo (deck no vacío)
        - La mano no está llena (menos de 5 cartas)
        
        RETORNA: La carta robada, o None si no se pudo robar
        """
        if len(self.deck) > 0 and len(self.hand) < 5:
            card = self.deck.pop(0)  # Sacar la primera carta
            self.hand.append(card)   # Agregarla a la mano
            return card
        return None
    
    def play_card(self, hand_index, position="ATK", star_num=1):
        """
        =====================================================================
        JUGAR CARTA AL CAMPO
        =====================================================================
        
        Toma una carta de la mano y la coloca en el campo de batalla.
        
        PARÁMETROS:
        - hand_index: Posición de la carta en la mano (0 a 4)
        - position: "ATK" (modo ataque) o "DEF" (modo defensa)
        - star_num: 1 o 2 (cuál estrella guardiana usar)
        
        COMPORTAMIENTO:
        - Si YA hay una carta en el campo, esa carta va al cementerio
          (se "sacrifica" para poner la nueva)
        - Guardamos la carta sacrificada para poder deshacer
        
        RETORNA: True si se jugó exitosamente, False si hubo error
        """
        # Validar que el índice sea válido
        if hand_index < 0 or hand_index >= len(self.hand):
            return False
        
        # Resetear sacrificio anterior
        self._last_sacrificed_card = None
        
        # Si ya hay una carta en el campo, va al cementerio
        if self.field is not None:
            self.graveyard.append(self.field)
            self._last_sacrificed_card = self.field  # Guardar para deshacer
        
        # Sacar la carta de la mano y ponerla en el campo
        card = self.hand.pop(hand_index)
        card.set_position(position)      # Configurar ATK o DEF
        card.select_star(star_num)       # Elegir estrella 1 o 2
        self.field = card
        return True
    
    def undo_play_card(self):
        """
        =====================================================================
        DESHACER JUGADA (UNDO)
        =====================================================================
        
        Revierte la última carta jugada al campo.
        
        COMPORTAMIENTO:
        1. La carta del campo vuelve a la mano
        2. Si se había sacrificado una carta, vuelve al campo
        
        NOTA: Solo funciona para la última jugada del turno actual.
        
        RETORNA: True si se deshizo exitosamente, False si no había nada
        """
        if self.field is None:
            return False
            
        # Devolver carta del campo a la mano
        self.hand.append(self.field)
        self.field = None
        
        # Restaurar carta sacrificada si hubo
        if self._last_sacrificed_card:
            # Verificar que está en el cementerio (debería ser la última)
            if self.graveyard and self.graveyard[-1] == self._last_sacrificed_card:
                self.field = self.graveyard.pop()  # Sacar del cementerio
            self._last_sacrificed_card = None
            
        return True
    
    def can_fuse(self, idx1, idx2):
        """
        =====================================================================
        ¿SE PUEDEN FUSIONAR ESTAS CARTAS?
        =====================================================================
        
        Verifica si dos cartas de la mano pueden combinarse.
        
        PARÁMETROS:
        - idx1, idx2: Índices de las cartas en la mano
        
        RETORNA: La carta resultante si es posible, None si no
        """
        # Validaciones básicas
        if idx1 >= len(self.hand) or idx2 >= len(self.hand) or idx1 == idx2:
            return None
        # Verificar en la base de datos de fusiones
        return check_fusion_by_cards(self.hand[idx1], self.hand[idx2])
    
    def fuse_cards(self, idx1, idx2):
        """
        =====================================================================
        FUSIONAR DOS CARTAS
        =====================================================================
        
        Combina dos cartas de la mano para crear una más fuerte.
        
        PROCESO:
        1. Verificar que la fusión es posible
        2. Las dos cartas originales van al cementerio
        3. La carta resultante se agrega a la mano
        
        IMPORTANTE: Se remueve primero el índice mayor para no
        afectar el índice menor (problema común con listas).
        
        RETORNA: La carta fusionada, o None si no fue posible
        """
        result = self.can_fuse(idx1, idx2)
        if result:
            # Remover las cartas originales (primero el índice mayor para no afectar el menor)
            if idx1 > idx2:
                self.graveyard.append(self.hand.pop(idx1))
                self.graveyard.append(self.hand.pop(idx2))
            else:
                self.graveyard.append(self.hand.pop(idx2))
                self.graveyard.append(self.hand.pop(idx1))
            
            # Agregar la carta fusionada a la mano
            self.hand.append(result)
            return result
        return None
    
    def get_possible_fusions(self):
        """
        =====================================================================
        OBTENER FUSIONES POSIBLES
        =====================================================================
        
        Revisa todas las combinaciones de cartas en la mano y retorna
        las fusiones que son posibles.
        
        RETORNA: Lista de tuplas (idx1, idx2, carta_resultado)
        """
        return get_possible_fusions_for_hand(self.hand)
    
    def copy(self):
        """
        =====================================================================
        CREAR COPIA PROFUNDA DEL JUGADOR
        =====================================================================
        
        Crea una copia independiente del jugador.
        IMPORTANTE: El Minimax necesita copiar el estado para simular
        movimientos sin afectar el juego real.
        
        "Copia profunda" significa que también se copian todas las cartas,
        no solo las referencias a ellas.
        
        RETORNA: Nuevo objeto Player con todos los datos copiados
        """
        new_player = Player(self.name, self.is_ai)
        new_player.life_points = self.life_points
        new_player.deck = [c.copy() for c in self.deck]       # Copiar cada carta
        new_player.hand = [c.copy() for c in self.hand]       # Copiar cada carta
        new_player.field = self.field.copy() if self.field else None
        new_player.graveyard = [c.copy() for c in self.graveyard]
        return new_player


class GameState:
    """
    =========================================================================
    CLASE GAMESTATE (Estado del Juego)
    =========================================================================
    
    Contiene todo el estado del juego y las reglas de batalla.
    Es el "cerebro" del juego que coordina todo.
    
    COMPONENTES PRINCIPALES:
    - Dos jugadores (human y ai)
    - Control de turnos y fases
    - Sistema de batalla
    - Verificación de victoria
    
    FASES DEL JUEGO:
    1. DRAW: Robar carta (automático)
    2. MAIN: Fusionar o jugar carta
    3. BATTLE: Resolver combate (automático)
    4. END: Fin del turno
    """
    
    def __init__(self, deck_size=20):
        """
        =====================================================================
        INICIALIZAR JUEGO
        =====================================================================
        
        PARÁMETROS:
        - deck_size: Número de cartas por mazo (entre 10 y 40)
        """
        self.deck_size = max(10, min(deck_size, 40))  # Limitar entre 10 y 40 cartas
        self.human = Player("Jugador", is_ai=False)
        self.ai = Player("IA", is_ai=True)
        self.current_player = self.human  # Humano siempre empieza
        self.turn_number = 1
        self.game_over = False
        self.winner = None
        self.battle_log = []           # Historial de batallas
        self.last_battle_result = None # Último resultado para mostrar
        self.phase = "DRAW"            # Fase actual
    
    def setup_game(self):
        """
        =====================================================================
        CONFIGURAR JUEGO INICIAL
        =====================================================================
        
        Prepara todo para una nueva partida:
        1. Obtener todas las cartas disponibles
        2. Mezclarlas aleatoriamente
        3. Repartir cartas a cada jugador
        4. Robar las 5 cartas iniciales
        
        NOTA: Aunque las cartas se reparten aleatoriamente, después
        TODAS son visibles (información perfecta para el Minimax).
        """
        # Obtener todas las cartas y mezclarlas
        all_cards = get_all_cards()
        random.shuffle(all_cards)
        
        # Asegurar que tenemos suficientes cartas
        if len(all_cards) < self.deck_size * 2:
            # Duplicar cartas si es necesario
            all_cards = all_cards * 2
            random.shuffle(all_cards)
        
        # Repartir cartas (primera mitad al humano, segunda a la IA)
        self.human.deck = all_cards[:self.deck_size]
        self.ai.deck = all_cards[self.deck_size:self.deck_size * 2]
        
        # Mezclar cada mazo individualmente
        random.shuffle(self.human.deck)
        random.shuffle(self.ai.deck)
        
        # Robar 5 cartas iniciales cada uno
        for _ in range(5):
            self.human.draw_card()
            self.ai.draw_card()
        
        self.phase = "MAIN"
        print(f"[Game] Juego configurado: {self.deck_size} cartas por mazo")
        print(f"[Game] Humano: {len(self.human.hand)} cartas en mano, {len(self.human.deck)} en mazo")
        print(f"[Game] IA: {len(self.ai.hand)} cartas en mano, {len(self.ai.deck)} en mazo")
    
    def get_battle_value(self, card, opponent_card=None):
        """
        =====================================================================
        CALCULAR VALOR DE BATALLA
        =====================================================================
        
        Obtiene el valor que usa una carta en batalla, incluyendo
        el bonus de estrella guardiana si aplica.
        
        VALOR BASE:
        - En ATK: se usa el valor de ATK de la carta
        - En DEF: se usa el valor de DEF de la carta
        
        BONUS DE ESTRELLA:
        - +500 si nuestra estrella es fuerte contra la del oponente
        - +0 si es neutral o débil
        
        EJEMPLO:
        - Carta con 1800 ATK, estrella Sol
        - Oponente con estrella Luna
        - Sol > Luna → +500 bonus
        - Valor final: 1800 + 500 = 2300
        
        RETORNA: Valor numérico para comparar en batalla
        """
        base_value = card.get_battle_value()  # ATK o DEF según posición
        
        if opponent_card:
            star_bonus = calculate_star_bonus(card.selected_star, opponent_card.selected_star)
            return base_value + star_bonus
        
        return base_value
    
    def resolve_battle(self, attacker="human"):
        """
        =====================================================================
        RESOLVER BATALLA
        =====================================================================
        
        Esta es la función central del combate. Se ejecuta cuando AMBOS
        jugadores tienen una carta en el campo.
        
        PARÁMETROS:
        - attacker: "human" o "ai" - indica quién está atacando
        
        PROCESO:
        1. Calcular valor de batalla de cada carta (ATK/DEF + bonus estrella)
        2. Comparar valores según quién ataca
        3. Aplicar resultado (daño, destrucción de cartas)
        4. Verificar si el juego terminó
        
        REGLAS DE BATALLA DE YU-GI-OH! ORIGINAL:
        
        El ATACANTE siempre usa ATK.
        El DEFENSOR usa ATK si está en ATK, DEF si está en DEF.
        
        ATK vs ATK:
        - Gana el mayor ATK
        - El perdedor recibe daño = diferencia de ATK
        - La carta perdedora va al cementerio
        
        ATK vs DEF:
        - Si ATK atacante > DEF defensor: Defensor destruido, sin daño
        - Si DEF defensor > ATK atacante: ATACANTE recibe daño (rebote), defensor NO destruido
        - Si son iguales: Nada pasa
        
        EMPATE ATK vs ATK:
        - Ambas cartas son destruidas, nadie recibe daño
        
        RETORNA: Diccionario con toda la información de la batalla
        """
        # Verificar que ambos tengan carta en campo
        if self.human.field is None or self.ai.field is None:
            return None
        
        human_card = self.human.field
        ai_card = self.ai.field
        
        # Determinar quién es atacante y defensor
        if attacker == "human":
            attacker_card = human_card
            defender_card = ai_card
            attacker_player = self.human
            defender_player = self.ai
        else:
            attacker_card = ai_card
            defender_card = human_card
            attacker_player = self.ai
            defender_player = self.human
        
        # ===================================================================
        # PASO 1: CALCULAR VALORES DE BATALLA
        # ===================================================================
        # El atacante SIEMPRE usa ATK (no puede atacar en DEF)
        attacker_base = attacker_card.atk
        attacker_star_bonus = calculate_star_bonus(attacker_card.selected_star, defender_card.selected_star)
        attacker_value = attacker_base + attacker_star_bonus
        
        # El defensor usa ATK o DEF según su posición
        defender_star_bonus = calculate_star_bonus(defender_card.selected_star, attacker_card.selected_star)
        if defender_card.position == "ATK":
            defender_base = defender_card.atk
        else:
            defender_base = defender_card.defense
        defender_value = defender_base + defender_star_bonus
        
        # ===================================================================
        # PASO 2: PREPARAR RESULTADO
        # ===================================================================
        result = {
            "human_card": human_card.name,
            "ai_card": ai_card.name,
            "attacker": attacker,
            "attacker_value": attacker_value,
            "defender_value": defender_value,
            "attacker_bonus": attacker_star_bonus,
            "defender_bonus": defender_star_bonus,
            "human_value": attacker_value if attacker == "human" else defender_value,
            "ai_value": defender_value if attacker == "human" else attacker_value,
            "human_star": human_card.selected_star,
            "ai_star": ai_card.selected_star,
            "human_position": human_card.position,
            "ai_position": ai_card.position,
            "defender_position": defender_card.position,
            "damage": 0,
            "winner": None,
            "description": ""
        }
        
        # ===================================================================
        # PASO 3: COMPARAR VALORES Y APLICAR RESULTADO
        # ===================================================================
        
        if attacker_value > defender_value:
            # ----- ATACANTE GANA -----
            if defender_card.position == "ATK":
                # Defensor en ATK: recibe daño por la diferencia
                result["damage"] = attacker_value - defender_value
                defender_player.life_points -= result["damage"]
                if attacker == "human":
                    result["description"] = f"¡Ganaste! Infliges {result['damage']} de daño."
                else:
                    result["description"] = f"¡Perdiste! Recibes {result['damage']} de daño."
            else:
                # Defensor en DEF: destruido pero sin daño
                if attacker == "human":
                    result["description"] = "¡Ganaste! La carta enemiga en DEF fue destruida."
                else:
                    result["description"] = "¡Perdiste! Tu carta en DEF fue destruida."
            
            # Carta del defensor va al cementerio
            defender_player.graveyard.append(defender_player.field)
            defender_player.field = None
            result["winner"] = attacker
            
        elif defender_value > attacker_value:
            # ----- DEFENSOR GANA (Atacante pierde) -----
            if defender_card.position == "ATK":
                # Defensor en ATK: Atacante recibe daño y su carta es destruida
                result["damage"] = defender_value - attacker_value
                attacker_player.life_points -= result["damage"]
                # Carta del atacante va al cementerio
                attacker_player.graveyard.append(attacker_player.field)
                attacker_player.field = None
                if attacker == "human":
                    result["description"] = f"¡Perdiste! Recibes {result['damage']} de daño."
                else:
                    result["description"] = f"¡Ganaste! La IA recibe {result['damage']} de daño."
                result["winner"] = "ai" if attacker == "human" else "human"
            else:
                # Defensor en DEF: ATACANTE recibe daño de rebote, defensor NO destruido
                result["damage"] = defender_value - attacker_value
                attacker_player.life_points -= result["damage"]
                # La carta del atacante NO es destruida en este caso
                if attacker == "human":
                    result["description"] = f"¡Rebote! Tu ATK es menor, recibes {result['damage']} de daño."
                else:
                    result["description"] = f"¡Defendiste! La IA recibe {result['damage']} de daño de rebote."
                result["winner"] = "ai" if attacker == "human" else "human"
                
        else:
            # ----- EMPATE (valores iguales) -----
            if defender_card.position == "ATK":
                # ATK vs ATK con empate: Ambas destruidas, sin daño
                self.human.graveyard.append(self.human.field)
                self.ai.graveyard.append(self.ai.field)
                self.human.field = None
                self.ai.field = None
                result["winner"] = "tie"
                result["description"] = "¡Empate! Ambas cartas fueron destruidas."
            else:
                # ATK vs DEF con empate: Nada pasa
                result["winner"] = "tie"
                result["description"] = "¡Empate! ATK = DEF, nada sucede."
        
        # ===================================================================
        # PASO 4: GUARDAR RESULTADO Y VERIFICAR FIN
        # ===================================================================
        self.battle_log.append(result)
        self.last_battle_result = result
        
        # Verificar condiciones de victoria
        self.check_game_over()
        
        return result
    
    def check_game_over(self):
        """
        =====================================================================
        VERIFICAR FIN DEL JUEGO
        =====================================================================
        
        El juego termina cuando:
        1. Un jugador llega a 0 o menos puntos de vida
        2. Un jugador se queda sin cartas (deck out)
        
        En ambos casos, el otro jugador gana.
        """
        # Victoria por puntos de vida
        if self.human.life_points <= 0:
            self.game_over = True
            self.winner = self.ai
            return
        
        if self.ai.life_points <= 0:
            self.game_over = True
            self.winner = self.human
            return
        
        # Victoria por deck out (sin cartas disponibles)
        # Un jugador está "sin cartas" si no tiene mazo, mano ni campo
        human_has_cards = len(self.human.deck) > 0 or len(self.human.hand) > 0 or self.human.field is not None
        ai_has_cards = len(self.ai.deck) > 0 or len(self.ai.hand) > 0 or self.ai.field is not None
        
        if not human_has_cards:
            self.game_over = True
            self.winner = self.ai
        elif not ai_has_cards:
            self.game_over = True
            self.winner = self.human
    
    def next_turn(self):
        """
        =====================================================================
        PASAR AL SIGUIENTE TURNO
        =====================================================================
        
        Cambia el jugador activo y ejecuta la fase de robo.
        El número de turno solo aumenta cuando vuelve al humano.
        """
        # Cambiar jugador activo
        if self.current_player == self.human:
            self.current_player = self.ai
        else:
            self.current_player = self.human
            self.turn_number += 1  # Nuevo turno del humano
        
        # Robar carta al inicio del turno
        self.current_player.draw_card()
        self.phase = "MAIN"
    
    def copy(self):
        """
        =====================================================================
        CREAR COPIA PROFUNDA DEL ESTADO
        =====================================================================
        
        Crea una copia COMPLETAMENTE independiente del estado del juego.
        
        CRÍTICO PARA MINIMAX: El algoritmo necesita simular muchos
        movimientos posibles sin afectar el juego real. Por eso se
        crean copias del estado en cada nivel del árbol de búsqueda.
        
        RETORNA: Nuevo objeto GameState con todos los datos copiados
        """
        new_state = GameState(self.deck_size)
        new_state.turn_number = self.turn_number
        new_state.game_over = self.game_over
        new_state.phase = self.phase
        
        # Copiar jugadores (copia profunda)
        new_state.human = self.human.copy()
        new_state.ai = self.ai.copy()
        
        # Establecer jugador actual correctamente
        new_state.current_player = new_state.ai if self.current_player.is_ai else new_state.human
        
        # Copiar ganador si existe
        if self.winner:
            new_state.winner = new_state.ai if self.winner.is_ai else new_state.human
        
        return new_state
    
    def get_possible_actions(self, player):
        """
        =====================================================================
        OBTENER ACCIONES POSIBLES
        =====================================================================
        
        Genera TODAS las acciones legales que un jugador puede hacer.
        Esta función es CRÍTICA para el Minimax, ya que define los
        "hijos" de cada nodo en el árbol de búsqueda.
        
        TIPOS DE ACCIONES:
        
        1. JUGAR CARTA ("play"):
           - Por cada carta en la mano
           - Por cada posición (ATK o DEF)
           - Por cada estrella (1 o 2)
           = Hasta 4 acciones por carta
        
        2. FUSIONAR ("fuse"):
           - Por cada par de cartas que pueden fusionarse
        
        3. PASAR ("pass"):
           - Si ya tiene carta en campo (mantenerla)
           - Si no hay otras opciones
        
        RETORNA: Lista de diccionarios, cada uno describe una acción
        
        EJEMPLO DE ACCIONES:
        [
            {"type": "play", "index": 0, "position": "ATK", "star": 1, "card_name": "Dragon"},
            {"type": "play", "index": 0, "position": "ATK", "star": 2, "card_name": "Dragon"},
            {"type": "play", "index": 0, "position": "DEF", "star": 1, "card_name": "Dragon"},
            {"type": "fuse", "idx1": 0, "idx2": 1, "result_name": "Fusion Dragon"},
            {"type": "pass"}
        ]
        """
        actions = []
        
        # ==================================================================
        # ACCIÓN 1: JUGAR UNA CARTA DE LA MANO
        # ==================================================================
        # Por cada carta, generar 4 variantes (2 posiciones × 2 estrellas)
        for i, card in enumerate(player.hand):
            # Posición ATK con estrella 1
            actions.append({
                "type": "play", 
                "index": i, 
                "position": "ATK", 
                "star": 1,
                "card_name": card.name
            })
            # Posición ATK con estrella 2
            actions.append({
                "type": "play", 
                "index": i, 
                "position": "ATK", 
                "star": 2,
                "card_name": card.name
            })
            # Posición DEF con estrella 1
            actions.append({
                "type": "play", 
                "index": i, 
                "position": "DEF", 
                "star": 1,
                "card_name": card.name
            })
            # Posición DEF con estrella 2
            actions.append({
                "type": "play", 
                "index": i, 
                "position": "DEF", 
                "star": 2,
                "card_name": card.name
            })
        
        # ==================================================================
        # ACCIÓN 2: FUSIONAR CARTAS
        # ==================================================================
        # Obtener todas las fusiones posibles con las cartas actuales
        fusions = player.get_possible_fusions()
        for idx1, idx2, result in fusions:
            actions.append({
                "type": "fuse", 
                "idx1": idx1, 
                "idx2": idx2,
                "result_name": result.name
            })
        
        # ==================================================================
        # ACCIÓN 3: PASAR TURNO
        # ==================================================================
        # Si no hay acciones posibles, debe poder pasar
        if not actions:
            actions.append({"type": "pass"})
        
        # Si ya tiene carta en campo, puede elegir mantenerla (pasar)
        if player.field is not None:
            actions.append({"type": "pass"})
        
        return actions
    
    def apply_action(self, player, action):
        """
        =====================================================================
        APLICAR ACCIÓN AL ESTADO
        =====================================================================
        
        Ejecuta una acción en el estado del juego.
        Esta función modifica el estado directamente (no crea copia).
        
        PARÁMETROS:
        - player: El jugador que realiza la acción
        - action: Diccionario con la acción a realizar
        
        ACCIONES SOPORTADAS:
        - "play": Jugar carta de la mano al campo
        - "fuse": Fusionar dos cartas de la mano
        - "pass": No hacer nada (mantener carta actual)
        """
        if action["type"] == "play":
            player.play_card(action["index"], action["position"], action["star"])
        elif action["type"] == "fuse":
            player.fuse_cards(action["idx1"], action["idx2"])
        # "pass" no hace nada - la carta en campo se mantiene
    
    def get_visible_upcoming_cards(self, player, num_cards=3):
        """
        =====================================================================
        OBTENER PRÓXIMAS CARTAS DEL MAZO
        =====================================================================
        
        Retorna las cartas que saldrán próximamente del mazo.
        
        NOTA IMPORTANTE - INFORMACIÓN PERFECTA:
        En esta versión del juego, TODAS las cartas son visibles para
        ambos jugadores. Esto permite que el Minimax funcione de manera
        determinista (sin elementos aleatorios).
        
        PARÁMETROS:
        - player: El jugador del cual ver el mazo
        - num_cards: Cuántas cartas mostrar (default 3)
        
        RETORNA: Lista de las próximas cartas
        """
        return player.deck[:num_cards]
    
    def get_game_info(self):
        """
        =====================================================================
        OBTENER INFORMACIÓN RESUMIDA DEL JUEGO
        =====================================================================
        
        Genera un diccionario con el estado actual del juego.
        Útil para debugging y para mostrar información en la GUI.
        
        RETORNA: Diccionario con todos los datos relevantes
        """
        return {
            "turn": self.turn_number,
            "current_player": self.current_player.name,
            "human_lp": self.human.life_points,
            "ai_lp": self.ai.life_points,
            "human_hand": len(self.human.hand),
            "ai_hand": len(self.ai.hand),
            "human_deck": len(self.human.deck),
            "ai_deck": len(self.ai.deck),
            "human_field": self.human.field.name if self.human.field else None,
            "ai_field": self.ai.field.name if self.ai.field else None,
            "game_over": self.game_over,
            "winner": self.winner.name if self.winner else None
        }


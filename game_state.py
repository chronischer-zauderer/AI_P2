# game_state.py - Estado del juego y lógica principal
# Yu-Gi-Oh! Forbidden Memories - Minimax AI Edition

import random
from cards import (Card, get_card_by_id, get_card_by_name, check_fusion, 
                   check_fusion_by_cards, calculate_star_bonus, get_all_cards, 
                   get_random_deck, get_possible_fusions_for_hand, CARD_DATABASE)


class Player:
    """Representa a un jugador (humano o IA)"""
    
    def __init__(self, name, is_ai=False):
        self.name = name
        self.is_ai = is_ai
        self.life_points = 8000
        self.deck = []           # Cartas en el mazo (orden conocido y visible)
        self.hand = []           # Cartas en la mano (máx 5)
        self.field = None        # Carta en el campo (solo 1)
        self.graveyard = []      # Cartas destruidas
    
    def draw_card(self):
        """Roba una carta del mazo si es posible"""
        if len(self.deck) > 0 and len(self.hand) < 5:
            card = self.deck.pop(0)
            self.hand.append(card)
            return card
        return None
    
    def play_card(self, hand_index, position="ATK", star_num=1):
        """
        Juega una carta de la mano al campo.
        Args:
            hand_index: Índice de la carta en la mano
            position: "ATK" o "DEF"
            star_num: 1 o 2 (estrella guardiana a usar)
        Returns:
            bool: True si se jugó exitosamente
        """
        if hand_index < 0 or hand_index >= len(self.hand):
            return False
        
        # Si ya hay una carta en el campo, va al cementerio
        if self.field is not None:
            self.graveyard.append(self.field)
        
        card = self.hand.pop(hand_index)
        card.set_position(position)
        card.select_star(star_num)
        self.field = card
        return True
    
    def can_fuse(self, idx1, idx2):
        """
        Verifica si dos cartas de la mano pueden fusionarse.
        Returns:
            Card o None
        """
        if idx1 >= len(self.hand) or idx2 >= len(self.hand) or idx1 == idx2:
            return None
        return check_fusion_by_cards(self.hand[idx1], self.hand[idx2])
    
    def fuse_cards(self, idx1, idx2):
        """
        Fusiona dos cartas de la mano.
        Returns:
            Card: La carta resultante, o None si no es posible
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
        """Retorna lista de fusiones posibles en la mano"""
        return get_possible_fusions_for_hand(self.hand)
    
    def copy(self):
        """Crea una copia profunda del jugador"""
        new_player = Player(self.name, self.is_ai)
        new_player.life_points = self.life_points
        new_player.deck = [c.copy() for c in self.deck]
        new_player.hand = [c.copy() for c in self.hand]
        new_player.field = self.field.copy() if self.field else None
        new_player.graveyard = [c.copy() for c in self.graveyard]
        return new_player


class GameState:
    """Estado completo del juego"""
    
    def __init__(self, deck_size=20):
        """
        Inicializa el estado del juego.
        Args:
            deck_size: Número de cartas por mazo (10-40)
        """
        self.deck_size = max(10, min(deck_size, 40))  # Entre 10 y 40 cartas
        self.human = Player("Jugador", is_ai=False)
        self.ai = Player("IA", is_ai=True)
        self.current_player = self.human  # Humano siempre empieza
        self.turn_number = 1
        self.game_over = False
        self.winner = None
        self.battle_log = []
        self.last_battle_result = None
        self.phase = "DRAW"  # DRAW, MAIN, BATTLE, END
    
    def setup_game(self):
        """
        Configura el juego inicial.
        Reparte cartas aleatorias a cada jugador.
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
        Calcula el valor de batalla de una carta incluyendo bonus de estrella.
        """
        base_value = card.get_battle_value()
        
        if opponent_card:
            star_bonus = calculate_star_bonus(card.selected_star, opponent_card.selected_star)
            return base_value + star_bonus
        
        return base_value
    
    def resolve_battle(self):
        """
        Resuelve el combate entre las cartas en el campo.
        Returns:
            dict: Resultado de la batalla con información detallada
        """
        if self.human.field is None or self.ai.field is None:
            return None
        
        human_card = self.human.field
        ai_card = self.ai.field
        
        # Calcular valores de batalla con bonus de estrellas
        human_value = self.get_battle_value(human_card, ai_card)
        ai_value = self.get_battle_value(ai_card, human_card)
        
        # Calcular bonus para mostrar
        human_bonus = calculate_star_bonus(human_card.selected_star, ai_card.selected_star)
        ai_bonus = calculate_star_bonus(ai_card.selected_star, human_card.selected_star)
        
        result = {
            "human_card": human_card.name,
            "ai_card": ai_card.name,
            "human_base": human_card.get_battle_value(),
            "ai_base": ai_card.get_battle_value(),
            "human_bonus": human_bonus,
            "ai_bonus": ai_bonus,
            "human_value": human_value,
            "ai_value": ai_value,
            "human_star": human_card.selected_star,
            "ai_star": ai_card.selected_star,
            "human_position": human_card.position,
            "ai_position": ai_card.position,
            "damage": 0,
            "winner": None,
            "description": ""
        }
        
        # Comparar valores
        if human_value > ai_value:
            # Jugador gana
            if ai_card.position == "ATK":
                result["damage"] = human_value - ai_value
                self.ai.life_points -= result["damage"]
                result["description"] = f"¡Ganaste! Infliges {result['damage']} de daño."
            else:
                result["description"] = "¡Ganaste! La carta enemiga estaba en DEF, no hay daño."
            
            self.ai.graveyard.append(self.ai.field)
            self.ai.field = None
            result["winner"] = "human"
            
        elif ai_value > human_value:
            # IA gana
            if human_card.position == "ATK":
                result["damage"] = ai_value - human_value
                self.human.life_points -= result["damage"]
                result["description"] = f"¡Perdiste! Recibes {result['damage']} de daño."
            else:
                result["description"] = "¡Perdiste! Tu carta estaba en DEF, no recibes daño."
            
            self.human.graveyard.append(self.human.field)
            self.human.field = None
            result["winner"] = "ai"
            
        else:
            # Empate - ambas cartas son destruidas
            self.human.graveyard.append(self.human.field)
            self.ai.graveyard.append(self.ai.field)
            self.human.field = None
            self.ai.field = None
            result["winner"] = "tie"
            result["description"] = "¡Empate! Ambas cartas fueron destruidas."
        
        self.battle_log.append(result)
        self.last_battle_result = result
        
        # Verificar condiciones de victoria
        self.check_game_over()
        
        return result
    
    def check_game_over(self):
        """Verifica si el juego ha terminado"""
        # Victoria por puntos de vida
        if self.human.life_points <= 0:
            self.game_over = True
            self.winner = self.ai
            return
        
        if self.ai.life_points <= 0:
            self.game_over = True
            self.winner = self.human
            return
        
        # Victoria por deck out (sin cartas)
        human_has_cards = len(self.human.deck) > 0 or len(self.human.hand) > 0 or self.human.field is not None
        ai_has_cards = len(self.ai.deck) > 0 or len(self.ai.hand) > 0 or self.ai.field is not None
        
        if not human_has_cards:
            self.game_over = True
            self.winner = self.ai
        elif not ai_has_cards:
            self.game_over = True
            self.winner = self.human
    
    def next_turn(self):
        """Pasa al siguiente turno"""
        # Cambiar jugador activo
        if self.current_player == self.human:
            self.current_player = self.ai
        else:
            self.current_player = self.human
            self.turn_number += 1
        
        # Robar carta al inicio del turno
        self.current_player.draw_card()
        self.phase = "MAIN"
    
    def copy(self):
        """Crea una copia profunda del estado del juego para el minimax"""
        new_state = GameState(self.deck_size)
        new_state.turn_number = self.turn_number
        new_state.game_over = self.game_over
        new_state.phase = self.phase
        
        # Copiar jugadores
        new_state.human = self.human.copy()
        new_state.ai = self.ai.copy()
        
        # Establecer jugador actual
        new_state.current_player = new_state.ai if self.current_player.is_ai else new_state.human
        
        # Copiar ganador si existe
        if self.winner:
            new_state.winner = new_state.ai if self.winner.is_ai else new_state.human
        
        return new_state
    
    def get_possible_actions(self, player):
        """
        Obtiene todas las acciones posibles para un jugador.
        Returns:
            list: Lista de diccionarios con acciones posibles
        """
        actions = []
        
        # Acción 1: Jugar una carta de la mano
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
        
        # Acción 2: Fusionar cartas
        fusions = player.get_possible_fusions()
        for idx1, idx2, result in fusions:
            actions.append({
                "type": "fuse", 
                "idx1": idx1, 
                "idx2": idx2,
                "result_name": result.name
            })
        
        # Si no hay acciones posibles, pasar turno
        if not actions:
            actions.append({"type": "pass"})
        
        # Si ya tiene carta en campo, agregar opción de pasar (mantener carta)
        if player.field is not None:
            actions.append({"type": "pass"})
        
        return actions
    
    def apply_action(self, player, action):
        """
        Aplica una acción al estado del juego.
        Args:
            player: El jugador que realiza la acción
            action: Diccionario con la acción a realizar
        """
        if action["type"] == "play":
            player.play_card(action["index"], action["position"], action["star"])
        elif action["type"] == "fuse":
            player.fuse_cards(action["idx1"], action["idx2"])
        # "pass" no hace nada
    
    def get_visible_upcoming_cards(self, player, num_cards=3):
        """
        Retorna las próximas cartas que saldrán del mazo.
        En esta versión del juego, TODAS las cartas son visibles.
        """
        return player.deck[:num_cards]
    
    def get_game_info(self):
        """Retorna información resumida del estado del juego"""
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


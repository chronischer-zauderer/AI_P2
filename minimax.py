# minimax.py - Implementación del algoritmo Minimax con poda alfa-beta
# Yu-Gi-Oh! Forbidden Memories - IA con información perfecta

import math
from cards import calculate_star_bonus, check_fusion_by_cards


class MinimaxAI:
    """
    Implementación del algoritmo Minimax con poda alfa-beta para la IA del juego.
    
    El algoritmo evalúa todas las posibles jugadas y sus consecuencias,
    eligiendo la que maximiza las posibilidades de ganar de la IA.
    
    Características:
    - Información perfecta: todas las cartas son visibles
    - Poda alfa-beta para optimizar la búsqueda
    - Función de evaluación heurística considerando múltiples factores
    """
    
    def __init__(self, max_depth=4):
        """
        Inicializa la IA.
        Args:
            max_depth: Profundidad máxima de búsqueda (más alto = más inteligente pero más lento)
        """
        self.max_depth = max_depth
        self.nodes_evaluated = 0
        self.pruning_count = 0
    
    def evaluate(self, state):
        """
        Función de evaluación heurística del estado del juego.
        Valores positivos favorecen a la IA, negativos al humano.
        
        Factores considerados:
        1. Diferencia de puntos de vida
        2. Control del campo
        3. Calidad de cartas en mano
        4. Cartas restantes
        5. Potencial de fusiones
        6. Próximas cartas del mazo (información perfecta)
        """
        # Victoria/Derrota definitiva
        if state.game_over:
            if state.winner and state.winner.is_ai:
                return 100000
            elif state.winner:
                return -100000
            return 0
        
        score = 0
        
        # Factor 1: Diferencia de puntos de vida (muy importante)
        life_diff = state.ai.life_points - state.human.life_points
        score += life_diff * 1.5
        
        # Factor 2: Control del campo
        if state.ai.field and not state.human.field:
            # IA tiene carta, humano no - ventaja
            score += state.ai.field.atk * 0.3
        elif state.human.field and not state.ai.field:
            # Humano tiene carta, IA no - desventaja
            score -= state.human.field.atk * 0.3
        elif state.ai.field and state.human.field:
            # Ambos tienen carta - evaluar resultado probable
            ai_value = state.get_battle_value(state.ai.field, state.human.field)
            human_value = state.get_battle_value(state.human.field, state.ai.field)
            
            if ai_value > human_value:
                # IA ganaría la batalla
                score += (ai_value - human_value) * 0.5
                # Bonus si el humano está en ATK (haría daño)
                if state.human.field.position == "ATK":
                    score += 200
            else:
                # Humano ganaría
                score -= (human_value - ai_value) * 0.5
                if state.ai.field.position == "ATK":
                    score -= 200
        
        # Factor 3: Calidad de cartas en mano
        ai_hand_power = sum(max(c.atk, c.defense) for c in state.ai.hand) if state.ai.hand else 0
        human_hand_power = sum(max(c.atk, c.defense) for c in state.human.hand) if state.human.hand else 0
        score += (ai_hand_power - human_hand_power) * 0.1
        
        # Mejor carta en mano
        ai_best = max((c.atk for c in state.ai.hand), default=0)
        human_best = max((c.atk for c in state.human.hand), default=0)
        score += (ai_best - human_best) * 0.15
        
        # Factor 4: Número de cartas (ventaja de recursos)
        hand_diff = len(state.ai.hand) - len(state.human.hand)
        deck_diff = len(state.ai.deck) - len(state.human.deck)
        score += hand_diff * 75
        score += deck_diff * 25
        
        # Factor 5: Potencial de fusiones
        ai_fusions = self._count_fusion_potential(state.ai.hand)
        human_fusions = self._count_fusion_potential(state.human.hand)
        score += (ai_fusions - human_fusions) * 150
        
        # Factor 6: Próximas cartas del mazo (información perfecta)
        if state.ai.deck:
            next_ai = state.ai.deck[0]
            score += max(next_ai.atk, next_ai.defense) * 0.05
        if state.human.deck:
            next_human = state.human.deck[0]
            score -= max(next_human.atk, next_human.defense) * 0.05
        
        # Factor 7: Penalización por vida baja
        if state.ai.life_points < 2000:
            score -= (2000 - state.ai.life_points) * 0.5
        if state.human.life_points < 2000:
            score += (2000 - state.human.life_points) * 0.5
        
        return score
    
    def _count_fusion_potential(self, hand):
        """
        Cuenta el potencial de fusiones en una mano.
        Considera no solo fusiones directas sino también el valor del resultado.
        """
        if len(hand) < 2:
            return 0
        
        fusion_value = 0
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                result = check_fusion_by_cards(hand[i], hand[j])
                if result:
                    # Valor basado en mejora respecto a las cartas originales
                    original_best = max(hand[i].atk, hand[j].atk)
                    improvement = result.atk - original_best
                    if improvement > 0:
                        fusion_value += 1 + (improvement / 500)
        
        return fusion_value
    
    def minimax(self, state, depth, alpha, beta, is_maximizing):
        """
        Algoritmo Minimax con poda alfa-beta.
        
        Args:
            state: Estado actual del juego
            depth: Profundidad restante de búsqueda
            alpha: Mejor valor encontrado para el maximizador (IA)
            beta: Mejor valor encontrado para el minimizador (Humano)
            is_maximizing: True si es turno de la IA (maximizar)
        
        Returns:
            Tuple (mejor_valor, mejor_acción)
        """
        self.nodes_evaluated += 1
        
        # Caso base: profundidad 0 o juego terminado
        if depth == 0 or state.game_over:
            return self.evaluate(state), None
        
        player = state.ai if is_maximizing else state.human
        actions = state.get_possible_actions(player)
        
        if not actions:
            return self.evaluate(state), None
        
        best_action = actions[0]
        
        if is_maximizing:
            # Turno de la IA - maximizar
            max_eval = -math.inf
            
            for action in actions:
                # Crear copia del estado y aplicar acción
                new_state = state.copy()
                new_player = new_state.ai
                new_state.apply_action(new_player, action)
                
                # Si ambos tienen carta en campo, simular batalla
                if new_state.human.field and new_state.ai.field:
                    new_state.resolve_battle()
                
                # Recursión (turno del humano = minimizar)
                eval_score, _ = self.minimax(new_state, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_action = action
                
                alpha = max(alpha, eval_score)
                
                # Poda beta
                if beta <= alpha:
                    self.pruning_count += 1
                    break
            
            return max_eval, best_action
        
        else:
            # Turno del humano - minimizar
            min_eval = math.inf
            
            for action in actions:
                new_state = state.copy()
                new_player = new_state.human
                new_state.apply_action(new_player, action)
                
                if new_state.human.field and new_state.ai.field:
                    new_state.resolve_battle()
                
                # Recursión (turno de la IA = maximizar)
                eval_score, _ = self.minimax(new_state, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_action = action
                
                beta = min(beta, eval_score)
                
                # Poda alfa
                if beta <= alpha:
                    self.pruning_count += 1
                    break
            
            return min_eval, best_action
    
    def get_best_move(self, state):
        """
        Obtiene el mejor movimiento para la IA usando Minimax.
        
        Args:
            state: Estado actual del juego
        
        Returns:
            dict: Mejor acción a realizar
        """
        self.nodes_evaluated = 0
        self.pruning_count = 0
        
        # Verificar si hay una fusión muy buena disponible
        good_fusion = self._check_for_valuable_fusion(state)
        if good_fusion:
            print(f"[IA Minimax] Fusión valiosa encontrada!")
            return good_fusion
        
        # Ejecutar Minimax
        score, best_action = self.minimax(
            state,
            self.max_depth,
            -math.inf,
            math.inf,
            True  # IA es el maximizador
        )
        
        print(f"[IA Minimax] Nodos evaluados: {self.nodes_evaluated}")
        print(f"[IA Minimax] Podas realizadas: {self.pruning_count}")
        print(f"[IA Minimax] Puntuación esperada: {score:.1f}")
        
        # Optimizar la acción seleccionada
        if best_action and best_action["type"] == "play":
            best_action = self._optimize_play_action(state, best_action)
        
        return best_action
    
    def _check_for_valuable_fusion(self, state):
        """
        Verifica si hay una fusión que valga la pena hacer inmediatamente.
        Una fusión es valiosa si produce un monstruo significativamente más fuerte.
        """
        hand = state.ai.hand
        best_fusion = None
        best_improvement = 0
        
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                result = check_fusion_by_cards(hand[i], hand[j])
                if result:
                    # Calcular mejora
                    current_best = max(hand[i].atk, hand[j].atk)
                    fusion_power = result.atk
                    improvement = fusion_power - current_best
                    
                    # Solo fusionar si es una mejora significativa (>500 ATK)
                    # O si el resultado es muy poderoso (>2500 ATK)
                    if improvement > 500 or fusion_power >= 2500:
                        if improvement > best_improvement:
                            best_improvement = improvement
                            best_fusion = {
                                "type": "fuse",
                                "idx1": i,
                                "idx2": j,
                                "result_name": result.name
                            }
        
        return best_fusion
    
    def _optimize_play_action(self, state, action):
        """
        Optimiza una acción de jugar carta, seleccionando la mejor
        estrella guardiana y posición según el contexto.
        """
        if action["type"] != "play":
            return action
        
        card = state.ai.hand[action["index"]]
        opponent_field = state.human.field
        
        # Seleccionar mejor estrella
        best_star = self._select_best_star(card, opponent_field)
        
        # Seleccionar mejor posición
        best_position = self._select_best_position(card, opponent_field)
        
        return {
            "type": "play",
            "index": action["index"],
            "position": best_position,
            "star": best_star,
            "card_name": card.name
        }
    
    def _select_best_star(self, card, opponent_field):
        """
        Selecciona la mejor estrella guardiana contra la carta del oponente.
        """
        if not opponent_field:
            return 1  # Por defecto primera estrella
        
        bonus1 = calculate_star_bonus(card.star1, opponent_field.selected_star)
        bonus2 = calculate_star_bonus(card.star2, opponent_field.selected_star)
        
        # Elegir la estrella con mejor bonus
        if bonus1 > bonus2:
            return 1
        elif bonus2 > bonus1:
            return 2
        else:
            # Si son iguales, preferir la primera
            return 1
    
    def _select_best_position(self, card, opponent_field):
        """
        Selecciona la mejor posición (ATK/DEF) considerando la carta del oponente.
        """
        if not opponent_field:
            # Sin oponente en campo, atacar si ATK es decente
            return "ATK" if card.atk >= 1500 else "DEF"
        
        # Calcular valores con estrellas
        our_atk = card.atk
        our_def = card.defense
        opp_atk = opponent_field.atk
        
        # Si podemos ganar atacando, atacar
        if our_atk > opp_atk:
            return "ATK"
        
        # Si nuestra defensa aguanta su ataque, defender
        if our_def >= opp_atk:
            return "DEF"
        
        # Si ninguna opción es buena, minimizar daño
        # Preferir defensa si es mayor que ataque
        return "DEF" if our_def > our_atk else "ATK"
    
    def get_difficulty_name(self):
        """Retorna el nombre de la dificultad según la profundidad"""
        if self.max_depth <= 2:
            return "Fácil"
        elif self.max_depth <= 4:
            return "Normal"
        elif self.max_depth <= 6:
            return "Difícil"
        else:
            return "Experto"


# ============================================================================
# minimax.py - Implementación del algoritmo Minimax con poda alfa-beta
# ============================================================================
# Yu-Gi-Oh! Forbidden Memories - IA con información perfecta
#
# DESCRIPCIÓN GENERAL:
# Este archivo contiene la implementación del algoritmo Minimax, que es el
# "cerebro" de la IA. El algoritmo simula todas las posibles jugadas futuras
# y elige la que le da mayor probabilidad de ganar.
#
# CONCEPTOS CLAVE:
# - Minimax: Algoritmo que asume que el oponente siempre juega de forma óptima
# - Poda Alfa-Beta: Optimización que evita explorar ramas innecesarias del árbol
# - Función de Evaluación: Asigna un puntaje numérico a cada estado del juego
#
# ============================================================================

import math
from cards import calculate_star_bonus, check_fusion_by_cards


class MinimaxAI:
    """
    ============================================================================
    CLASE PRINCIPAL DE LA IA - MinimaxAI
    ============================================================================
    
    Esta clase implementa el algoritmo Minimax con poda alfa-beta para controlar
    la IA del juego. Evalúa todas las posibles jugadas y sus consecuencias,
    eligiendo la que maximiza las posibilidades de ganar.
    
    CARACTERÍSTICAS:
    - Información perfecta: La IA puede ver todas las cartas (tuyas y del mazo)
    - Poda alfa-beta: Optimiza la búsqueda ignorando ramas que no afectan el resultado
    - Evaluación heurística: Usa múltiples factores para puntuar cada estado
    
    ATRIBUTOS:
    - max_depth: Qué tan lejos en el futuro "piensa" la IA (más = más inteligente)
    - nodes_evaluated: Contador de cuántos estados analizó
    - pruning_count: Cuántas ramas se "podaron" (ahorraron)
    """
    
    def __init__(self, max_depth=4):
        """
        Constructor de la IA.
        
        PARÁMETROS:
        - max_depth: Profundidad máxima de búsqueda
            * 2 = Fácil (mira 2 turnos adelante)
            * 4 = Normal (mira 4 turnos adelante) [DEFAULT]
            * 6 = Difícil (mira 6 turnos adelante)
            * 8+ = Experto (muy lento pero muy inteligente)
        """
        self.max_depth = max_depth      # Qué tan "lejos" piensa la IA
        self.nodes_evaluated = 0         # Contador de estados analizados
        self.pruning_count = 0           # Contador de ramas podadas (optimización)
    
    def evaluate(self, state):
        """
        ========================================================================
        FUNCIÓN DE EVALUACIÓN HEURÍSTICA
        ========================================================================
        
        Esta es la función más importante del Minimax. Asigna un PUNTAJE NUMÉRICO
        a cada estado del juego para determinar qué tan "bueno" o "malo" es
        para la IA.
        
        REGLA DE PUNTUACIÓN:
        - Valores POSITIVOS (+) = Favorable para la IA
        - Valores NEGATIVOS (-) = Favorable para el Humano
        - Valor 0 = Estado neutral
        
        FACTORES QUE CONSIDERA (7 en total):
        1. Diferencia de puntos de vida (LP)
        2. Control del campo (quién tiene carta y quién ganaría)
        3. Calidad de las cartas en la mano
        4. Cantidad de cartas restantes (recursos)
        5. Potencial de fusiones disponibles
        6. Calidad de próximas cartas del mazo (información perfecta)
        7. Penalización si la vida está muy baja (peligro de perder)
        
        RETORNA: Un número (float) que representa qué tan bueno es el estado
        """
        
        # ======================================================================
        # CASO ESPECIAL: JUEGO TERMINADO
        # ======================================================================
        # Si el juego ya terminó, retornamos un valor extremo
        if state.game_over:
            if state.winner and state.winner.is_ai:
                return 100000   # Victoria Máximo puntaje posible
            elif state.winner:
                return -100000  # Derrota. Mínimo puntaje posible
            return 0            # Empate (raro pero posible)
        
        # Inicializamos el puntaje en 0
        score = 0
        
        # ======================================================================
        # FACTOR 1: DIFERENCIA DE PUNTOS DE VIDA (Peso: 1.5)
        # ======================================================================
        # Este es el factor MÁS IMPORTANTE porque determina quién gana.
        # Ejemplo: Si IA tiene 8000 LP y Humano tiene 6000 LP:
        #          life_diff = 8000 - 6000 = 2000
        #          score += 2000 * 1.5 = +3000 (muy bueno para IA)
        life_diff = state.ai.life_points - state.human.life_points
        score += life_diff * 1.5
        
        # ======================================================================
        # FACTOR 2: CONTROL DEL CAMPO (Peso: 0.3 - 0.5)
        # ======================================================================
        # Evalúa quién tiene carta en el campo y quién ganaría una batalla.
        
        if state.ai.field and not state.human.field:
            # CASO A: IA tiene carta, Humano NO tiene
            # Esto es una ventaja porque la IA puede atacar sin oposición
            score += state.ai.field.atk * 0.3
            
        elif state.human.field and not state.ai.field:
            # CASO B: Humano tiene carta, IA NO tiene
            # Esto es una desventaja porque el humano puede atacar
            score -= state.human.field.atk * 0.3
            
        elif state.ai.field and state.human.field:
            # CASO C: AMBOS tienen carta 
            # Calculamos quién GANARÍA la batalla (incluyendo bonus de estrellas)
            
            # get_battle_value() calcula: valor_base + bonus_estrella
            ai_value = state.get_battle_value(state.ai.field, state.human.field)
            human_value = state.get_battle_value(state.human.field, state.ai.field)
            
            if ai_value > human_value:
                # IA ganaría la batalla
                score += (ai_value - human_value) * 0.5
                
                # BONUS EXTRA: Si el humano está en ATK, recibiría daño directo
                if state.human.field.position == "ATK":
                    score += 200  # Bonus por poder infligir daño
            else:
                # Humano ganaría la batalla
                score -= (human_value - ai_value) * 0.5
                
                # PENALIZACIÓN: Si la IA está en ATK, recibiría daño directo
                if state.ai.field.position == "ATK":
                    score -= 200  # Penalización por recibir daño
        
        # ======================================================================
        # FACTOR 3: CALIDAD DE CARTAS EN MANO (Peso: 0.1 - 0.15)
        # ======================================================================
        # Suma el poder de todas las cartas en la mano (el mejor valor entre ATK y DEF)
        
        # Calcular poder total de la mano de la IA
        ai_hand_power = sum(max(c.atk, c.defense) for c in state.ai.hand) if state.ai.hand else 0
        # Calcular poder total de la mano del Humano
        human_hand_power = sum(max(c.atk, c.defense) for c in state.human.hand) if state.human.hand else 0
        # La diferencia nos dice quién tiene "mejores cartas"
        score += (ai_hand_power - human_hand_power) * 0.1
        
        # También consideramos la MEJOR carta individual de cada mano
        ai_best = max((c.atk for c in state.ai.hand), default=0)
        human_best = max((c.atk for c in state.human.hand), default=0)
        score += (ai_best - human_best) * 0.15
        
        # ======================================================================
        # FACTOR 4: NÚMERO DE CARTAS - VENTAJA DE RECURSOS (Peso: 25 - 75)
        # ======================================================================
        # Tener más cartas = más opciones = ventaja estratégica
        
        hand_diff = len(state.ai.hand) - len(state.human.hand)
        deck_diff = len(state.ai.deck) - len(state.human.deck)
        
        score += hand_diff * 75   # Cartas en mano valen más (son inmediatas)
        score += deck_diff * 25   # Cartas en mazo valen menos (son futuras)
        
        # ======================================================================
        # FACTOR 5: POTENCIAL DE FUSIONES (Peso: 150)
        # ======================================================================
        # Si la IA tiene cartas que pueden fusionarse para crear algo fuerte,
        # eso es una ventaja porque puede "mejorar" sus cartas.
        
        ai_fusions = self._count_fusion_potential(state.ai.hand)
        human_fusions = self._count_fusion_potential(state.human.hand)
        score += (ai_fusions - human_fusions) * 150
        
        # ======================================================================
        # FACTOR 6: PRÓXIMAS CARTAS DEL MAZO - INFORMACIÓN PERFECTA (Peso: 0.05)
        # ======================================================================
        # Como el juego usa información perfecta, la IA sabe qué carta saldrá
        # del mazo en el próximo turno. Si es una carta fuerte, es una ventaja.
        
        if state.ai.deck:
            next_ai = state.ai.deck[0]  # Primera carta del mazo (la próxima)
            score += max(next_ai.atk, next_ai.defense) * 0.05
            
        if state.human.deck:
            next_human = state.human.deck[0]
            score -= max(next_human.atk, next_human.defense) * 0.05
        
        # ======================================================================
        # FACTOR 7: PENALIZACIÓN POR VIDA BAJA (Peso: 0.5)
        # ======================================================================
        # Si un jugador tiene menos de 2000 LP, está en peligro de perder.
        # Esto hace que la IA sea más cautelosa cuando está herida.
        
        if state.ai.life_points < 2000:
            # IA en peligro - penalizar este estado
            score -= (2000 - state.ai.life_points) * 0.5
            
        if state.human.life_points < 2000:
            # Humano en peligro - favorecer este estado
            score += (2000 - state.human.life_points) * 0.5
        
        # Retornar el puntaje final calculado
        return score
    
    def _count_fusion_potential(self, hand):
        """
        ========================================================================
        CONTADOR DE POTENCIAL DE FUSIONES
        ========================================================================
        
        Esta función analiza una mano de cartas y determina cuántas fusiones
        valiosas están disponibles.
        
        LÓGICA:
        - Revisa cada par posible de cartas en la mano
        - Si pueden fusionarse, calcula cuánto "mejora" el resultado
        - Una fusión es más valiosa si el resultado es mucho más fuerte
        
        PARÁMETROS:
        - hand: Lista de cartas en la mano del jugador
        
        RETORNA: Un valor numérico que representa el "potencial de fusión"
        """
        # Si hay menos de 2 cartas, no se puede fusionar
        if len(hand) < 2:
            return 0
        
        fusion_value = 0
        
        # Revisar cada par posible de cartas (combinaciones)
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                # Intentar fusionar carta i con carta j
                result = check_fusion_by_cards(hand[i], hand[j])
                
                if result:
                    # ¡Fusión posible! Calcular qué tan buena es
                    
                    # ¿Cuál es el ATK más alto de las dos cartas originales?
                    original_best = max(hand[i].atk, hand[j].atk)
                    
                    # ¿Cuánto mejora el resultado respecto a las originales?
                    improvement = result.atk - original_best
                    
                    # Solo cuenta si hay mejora real
                    if improvement > 0:
                        # Fórmula: 1 punto base + bonus por cada 500 ATK de mejora
                        # Ejemplo: Mejora de 1000 ATK = 1 + (1000/500) = 3 puntos
                        fusion_value += 1 + (improvement / 500)
        
        return fusion_value
    
    def minimax(self, state, depth, alpha, beta, is_maximizing):
        """
        ========================================================================
        ALGORITMO MINIMAX CON PODA ALFA-BETA
        ========================================================================
        
        Este es el CORAZÓN del algoritmo. Explora recursivamente todas las
        posibles jugadas futuras para encontrar la mejor decisión.
        
        CONCEPTO CLAVE - DOS JUGADORES:
        - MAX (IA): Quiere MAXIMIZAR el puntaje (elegir el valor más alto)
        - MIN (Humano): Quiere MINIMIZAR el puntaje (elegir el valor más bajo)
        
        PODA ALFA-BETA:
        - Alpha (α): Mejor opción encontrada hasta ahora para MAX
        - Beta (β): Mejor opción encontrada hasta ahora para MIN
        - Si β ≤ α, podemos "podar" (ignorar) el resto de la rama
          porque sabemos que no afectará el resultado final
        
        PARÁMETROS:
        - state: Estado actual del juego (posiciones, LP, cartas, etc.)
        - depth: Cuántos niveles más podemos explorar (0 = parar)
        - alpha: Mejor valor para MAX encontrado hasta ahora
        - beta: Mejor valor para MIN encontrado hasta ahora
        - is_maximizing: True = turno de IA (MAX), False = turno Humano (MIN)
        
        RETORNA: Tupla (mejor_puntaje, mejor_acción)
        """
        # Contador de nodos explorados (para estadísticas)
        self.nodes_evaluated += 1
        
        # ======================================================================
        # CASO BASE: Parar la recursión
        # ======================================================================
        # Paramos si: llegamos al límite de profundidad O el juego terminó
        if depth == 0 or state.game_over:
            # Evaluar el estado actual y retornar (sin acción porque es hoja)
            return self.evaluate(state), None
        
        # Determinar qué jugador está actuando en este nivel
        player = state.ai if is_maximizing else state.human
        
        # Obtener todas las acciones posibles para este jugador
        # Acciones incluyen: jugar carta (4 opciones por carta), fusionar, pasar
        actions = state.get_possible_actions(player)
        
        # Si no hay acciones posibles, evaluar estado actual
        if not actions:
            return self.evaluate(state), None
        
        # Inicializar la mejor acción con la primera disponible
        best_action = actions[0]
        
        # ======================================================================
        # CASO: TURNO DE LA IA (MAXIMIZAR)
        # ======================================================================
        if is_maximizing:
            # Empezamos con el peor valor posible para MAX
            max_eval = -math.inf
            
            # Probar CADA acción posible
            for action in actions:
                # ----------------------------------------------------------
                # PASO 1: Simular la acción
                # ----------------------------------------------------------
                # Crear una COPIA del estado (no modificar el original)
                new_state = state.copy()
                new_player = new_state.ai
                
                # Aplicar la acción en el estado copiado
                new_state.apply_action(new_player, action)
                
                # Si ambos tienen carta en campo, simular la batalla
                # La IA es el atacante cuando es su turno
                if new_state.human.field and new_state.ai.field:
                    new_state.resolve_battle(attacker="ai")
                
                # ----------------------------------------------------------
                # PASO 2: Recursión - Explorar el futuro
                # ----------------------------------------------------------
                if action["type"] == "fuse":
                    # FUSIÓN: Sigue siendo turno de la IA (puede jugar la carta fusionada)
                    # NO reducimos profundidad para que evalúe jugar el resultado
                    eval_score, _ = self.minimax(new_state, depth, alpha, beta, True)
                else:
                    # JUGAR o PASAR: Cambia al turno del humano (minimizar)
                    # Reducimos profundidad porque es un nuevo "nivel"
                    eval_score, _ = self.minimax(new_state, depth - 1, alpha, beta, False)
                
                # ----------------------------------------------------------
                # PASO 3: Actualizar mejor opción
                # ----------------------------------------------------------
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_action = action
                
                # Actualizar alpha (mejor opción para MAX hasta ahora)
                alpha = max(alpha, eval_score)
                
                # ----------------------------------------------------------
                # PODA BETA: ¿Podemos ignorar el resto?
                # ----------------------------------------------------------
                # Si beta ≤ alpha, el jugador MIN nunca elegiría este camino
                # porque ya encontró algo mejor. Podemos "podar" esta rama.
                if beta <= alpha:
                    self.pruning_count += 1  # Contador de podas
                    break  # ¡Salir del loop! (ahorramos tiempo)
            
            return max_eval, best_action
        
        # ======================================================================
        # CASO: TURNO DEL HUMANO (MINIMIZAR)
        # ======================================================================
        else:
            # Empezamos con el peor valor posible para MIN
            min_eval = math.inf
            
            # Probar CADA acción posible
            for action in actions:
                # Simular la acción
                new_state = state.copy()
                new_player = new_state.human
                new_state.apply_action(new_player, action)
                
                # Resolver batalla si es posible
                # El humano es el atacante cuando es su turno
                if new_state.human.field and new_state.ai.field:
                    new_state.resolve_battle(attacker="human")
                
                # Recursión
                if action["type"] == "fuse":
                    # FUSIÓN: Sigue siendo turno del humano
                    eval_score, _ = self.minimax(new_state, depth, alpha, beta, False)
                else:
                    # JUGAR o PASAR: Cambia al turno de la IA
                    eval_score, _ = self.minimax(new_state, depth - 1, alpha, beta, True)
                
                # Actualizar mejor opción para MIN
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_action = action
                
                # Actualizar beta (mejor opción para MIN hasta ahora)
                beta = min(beta, eval_score)
                
                # ----------------------------------------------------------
                # PODA ALFA: ¿Podemos ignorar el resto?
                # ----------------------------------------------------------
                # Si beta ≤ alpha, el jugador MAX nunca elegiría este camino
                if beta <= alpha:
                    self.pruning_count += 1
                    break
            
            return min_eval, best_action
    
    def get_best_move(self, state):
        """
        ========================================================================
        OBTENER MEJOR MOVIMIENTO (Punto de entrada principal)
        ========================================================================
        
        Esta es la función que se llama desde el juego cuando es turno de la IA.
        Coordina todo el proceso de decisión.
        
        FLUJO DE EJECUCIÓN:
        1. Primero revisa si hay una fusión muy buena disponible (atajo)
        2. Si no, ejecuta el algoritmo Minimax completo
        3. Finalmente, optimiza la acción seleccionada
        
        PARÁMETROS:
        - state: Estado actual del juego
        
        RETORNA: Diccionario con la mejor acción a realizar
                 Ejemplo: {"type": "play", "index": 2, "position": "ATK", "star": 1}
        """
        # Resetear contadores para esta búsqueda
        self.nodes_evaluated = 0
        self.pruning_count = 0
        
        # ======================================================================
        # PASO 1: VERIFICAR FUSIÓN VALIOSA (Atajo)
        # ======================================================================
        # Antes de hacer el Minimax completo, revisamos si hay una fusión
        # que claramente vale la pena. Esto ahorra tiempo de cálculo.
        good_fusion = self._check_for_valuable_fusion(state)
        if good_fusion:
            print(f"[IA Minimax] Fusión valiosa encontrada!")
            return good_fusion
        
        # ======================================================================
        # PASO 2: EJECUTAR ALGORITMO MINIMAX
        # ======================================================================
        # Llamamos al Minimax con:
        # - Estado actual
        # - Profundidad máxima configurada
        # - Alpha inicial: -infinito (peor caso para MAX)
        # - Beta inicial: +infinito (peor caso para MIN)
        # - is_maximizing=True (empezamos con turno de IA)
        score, best_action = self.minimax(
            state,
            self.max_depth,
            -math.inf,
            math.inf,
            True  # IA es el maximizador
        )
        
        # Imprimir estadísticas de la búsqueda
        print(f"[IA Minimax] Nodos evaluados: {self.nodes_evaluated}")
        print(f"[IA Minimax] Podas realizadas: {self.pruning_count}")
        print(f"[IA Minimax] Puntuación esperada: {score:.1f}")
        
        # ======================================================================
        # PASO 3: OPTIMIZAR LA ACCIÓN SELECCIONADA
        # ======================================================================
        # Si la mejor acción es jugar una carta, optimizamos la estrella
        # y posición según el contexto actual
        if best_action and best_action["type"] == "play":
            best_action = self._optimize_play_action(state, best_action)
        
        return best_action
    
    def _check_for_valuable_fusion(self, state):
        """
        ========================================================================
        VERIFICAR FUSIÓN VALIOSA (Atajo de optimización)
        ========================================================================
        
        Esta función es un "atajo" que revisa ANTES de ejecutar el Minimax
        completo si hay una fusión que claramente conviene hacer.
        
        ¿POR QUÉ EXISTE ESTA FUNCIÓN?
        El Minimax puede ser lento al explorar todas las posibilidades.
        Si hay una fusión obviamente buena, la hacemos directamente
        sin perder tiempo en el algoritmo completo.
        
        CRITERIOS PARA "FUSIÓN VALIOSA":
        1. La fusión mejora el ATK en más de 500 puntos
        2. O el resultado tiene 2500+ ATK (monstruo muy fuerte)
        
        EJEMPLO:
        - Tenemos: "Dragon Zombie" (1600 ATK) y "Firegrass" (700 ATK)
        - Fusión produce: "Black Dragon Jungle King" (2100 ATK)
        - Mejora: 2100 - 1600 = 500 puntos → ¡Vale la pena!
        
        RETORNA:
        - Diccionario con la acción de fusión si encontró una buena
        - None si no hay fusiones valiosas
        """
        hand = state.ai.hand  # Mano actual de la IA
        best_fusion = None
        best_improvement = 0  # Mejor mejora encontrada
        
        # Revisar TODAS las combinaciones posibles de 2 cartas
        for i in range(len(hand)):
            for j in range(i + 1, len(hand)):
                # Intentar fusionar carta i con carta j
                result = check_fusion_by_cards(hand[i], hand[j])
                
                if result:  # ¡Fusión posible!
                    # Calcular cuánto mejoramos
                    current_best = max(hand[i].atk, hand[j].atk)  # Mejor carta actual
                    fusion_power = result.atk  # ATK del resultado
                    improvement = fusion_power - current_best  # Ganancia neta
                    
                    # ¿Vale la pena esta fusión?
                    # - Mejora más de 500 ATK, O
                    # - El resultado es muy poderoso (2500+ ATK)
                    if improvement > 500 or fusion_power >= 2500:
                        # ¿Es la mejor fusión encontrada hasta ahora?
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
        ========================================================================
        OPTIMIZAR ACCIÓN DE JUGAR CARTA
        ========================================================================
        
        Una vez que Minimax decide QUÉ carta jugar, esta función decide
        CÓMO jugarla de la mejor manera:
        
        1. ¿QUÉ ESTRELLA GUARDIANA USAR?
           - Elegir la estrella que nos dé ventaja (+500) contra el oponente
           
        2. ¿EN QUÉ POSICIÓN? (ATK o DEF)
           - ATK: Usamos el valor de ataque para la batalla
           - DEF: Usamos el valor de defensa (más seguro si es alto)
        
        PARÁMETROS:
        - state: Estado actual del juego
        - action: Acción de tipo "play" con el índice de la carta
        
        RETORNA: Acción optimizada con estrella y posición incluidas
        """
        # Si no es acción de jugar, no hay nada que optimizar
        if action["type"] != "play":
            return action
        
        # Obtener la carta que vamos a jugar
        card = state.ai.hand[action["index"]]
        # Obtener la carta del oponente en campo (si hay)
        opponent_field = state.human.field
        
        # Elegir la mejor estrella guardiana
        best_star = self._select_best_star(card, opponent_field)
        
        # Elegir la mejor posición (ATK o DEF)
        best_position = self._select_best_position(card, opponent_field)
        
        # Retornar la acción completa y optimizada
        return {
            "type": "play",
            "index": action["index"],
            "position": best_position,
            "star": best_star,
            "card_name": card.name
        }
    
    def _select_best_star(self, card, opponent_field):
        """
        ========================================================================
        SELECCIONAR MEJOR ESTRELLA GUARDIANA
        ========================================================================
        
        Cada carta tiene 2 estrellas guardianas (ej: Sol y Mercurio).
        Esta función elige cuál usar basándose en la carta del oponente.
        
        SISTEMA DE ESTRELLAS (ver cards.py para detalles):
        - 10 estrellas: Sol, Luna, Mercurio, Venus, Marte, Júpiter,
                        Saturno, Urano, Neptuno, Plutón
        - Relaciones: Cada estrella es FUERTE contra 2 y DÉBIL contra 2
        - Bonus: +500 ATK si nuestra estrella es fuerte contra la del oponente
        
        EJEMPLO:
        - Nuestra carta: Estrellas Sol (pos 1) y Mercurio (pos 2)
        - Oponente usa: Luna
        - Sol vs Luna: +500 (Sol es fuerte contra Luna)
        - Mercurio vs Luna: +0 (neutral)
        - DECISIÓN: Usar estrella 1 (Sol)
        
        RETORNA: 1 o 2 (índice de la estrella a usar)
        """
        # Si no hay oponente en campo, usar la primera estrella por defecto
        if not opponent_field:
            return 1
        
        # Calcular el bonus de cada estrella contra la del oponente
        bonus1 = calculate_star_bonus(card.star1, opponent_field.selected_star)
        bonus2 = calculate_star_bonus(card.star2, opponent_field.selected_star)
        
        # Elegir la estrella con mejor bonus
        if bonus1 > bonus2:
            return 1  # Primera estrella es mejor
        elif bonus2 > bonus1:
            return 2  # Segunda estrella es mejor
        else:
            return 1  # Si son iguales, preferir la primera
    
    def _select_best_position(self, card, opponent_field):
        """
        ========================================================================
        SELECCIONAR MEJOR POSICIÓN (ATK o DEF)
        ========================================================================
        
        Decide si jugar la carta en modo Ataque (ATK) o Defensa (DEF).
        
        REGLAS DE BATALLA:
        - ATK vs ATK: El mayor ATK gana, el perdedor pierde 1 vida
        - ATK vs DEF: Si ATK > DEF, atacante gana. Si DEF >= ATK, empate/nada pasa
        - DEF es más "seguro" porque no perdemos vida si nos superan
        
        LÓGICA DE DECISIÓN:
        1. Sin oponente → ATK si tenemos 1500+, sino DEF (conservador)
        2. Nuestro ATK > Oponente ATK → ¡ATK! (ganamos seguro)
        3. Nuestra DEF >= Oponente ATK → DEF (aguantamos su ataque)
        4. Ninguna opción buena → Elegir el mal menor
        
        RETORNA: "ATK" o "DEF"
        """
        # CASO 1: No hay oponente en campo
        if not opponent_field:
            # Atacar si tenemos buen ATK, sino defender
            return "ATK" if card.atk >= 1500 else "DEF"
        
        # Obtener valores relevantes
        our_atk = card.atk
        our_def = card.defense
        opp_atk = opponent_field.atk  # ATK del oponente
        
        # CASO 2: Podemos ganar atacando → ¡ATACAR!
        if our_atk > opp_atk:
            return "ATK"
        
        # CASO 3: Nuestra defensa aguanta su ataque → DEFENDER
        if our_def >= opp_atk:
            return "DEF"
        
        # CASO 4: No podemos ganar ni aguantar
        # Elegir el "mal menor" - preferir el valor más alto
        return "DEF" if our_def > our_atk else "ATK"
    
    def get_difficulty_name(self):
        """
        ========================================================================
        OBTENER NOMBRE DE DIFICULTAD
        ========================================================================
        
        Traduce la profundidad del Minimax a un nombre amigable.
        Mayor profundidad = IA más inteligente pero más lenta.
        
        MAPEO:
        - Profundidad 1-2: "Fácil" (piensa 1-2 turnos adelante)
        - Profundidad 3-4: "Normal" (piensa 3-4 turnos adelante)
        - Profundidad 5-6: "Difícil" (piensa 5-6 turnos adelante)
        - Profundidad 7+: "Experto" (análisis muy profundo)
        """
        if self.max_depth <= 2:
            return "Fácil"
        elif self.max_depth <= 4:
            return "Normal"
        elif self.max_depth <= 6:
            return "Difícil"
        else:
            return "Experto"


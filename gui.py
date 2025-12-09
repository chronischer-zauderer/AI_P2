# gui.py - Interfaz gráfica del juego usando Pygame
# Yu-Gi-Oh! Forbidden Memories - Universidad del Valle - IA

import pygame
import sys
import random
from game_state import GameState
from minimax import MinimaxAI
from cards import (
    CARD_DATABASE, FUSIONS, GUARDIAN_STARS, 
    check_fusion_by_cards, calculate_star_bonus
)
from card_image_manager import get_card_image_manager

# Inicializar Pygame
pygame.init()

# Configuración de pantalla dinámica
info = pygame.display.Info()
# Usar 90% del tamaño de pantalla disponible
SCREEN_WIDTH = int(info.current_w * 0.9)
SCREEN_HEIGHT = int(info.current_h * 0.9)

# Asegurar dimensiones mínimas
SCREEN_WIDTH = max(1024, SCREEN_WIDTH)
SCREEN_HEIGHT = max(700, SCREEN_HEIGHT)

FPS = 60

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
BLUE = (30, 144, 255)
GOLD = (255, 215, 0)
PURPLE = (138, 43, 226)
BROWN = (139, 69, 19)
DARK_BLUE = (25, 25, 112)
DARK_GREEN = (0, 100, 0)
ORANGE = (255, 140, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)

# Colores de estrellas guardianas
STAR_COLORS = {
    "Sol": (255, 223, 0),
    "Luna": (192, 192, 192),
    "Venus": (255, 182, 193),
    "Mercurio": (148, 0, 211),
    "Marte": (255, 69, 0),
    "Jupiter": (34, 139, 34),
    "Saturno": (135, 206, 235),
    "Urano": (139, 90, 43),
    "Pluton": (255, 255, 0),
    "Neptuno": (0, 191, 255)
}

# Tamaños de carta dinámicos (Ajustados para evitar superposición)
CARD_HEIGHT = int(SCREEN_HEIGHT * 0.18)  # Reducido de 0.22 a 0.18
CARD_WIDTH = int(CARD_HEIGHT * 0.72)     # Mantener proporción
SMALL_CARD_HEIGHT = int(CARD_HEIGHT * 0.7) # Un poco más grandes las pequeñas
SMALL_CARD_WIDTH = int(CARD_WIDTH * 0.7)

class Button:
    """Clase para botones de la interfaz"""
    def __init__(self, x, y, width, height, text, color=BLUE, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c + 30, 255) for c in color)
        self.text_color = text_color
        self.is_hovered = False
        self.enabled = True
    
    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered and self.enabled else self.color
        if not self.enabled:
            color = GRAY
        
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
        
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered
    
    def is_clicked(self, pos):
        return self.enabled and self.rect.collidepoint(pos)

class CardSprite:
    """Representa una carta visual en la interfaz - Versión mejorada con imágenes"""
    def __init__(self, card, x, y, width=CARD_WIDTH, height=CARD_HEIGHT, face_down=False):
        self.card = card
        self.rect = pygame.Rect(x, y, width, height)
        self.face_down = face_down
        self.selected = False
        self.hover = False
        self.image_manager = get_card_image_manager()
    
    def draw(self, screen, font_small, font_tiny):
        if self.face_down:
            # Carta boca abajo - diseño mejorado
            pygame.draw.rect(screen, BROWN, self.rect, border_radius=8)
            pygame.draw.rect(screen, GOLD, self.rect, 3, border_radius=8)
            # Patrón decorativo mejorado
            inner_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 10, 
                                     self.rect.width - 20, self.rect.height - 20)
            pygame.draw.rect(screen, DARK_BLUE, inner_rect, border_radius=5)
            
            # Patrón de líneas decorativas
            for i in range(5):
                y_pos = self.rect.y + 20 + i * (self.rect.height - 40) // 5
                pygame.draw.line(screen, GOLD, 
                               (self.rect.x + 15, y_pos),
                               (self.rect.x + self.rect.width - 15, y_pos), 2)
        else:
            # Obtener imagen de la carta (generada con mejor diseño)
            card_image = self.image_manager.get_card_image(self.card, 
                                                          self.rect.width, 
                                                          self.rect.height)
            
            # Dibujar la imagen de la carta
            screen.blit(card_image, self.rect)
            
            # Borde adicional según estado
            if self.selected:
                # Borde dorado grueso si está seleccionada
                pygame.draw.rect(screen, GOLD, self.rect, 4, border_radius=5)
                # Efecto de brillo
                glow_rect = self.rect.inflate(8, 8)
                pygame.draw.rect(screen, GOLD, glow_rect, 2, border_radius=6)
            elif self.hover:
                # Borde blanco si está en hover
                pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=5)
    
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

class Game:
    """Clase principal del juego"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Yu-Gi-Oh! Forbidden Memories - Minimax AI")
        self.clock = pygame.time.Clock()
        
        # Fuentes
        self.font_large = pygame.font.Font(None, int(SCREEN_HEIGHT * 0.06))
        self.font_medium = pygame.font.Font(None, int(SCREEN_HEIGHT * 0.04))
        self.font_small = pygame.font.Font(None, int(SCREEN_HEIGHT * 0.03))
        self.font_tiny = pygame.font.Font(None, int(SCREEN_HEIGHT * 0.022))
        self.font_micro = pygame.font.Font(None, int(SCREEN_HEIGHT * 0.018))
        
        # Estado del juego
        self.game_state = None
        self.ai = MinimaxAI(max_depth=3)
        
        # Estado de la UI
        self.state = "MENU"  # MENU, CONFIG, GAME, GAME_OVER, DECK_VIEW
        self.deck_size = 20
        self.selected_card_index = None
        self.fusion_mode = False
        self.fusion_first_card = None
        self.message = ""
        self.message_timer = 0
        self.ai_thinking = False
        self.waiting_for_battle = False
        self.card_played_this_turn = False # Para controlar el deshacer
        
        # === SISTEMA DE FASES (Como Yu-Gi-Oh! real) ===
        # DRAW_PHASE -> MAIN_PHASE -> BATTLE_PHASE -> END_PHASE
        self.current_phase = "DRAW_PHASE"
        self.phase_names = {
            "DRAW_PHASE": "Fase de Robo",
            "MAIN_PHASE": "Fase Principal",
            "BATTLE_PHASE": "Fase de Batalla",
            "END_PHASE": "Fase Final"
        }
        self.phase_colors = {
            "DRAW_PHASE": CYAN,
            "MAIN_PHASE": GREEN,
            "BATTLE_PHASE": RED,
            "END_PHASE": GRAY
        }
        
        # Control de animaciones y flujo
        self.animation_timer = 0
        self.drawn_card = None  # Carta recién robada (para mostrar animación)
        self.show_drawn_card = False
        self.battle_result_display = None  # Para mostrar resultado de batalla
        
        # Botones del menú
        self.setup_menu_buttons()
        
        # Sprites de cartas
        self.hand_sprites = []
        self.ai_hand_sprites = []
        self.human_field_sprite = None
        self.ai_field_sprite = None
        self.deck_preview_sprites = []
        self.ai_deck_preview_sprites = []
    
    def setup_menu_buttons(self):
        """Configura los botones del menú principal"""
        center_x = SCREEN_WIDTH // 2
        
        # Menú principal
        self.btn_play = Button(center_x - 100, SCREEN_HEIGHT * 0.3, 200, 50, "JUGAR", GREEN)
        self.btn_config = Button(center_x - 100, SCREEN_HEIGHT * 0.3 + 70, 200, 50, "CONFIGURACIÓN", BLUE)
        self.btn_rules = Button(center_x - 100, SCREEN_HEIGHT * 0.3 + 140, 200, 50, "REGLAS", PURPLE)
        self.btn_exit = Button(center_x - 100, SCREEN_HEIGHT * 0.3 + 210, 200, 50, "SALIR", RED)
        
        # Botones de configuración
        self.btn_deck_minus = Button(center_x - 150, SCREEN_HEIGHT * 0.4, 50, 40, "-", RED)
        self.btn_deck_plus = Button(center_x + 100, SCREEN_HEIGHT * 0.4, 50, 40, "+", GREEN)
        self.btn_back = Button(center_x - 100, SCREEN_HEIGHT * 0.6, 200, 50, "VOLVER", GRAY)
        
        # Botones del juego - Centrados y organizados
        btn_width = int(SCREEN_WIDTH * 0.1) # 10% del ancho
        btn_height = int(SCREEN_HEIGHT * 0.05) # Altura relativa
        spacing = 15 # Más espacio entre botones
        
        # Botón extra para ver mazos y deshacer
        total_buttons = 8
        total_width = (btn_width * total_buttons) + (spacing * (total_buttons - 1))
        start_x = (SCREEN_WIDTH - total_width) // 2
        y_pos = SCREEN_HEIGHT - btn_height - 20 # Margen inferior
        
        self.btn_play_card = Button(start_x, y_pos, btn_width, btn_height, "JUGAR", GREEN)
        self.btn_fuse = Button(start_x + (btn_width + spacing), y_pos, btn_width, btn_height, "FUSIONAR", PURPLE)
        self.btn_position = Button(start_x + (btn_width + spacing) * 2, y_pos, btn_width, btn_height, "POS: ATK", BLUE)
        self.btn_star = Button(start_x + (btn_width + spacing) * 3, y_pos, btn_width, btn_height, "ESTRELLA 1", ORANGE)
        self.btn_battle = Button(start_x + (btn_width + spacing) * 4, y_pos, btn_width, btn_height, "BATALLA", RED)
        self.btn_view_decks = Button(start_x + (btn_width + spacing) * 5, y_pos, btn_width, btn_height, "VER MAZOS", CYAN)
        self.btn_undo = Button(start_x + (btn_width + spacing) * 6, y_pos, btn_width, btn_height, "DESHACER", YELLOW)
        self.btn_end_turn = Button(start_x + (btn_width + spacing) * 7, y_pos, btn_width, btn_height, "FIN TURNO", GRAY)
        
        self.menu_buttons = [self.btn_play, self.btn_config, self.btn_rules, self.btn_exit]
        self.config_buttons = [self.btn_deck_minus, self.btn_deck_plus, self.btn_back]
        self.game_buttons = [self.btn_play_card, self.btn_fuse, self.btn_position, 
                            self.btn_star, self.btn_battle, self.btn_view_decks, self.btn_undo, self.btn_end_turn]
        
        # Botón volver en vista de mazos
        self.btn_close_decks = Button(center_x - 100, SCREEN_HEIGHT - 80, 200, 50, "VOLVER AL JUEGO", GRAY)
    
    def start_game(self):
        """Inicia una nueva partida"""
        self.game_state = GameState(self.deck_size)
        self.game_state.setup_game()
        self.state = "GAME"
        self.selected_card_index = None
        self.fusion_mode = False
        self.fusion_first_card = None
        self.waiting_for_battle = False
        self.card_played_this_turn = False
        
        # Iniciar en fase principal (ya se robaron las cartas iniciales)
        self.current_phase = "MAIN_PHASE"
        self.drawn_card = None
        self.show_drawn_card = False
        self.battle_result_display = None
        
        self.message = "¡Comienza el duelo! Tu turno - Fase Principal"
        self.message_timer = 180
        self.update_card_sprites()
        print(f"[Juego] Partida iniciada con {self.deck_size} cartas por mazo")
        print(f"[Juego] Total de cartas disponibles: {len(CARD_DATABASE)}")
        print(f"[Juego] Total de fusiones disponibles: {len(FUSIONS)}")
        
        # Mostrar ayuda de fusiones para el primer turno
        self.print_fusion_help()
    
    def update_card_sprites(self):
        """Actualiza los sprites de las cartas"""
        # Mano del jugador
        self.hand_sprites = []
        hand = self.game_state.human.hand
        
        # Espaciado entre cartas
        card_spacing = 20
        
        # Centrar mano dinámicamente
        total_hand_width = len(hand) * CARD_WIDTH + (len(hand) - 1) * card_spacing
        start_x = (SCREEN_WIDTH - total_hand_width) // 2
        
        # Posición Y calculada para estar entre el campo y los botones
        # Campo termina aprox en SCREEN_HEIGHT/2 + CARD_HEIGHT + 30
        # Botones empiezan en SCREEN_HEIGHT - btn_height - 20
        # Ponemos la mano un poco más arriba de los botones
        hand_y = SCREEN_HEIGHT - int(SCREEN_HEIGHT * 0.05) - 40 - CARD_HEIGHT
        
        for i, card in enumerate(hand):
            sprite = CardSprite(card, start_x + i * (CARD_WIDTH + card_spacing), 
                              hand_y, CARD_WIDTH, CARD_HEIGHT)
            self.hand_sprites.append(sprite)
        
        # Mano de la IA (visible en esta versión)
        self.ai_hand_sprites = []
        ai_hand = self.game_state.ai.hand
        
        ai_card_spacing = 10
        total_ai_hand_width = len(ai_hand) * SMALL_CARD_WIDTH + (len(ai_hand) - 1) * ai_card_spacing
        start_x = (SCREEN_WIDTH - total_ai_hand_width) // 2
        
        for i, card in enumerate(ai_hand):
            sprite = CardSprite(card, start_x + i * (SMALL_CARD_WIDTH + ai_card_spacing), 
                              20, SMALL_CARD_WIDTH, SMALL_CARD_HEIGHT)
            self.ai_hand_sprites.append(sprite)
        
        # Campo del jugador
        if self.game_state.human.field:
            self.human_field_sprite = CardSprite(
                self.game_state.human.field,
                SCREEN_WIDTH // 2 - CARD_WIDTH - 20,
                SCREEN_HEIGHT // 2 + 20,
                CARD_WIDTH, CARD_HEIGHT
            )
        else:
            self.human_field_sprite = None
        
        # Campo de la IA
        if self.game_state.ai.field:
            self.ai_field_sprite = CardSprite(
                self.game_state.ai.field,
                SCREEN_WIDTH // 2 + 20,
                SCREEN_HEIGHT // 2 - CARD_HEIGHT - 20,
                CARD_WIDTH, CARD_HEIGHT
            )
        else:
            self.ai_field_sprite = None
        
        # Preview de mazos (Solo para vista rápida lateral si cabe)
        self.deck_preview_sprites = []
        # Mostrar TODAS las cartas restantes (requisito de información perfecta)
        upcoming = self.game_state.get_visible_upcoming_cards(self.game_state.human, 100)
        for i, card in enumerate(upcoming):
            # Posición placeholder, se dibuja en draw_deck_preview
            sprite = CardSprite(card, 0, 0, 0, 0)
            self.deck_preview_sprites.append(sprite)
        
        self.ai_deck_preview_sprites = []
        ai_upcoming = self.game_state.get_visible_upcoming_cards(self.game_state.ai, 100)
        for i, card in enumerate(ai_upcoming):
            sprite = CardSprite(card, 0, 0, 0, 0)
            self.ai_deck_preview_sprites.append(sprite)
    
    def handle_card_click(self, pos):
        """Maneja el click en una carta de la mano"""
        for i, sprite in enumerate(self.hand_sprites):
            if sprite.check_click(pos):
                if self.fusion_mode:
                    if self.fusion_first_card is None:
                        self.fusion_first_card = i
                        sprite.selected = True
                        self.message = "Selecciona la segunda carta para fusionar"
                    elif i != self.fusion_first_card:
                        # Intentar fusión
                        hand = self.game_state.human.hand
                        
                        # Validar índices antes de acceder
                        if self.fusion_first_card >= len(hand) or i >= len(hand):
                            self.message = "Error: Carta no válida"
                            self.fusion_mode = False
                            self.fusion_first_card = None
                            self.update_card_sprites()
                            return

                        result = check_fusion_by_cards(hand[self.fusion_first_card], hand[i])
                        if result:
                            fused = self.game_state.human.fuse_cards(self.fusion_first_card, i)
                            if fused:
                                self.message = f"¡Fusión exitosa! Obtuviste {fused.name} (ATK: {fused.atk})"
                            self.fusion_mode = False
                            self.fusion_first_card = None
                            self.update_card_sprites()
                        else:
                            self.message = "Estas cartas no pueden fusionarse"
                            self.fusion_mode = False
                            self.fusion_first_card = None
                        for s in self.hand_sprites:
                            s.selected = False
                else:
                    # Selección normal
                    self.selected_card_index = i
                    for s in self.hand_sprites:
                        s.selected = False
                    sprite.selected = True
                return
    
    def play_selected_card(self):
        """Juega la carta seleccionada"""
        if self.selected_card_index is not None and self.current_phase == "MAIN_PHASE":
            position = "ATK" if "ATK" in self.btn_position.text else "DEF"
            star = 1 if "1" in self.btn_star.text else 2
            
            success = self.game_state.human.play_card(self.selected_card_index, position, star)
            if success:
                self.card_played_this_turn = True
                self.selected_card_index = None
                
                # Resetear estado de fusión por seguridad
                self.fusion_mode = False
                self.fusion_first_card = None
                
                self.update_card_sprites()
                
                card_name = self.game_state.human.field.name if self.game_state.human.field else "una carta"
                self.message = f"¡{card_name} invocado en posición {position}!"
                
                # Solo pasar a fase de batalla si:
                # 1. Hay carta enemiga en campo
                # 2. Tu carta está en ATK (los monstruos en DEF no atacan)
                if self.game_state.human.field and self.game_state.ai.field and position == "ATK":
                    self.waiting_for_battle = True
                    pygame.time.wait(500)
                    self.current_phase = "BATTLE_PHASE"
                    self.message = f"¡Fase de Batalla! {card_name} vs {self.game_state.ai.field.name}"
                elif position == "DEF":
                    # Carta en DEF no ataca, terminar turno directamente
                    self.message = f"¡{card_name} en DEF! No puede atacar. Fin de tu turno."
                else:
                    self.message = f"¡{card_name} invocado! Puedes terminar tu turno."
    
    def resolve_battle(self):
        """Resuelve la batalla entre cartas - Con animación mejorada (HUMANO ATACA)"""
        if self.game_state.human.field and self.game_state.ai.field:
            # Mostrar enfrentamiento
            human_card = self.game_state.human.field
            ai_card = self.game_state.ai.field
            
            self.message = f"⚔️ {human_card.name} ataca a {ai_card.name}..."
            self.draw_game()
            pygame.display.flip()
            pygame.time.wait(800)
            
            # HUMANO es el atacante
            result = self.game_state.resolve_battle(attacker="human")
            self.waiting_for_battle = False
            
            if result:
                # Guardar resultado para mostrar
                self.battle_result_display = result
                
                if result["winner"] == "human":
                    self.message = f"✓ ¡Victoria! {result['description']}"
                elif result["winner"] == "ai":
                    self.message = f"✗ ¡Derrota! {result['description']}"
                else:
                    self.message = f"= {result['description']}"
                
                # Mostrar resultado con pausa
                self.draw_game()
                pygame.display.flip()
                pygame.time.wait(1500)
                
                self.battle_result_display = None
            
            # Pasar a fase final después de batalla
            self.current_phase = "END_PHASE"
            self.update_card_sprites()
            
            if self.game_state.game_over:
                self.state = "GAME_OVER"
            else:
                self.message = "Fase Final - Presiona FIN TURNO"
    
    def end_turn(self):
        """Termina el turno del jugador y pasa al turno de la IA"""
        self.card_played_this_turn = False
        self.current_phase = "END_PHASE"
        
        self.message = "Fin de tu turno..."
        self.draw_game()
        pygame.display.flip()
        pygame.time.wait(500)
        
        # Cambiar turno
        self.game_state.next_turn()
        
        # Ejecutar turno de la IA
        self.ai_turn()
    
    def ai_turn(self):
        """Ejecuta el turno de la IA con fases y animaciones mejoradas"""
        self.ai_thinking = True
        
        # === FASE DE ROBO DE LA IA ===
        self.current_phase = "DRAW_PHASE"
        self.message = "🎴 Turno de la IA - Fase de Robo"
        self.draw_game()
        pygame.display.flip()
        pygame.time.wait(800)
        
        # Mostrar que robó una carta (ya se robó en next_turn)
        if self.game_state.ai.hand:
            last_card = self.game_state.ai.hand[-1]
            self.message = f"🎴 La IA robó: {last_card.name}"
            self.update_card_sprites()
            self.draw_game()
            pygame.display.flip()
            pygame.time.wait(1000)
        
        # === FASE PRINCIPAL DE LA IA ===
        self.current_phase = "MAIN_PHASE"
        self.message = "🤔 La IA está pensando..."
        self.draw_game()
        pygame.display.flip()
        pygame.time.wait(500)
        
        # Obtener mejor movimiento de la IA
        best_action = self.ai.get_best_move(self.game_state)
        
        if best_action:
            # Intentar fusión primero
            if best_action["type"] == "fuse":
                idx1, idx2 = best_action["idx1"], best_action["idx2"]
                card1_name = self.game_state.ai.hand[idx1].name if idx1 < len(self.game_state.ai.hand) else "?"
                card2_name = self.game_state.ai.hand[idx2].name if idx2 < len(self.game_state.ai.hand) else "?"
                
                self.message = f"🔮 La IA fusiona: {card1_name} + {card2_name}"
                self.draw_game()
                pygame.display.flip()
                pygame.time.wait(1000)
                
                result = self.game_state.ai.fuse_cards(idx1, idx2)
                if result:
                    self.message = f"✨ ¡Fusión! La IA obtuvo {result.name} (ATK: {result.atk})"
                    self.update_card_sprites()
                    self.draw_game()
                    pygame.display.flip()
                    pygame.time.wait(1500)
                    
                    # La IA puede hacer otra acción después de fusionar
                    best_action = self.ai.get_best_move(self.game_state)
            
            # Jugar carta
            if best_action and best_action["type"] == "play":
                card_idx = best_action.get("card_index", 0)
                card_to_play = self.game_state.ai.hand[card_idx] if card_idx < len(self.game_state.ai.hand) else None
                position = best_action.get("position", "ATK")
                
                if card_to_play:
                    self.message = f"📤 La IA invoca: {card_to_play.name} en {position}"
                    self.draw_game()
                    pygame.display.flip()
                    pygame.time.wait(800)
                
                self.game_state.apply_action(self.game_state.ai, best_action)
                self.update_card_sprites()
                
                if self.game_state.ai.field:
                    self.message = f"⚔️ {self.game_state.ai.field.name} está en el campo"
                    self.draw_game()
                    pygame.display.flip()
                    pygame.time.wait(800)
        else:
            self.message = "🤷 La IA no puede hacer ningún movimiento"
            self.draw_game()
            pygame.display.flip()
            pygame.time.wait(1000)
        
        self.update_card_sprites()
        
        # === FASE DE BATALLA DE LA IA ===
        if self.game_state.human.field and self.game_state.ai.field:
            self.current_phase = "BATTLE_PHASE"
            ai_card = self.game_state.ai.field
            human_card = self.game_state.human.field
            
            self.message = f"⚔️ ¡{ai_card.name} ataca a {human_card.name}!"
            self.draw_game()
            pygame.display.flip()
            pygame.time.wait(1000)
            
            # IA es el atacante
            result = self.game_state.resolve_battle(attacker="ai")
            self.waiting_for_battle = False
            
            if result:
                if result["winner"] == "human":
                    self.message = f"✓ ¡Defendiste! {result['description']}"
                elif result["winner"] == "ai":
                    self.message = f"✗ La IA ganó: {result['description']}"
                else:
                    self.message = f"= {result['description']}"
                
                self.update_card_sprites()
                self.draw_game()
                pygame.display.flip()
                pygame.time.wait(1500)
        
        # === FASE FINAL DE LA IA ===
        self.current_phase = "END_PHASE"
        self.ai_thinking = False
        
        if not self.game_state.game_over:
            self.message = "La IA termina su turno..."
            self.draw_game()
            pygame.display.flip()
            pygame.time.wait(600)
            
            # === PASAR AL TURNO DEL JUGADOR ===
            self.game_state.next_turn()
            
            # Fase de robo del jugador
            self.current_phase = "DRAW_PHASE"
            if self.game_state.human.hand:
                drawn = self.game_state.human.hand[-1]
                self.drawn_card = drawn
                self.show_drawn_card = True
                self.message = f"🎴 ¡Tu turno! Robaste: {drawn.name}"
                self.update_card_sprites()
                self.draw_game()
                pygame.display.flip()
                pygame.time.wait(1200)
                self.show_drawn_card = False
            
            # Pasar a fase principal
            self.current_phase = "MAIN_PHASE"
            self.message = "Tu turno - Fase Principal"
            self.update_card_sprites()
            
            # Mostrar ayuda de fusiones en consola
            self.print_fusion_help()
        else:
            self.state = "GAME_OVER"
    
    def print_fusion_help(self):
        """Muestra en consola las fusiones posibles para el turno del humano"""
        from cards import get_possible_fusions_for_hand
        
        hand = self.game_state.human.hand
        fusions = get_possible_fusions_for_hand(hand)
        
        print("\n" + "="*60)
        print("🔮 AYUDA DE FUSIONES - Tu mano actual:")
        print("="*60)
        
        # Mostrar cartas en mano
        for i, card in enumerate(hand):
            print(f"  [{i+1}] {card.name} (ATK:{card.atk}/DEF:{card.defense})")
        
        print("-"*60)
        
        if fusions:
            print("✨ FUSIONES POSIBLES:")
            for idx1, idx2, result in fusions:
                card1 = hand[idx1]
                card2 = hand[idx2]
                print(f"  → [{idx1+1}] {card1.name} + [{idx2+1}] {card2.name}")
                print(f"    = {result.name} (ATK:{result.atk}/DEF:{result.defense})")
        else:
            print("❌ No hay fusiones posibles con tu mano actual.")
        
        print("="*60 + "\n")
    
    def draw_menu(self):
        """Dibuja el menú principal con diseño mejorado"""
        # Fondo con gradiente azul oscuro
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            color = (
                int(25 + 40 * ratio),
                int(25 + 60 * ratio),
                int(112 + 50 * ratio)
            )
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Título con sombra
        title_text = "Yu-Gi-Oh! Forbidden Memories"
        title_shadow = self.font_large.render(title_text, True, (0, 0, 0))
        title = self.font_large.render(title_text, True, GOLD)
        
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=100)
        shadow_rect = title_rect.move(3, 3)
        
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        
        # Borde decorativo alrededor del título
        title_border = title_rect.inflate(20, 15)
        pygame.draw.rect(self.screen, GOLD, title_border, 2, border_radius=10)
        
        # Subtítulo con efecto
        subtitle = self.font_medium.render("Minimax AI Edition", True, CYAN)
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, y=160)
        self.screen.blit(subtitle, subtitle_rect)
        
        # Info del proyecto con fondo
        info_text = "Universidad del Valle - Introducción a la IA"
        info = self.font_small.render(info_text, True, LIGHT_GRAY)
        info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, y=220)
        
        # Fondo para info
        info_bg = pygame.Surface((info.get_width() + 20, info.get_height() + 8), pygame.SRCALPHA)
        pygame.draw.rect(info_bg, (0, 0, 0, 120), info_bg.get_rect(), border_radius=5)
        self.screen.blit(info_bg, (info_rect.x - 10, info_rect.y - 4))
        self.screen.blit(info, info_rect)
        
        # Botones con sombra
        for btn in self.menu_buttons:
            # Sombra del botón
            shadow_rect = btn.rect.move(3, 3)
            pygame.draw.rect(self.screen, (0, 0, 0), shadow_rect, border_radius=8)
            btn.draw(self.screen, self.font_medium)
    
    def draw_config(self):
        """Dibuja la pantalla de configuración"""
        self.screen.fill(DARK_BLUE)
        
        title = self.font_large.render("Configuración", True, GOLD)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=100)
        self.screen.blit(title, title_rect)
        
        # Tamaño del mazo
        deck_label = self.font_medium.render("Cartas por mazo:", True, WHITE)
        deck_rect = deck_label.get_rect(centerx=SCREEN_WIDTH // 2, y=300)
        self.screen.blit(deck_label, deck_rect)
        
        deck_value = self.font_large.render(str(self.deck_size), True, GOLD)
        deck_value_rect = deck_value.get_rect(centerx=SCREEN_WIDTH // 2, y=350)
        self.screen.blit(deck_value, deck_value_rect)
        
        # Info
        info = self.font_small.render("(Mínimo 10, Máximo 40)", True, LIGHT_GRAY)
        info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, y=420)
        self.screen.blit(info, info_rect)
        
        # Botones
        for btn in self.config_buttons:
            btn.draw(self.screen, self.font_medium)
    
    def draw_rules(self):
        """Dibuja la pantalla de reglas"""
        self.screen.fill(DARK_BLUE)
        
        title = self.font_large.render("Reglas del Juego", True, GOLD)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)
        
        rules = [
            "• El humano siempre empieza primero",
            "• Cada jugador comienza con 8000 puntos de vida",
            "• Se roban 5 cartas al inicio y 1 por turno",
            "• Solo puede haber 1 carta en el campo por jugador",
            "• Las cartas pueden estar en posición ATK o DEF",
            "• Cada carta tiene 2 estrellas guardianas",
            "• Ventaja de estrella = +500 ATK/DEF en batalla",
            "• Si ATK > DEF del oponente, se inflige daño a LP",
            "• Si la carta está en DEF, no hay daño directo a LP",
            "• Se pueden fusionar 2 cartas de la mano",
            "• TODAS las cartas son visibles (información perfecta)",
            "• La IA usa algoritmo Minimax con poda alfa-beta",
            f"• Dataset: {len(CARD_DATABASE)} monstruos, {len(FUSIONS)} fusiones",
            "",
            "Presiona ESC para volver al menú"
        ]
        
        y = 100
        for rule in rules:
            text = self.font_small.render(rule, True, WHITE)
            self.screen.blit(text, (100, y))
            y += 35
        
        # Tabla de estrellas
        self.draw_star_table()
    
    def draw_star_table(self):
        """Dibuja la tabla de estrellas guardianas"""
        start_x = SCREEN_WIDTH - 450
        start_y = 100
        
        title = self.font_small.render("Estrellas Guardianas:", True, GOLD)
        self.screen.blit(title, (start_x, start_y))
        
        y = start_y + 30
        for star, relations in GUARDIAN_STARS.items():
            color = STAR_COLORS.get(star, WHITE)
            text = f"{star}: Fuerte vs {relations['strong']}, Débil vs {relations['weak']}"
            surface = self.font_tiny.render(text, True, color)
            self.screen.blit(surface, (start_x, y))
            y += 22
    
    def draw_game(self):
        """Dibuja la pantalla del juego con diseño mejorado"""
        # Fondo con gradiente verde (campo de duelo)
        for y in range(SCREEN_HEIGHT):
            # Gradiente de verde oscuro a verde claro
            ratio = y / SCREEN_HEIGHT
            color = (
                int(15 + 20 * ratio),
                int(50 + 30 * ratio),
                int(15 + 20 * ratio)
            )
            pygame.draw.line(self.screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Línea divisoria del campo con efecto
        pygame.draw.line(self.screen, GOLD, (0, SCREEN_HEIGHT // 2), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT // 2), 4)
        pygame.draw.line(self.screen, (180, 140, 0), (0, SCREEN_HEIGHT // 2 - 2), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT // 2 - 2), 1)
        pygame.draw.line(self.screen, (180, 140, 0), (0, SCREEN_HEIGHT // 2 + 2), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT // 2 + 2), 1)
        
        # === INDICADOR DE FASE (Nuevo) ===
        self.draw_phase_indicator()
        
        # Información de jugadores
        self.draw_player_info()
        
        # Campo de batalla
        self.draw_field()
        
        # Manos de cartas
        self.draw_hands()
        
        # Preview de mazos
        self.draw_deck_preview()
        
        # Carta recién robada (resaltada)
        if self.show_drawn_card and self.drawn_card:
            self.draw_drawn_card_highlight()
        
        # Botones de acción
        self.update_button_states()
        for btn in self.game_buttons:
            btn.draw(self.screen, self.font_small)
        
        # Mensaje con diseño mejorado
        if self.message:
            msg_surface = self.font_medium.render(self.message, True, YELLOW)
            # Mover mensaje arriba, entre la mano de la IA y el campo de la IA
            # Esto evita que tape las estadísticas o el campo
            msg_rect = msg_surface.get_rect(centerx=SCREEN_WIDTH // 2, y=210)
            
            # Fondo semi-transparente con efecto de sombra
            bg_rect = msg_rect.inflate(40, 20)
            shadow_rect = bg_rect.move(3, 3)
            
            # Sombra
            s_shadow = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s_shadow, (0, 0, 0, 100), s_shadow.get_rect(), border_radius=10)
            self.screen.blit(s_shadow, shadow_rect)
            
            # Fondo del mensaje
            s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, 230), s.get_rect(), border_radius=10)
            pygame.draw.rect(s, GOLD, s.get_rect(), 3, border_radius=10)
            self.screen.blit(s, bg_rect)
            
            self.screen.blit(msg_surface, msg_rect)
    
    def draw_phase_indicator(self):
        """Dibuja el indicador de fase actual del turno"""
        # Posición en la parte superior derecha
        x = SCREEN_WIDTH - 280
        y = 15
        
        # Determinar de quién es el turno
        is_human_turn = self.game_state.current_player == self.game_state.human
        turn_owner = "TU TURNO" if is_human_turn else "TURNO IA"
        turn_color = GREEN if is_human_turn else RED
        
        # Fondo del indicador
        bg_rect = pygame.Rect(x - 10, y - 5, 270, 80)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 180), s.get_rect(), border_radius=10)
        pygame.draw.rect(s, turn_color, s.get_rect(), 2, border_radius=10)
        self.screen.blit(s, bg_rect)
        
        # Turno
        turn_text = self.font_small.render(turn_owner, True, turn_color)
        self.screen.blit(turn_text, (x, y))
        
        # Número de turno
        turn_num = self.font_tiny.render(f"Turno #{self.game_state.turn_number}", True, WHITE)
        self.screen.blit(turn_num, (x + 120, y + 3))
        
        # Fase actual
        phase_name = self.phase_names.get(self.current_phase, self.current_phase)
        phase_color = self.phase_colors.get(self.current_phase, WHITE)
        phase_text = self.font_medium.render(phase_name, True, phase_color)
        self.screen.blit(phase_text, (x, y + 28))
        
        # Mini indicadores de todas las fases
        phases = ["DRAW_PHASE", "MAIN_PHASE", "BATTLE_PHASE", "END_PHASE"]
        phase_short = ["ROB", "MAIN", "BAT", "FIN"]
        dot_x = x
        for i, phase in enumerate(phases):
            is_current = (phase == self.current_phase)
            color = self.phase_colors[phase] if is_current else DARK_GRAY
            
            # Círculo indicador
            pygame.draw.circle(self.screen, color, (dot_x + 12, y + 65), 8)
            if is_current:
                pygame.draw.circle(self.screen, WHITE, (dot_x + 12, y + 65), 8, 2)
            
            # Etiqueta
            label = self.font_micro.render(phase_short[i], True, color)
            self.screen.blit(label, (dot_x, y + 75))
            
            dot_x += 65
    
    def draw_drawn_card_highlight(self):
        """Resalta la carta recién robada"""
        if not self.hand_sprites:
            return
        
        # La carta robada es la última en la mano
        last_sprite = self.hand_sprites[-1]
        
        # Dibujar un borde brillante alrededor
        glow_rect = last_sprite.rect.inflate(10, 10)
        pygame.draw.rect(self.screen, GOLD, glow_rect, 4, border_radius=8)
        
        # Texto "¡NUEVA!"
        new_text = self.font_tiny.render("¡NUEVA!", True, GOLD)
        text_rect = new_text.get_rect(centerx=last_sprite.rect.centerx, bottom=last_sprite.rect.top - 5)
        self.screen.blit(new_text, text_rect)
    
    def draw_player_info(self):
        """Dibuja información de los jugadores"""
        center_x = SCREEN_WIDTH // 2
        
        # Distancia desde el centro para los textos
        offset_x = int(SCREEN_WIDTH * 0.25)
        
        # --- JUGADOR HUMANO ---
        # LP cerca de su zona de campo
        human_lp = self.font_medium.render(f"LP: {self.game_state.human.life_points}", True, GREEN)
        # Posicionar a la izquierda de la zona de campo
        self.screen.blit(human_lp, (center_x - offset_x - 100, SCREEN_HEIGHT // 2 + 50))
        
        # Stats del mazo (derecha)
        human_deck = self.font_small.render(f"Mazo: {len(self.game_state.human.deck)}", True, WHITE)
        self.screen.blit(human_deck, (center_x + offset_x, SCREEN_HEIGHT // 2 + 50))
        
        human_grave = self.font_small.render(f"Cementerio: {len(self.game_state.human.graveyard)}", True, GRAY)
        self.screen.blit(human_grave, (center_x + offset_x, SCREEN_HEIGHT // 2 + 80))
        
        # --- IA ---
        # LP cerca de su zona de campo
        ai_lp = self.font_medium.render(f"LP: {self.game_state.ai.life_points}", True, RED)
        # Posicionar a la derecha de la zona de campo (simetría inversa)
        self.screen.blit(ai_lp, (center_x + offset_x, SCREEN_HEIGHT // 2 - 80))
        
        # Stats del mazo (izquierda)
        ai_deck = self.font_small.render(f"Mazo: {len(self.game_state.ai.deck)}", True, WHITE)
        self.screen.blit(ai_deck, (center_x - offset_x - 100, SCREEN_HEIGHT // 2 - 80))
        
        ai_grave = self.font_small.render(f"Cementerio: {len(self.game_state.ai.graveyard)}", True, GRAY)
        self.screen.blit(ai_grave, (center_x - offset_x - 100, SCREEN_HEIGHT // 2 - 50))
        
        # Turno (Debajo de la mano de la IA para no tapar cartas)
        turn = self.font_small.render(f"Turno: {self.game_state.turn_number}", True, GOLD)
        turn_rect = turn.get_rect(centerx=center_x, y=SMALL_CARD_HEIGHT + 40)
        self.screen.blit(turn, turn_rect)
    
    def draw_field(self):
        """Dibuja el campo de batalla con diseño mejorado"""
        # Zona de campo del jugador (con efecto de sombra y gradiente)
        player_zone = pygame.Rect(SCREEN_WIDTH // 2 - CARD_WIDTH - 30, 
                                  SCREEN_HEIGHT // 2 + 10,
                                  CARD_WIDTH + 20, CARD_HEIGHT + 20)
        
        # Sombra de la zona
        shadow_zone = player_zone.move(4, 4)
        shadow_surf = pygame.Surface((shadow_zone.width, shadow_zone.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=8)
        self.screen.blit(shadow_surf, shadow_zone)
        
        # Fondo de la zona con gradiente
        for i in range(player_zone.height):
            ratio = i / player_zone.height
            color = (
                int(30 + 20 * ratio),
                int(50 + 30 * ratio),
                int(30 + 20 * ratio)
            )
            pygame.draw.line(self.screen, color, 
                           (player_zone.left, player_zone.top + i),
                           (player_zone.right, player_zone.top + i))
        
        pygame.draw.rect(self.screen, DARK_GREEN, player_zone, 3, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, player_zone, 1, border_radius=8)
        
        # Zona de campo de la IA (con efecto similar)
        ai_zone = pygame.Rect(SCREEN_WIDTH // 2 + 10,
                              SCREEN_HEIGHT // 2 - CARD_HEIGHT - 30,
                              CARD_WIDTH + 20, CARD_HEIGHT + 20)
        
        # Sombra de la zona
        shadow_zone = ai_zone.move(4, 4)
        shadow_surf = pygame.Surface((shadow_zone.width, shadow_zone.height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect(), border_radius=8)
        self.screen.blit(shadow_surf, shadow_zone)
        
        # Fondo de la zona con gradiente azulado
        for i in range(ai_zone.height):
            ratio = i / ai_zone.height
            color = (
                int(30 + 20 * ratio),
                int(30 + 20 * ratio),
                int(50 + 30 * ratio)
            )
            pygame.draw.line(self.screen, color, 
                           (ai_zone.left, ai_zone.top + i),
                           (ai_zone.right, ai_zone.top + i))
        
        pygame.draw.rect(self.screen, DARK_BLUE, ai_zone, 3, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, ai_zone, 1, border_radius=8)
        
        # Etiquetas con fondo
        player_label = self.font_tiny.render("TU CAMPO", True, WHITE)
        label_bg = pygame.Surface((player_label.get_width() + 10, player_label.get_height() + 4), pygame.SRCALPHA)
        pygame.draw.rect(label_bg, (0, 100, 0, 180), label_bg.get_rect(), border_radius=4)
        self.screen.blit(label_bg, (player_zone.x, player_zone.bottom + 5))
        self.screen.blit(player_label, (player_zone.x + 5, player_zone.bottom + 7))
        
        ai_label = self.font_tiny.render("CAMPO IA", True, WHITE)
        label_bg = pygame.Surface((ai_label.get_width() + 10, ai_label.get_height() + 4), pygame.SRCALPHA)
        pygame.draw.rect(label_bg, (100, 0, 0, 180), label_bg.get_rect(), border_radius=4)
        self.screen.blit(label_bg, (ai_zone.x, ai_zone.y - 20))
        self.screen.blit(ai_label, (ai_zone.x + 5, ai_zone.y - 18))
        
        # Cartas en el campo
        if self.human_field_sprite:
            self.human_field_sprite.draw(self.screen, self.font_small, self.font_tiny)
        
        if self.ai_field_sprite:
            self.ai_field_sprite.draw(self.screen, self.font_small, self.font_tiny)
    
    def draw_hands(self):
        """Dibuja las manos de cartas"""
        # Etiqueta mano jugador
        hand_label = self.font_small.render("Tu Mano:", True, WHITE)
        self.screen.blit(hand_label, (50, SCREEN_HEIGHT - 240))
        
        # Mano del jugador
        for sprite in self.hand_sprites:
            sprite.draw(self.screen, self.font_small, self.font_tiny)
        
        # Etiqueta mano IA
        ai_hand_label = self.font_small.render("Mano IA (visible):", True, WHITE)
        self.screen.blit(ai_hand_label, (SCREEN_WIDTH // 2 - 60, 10)) # Centrado arriba
        
        # Mano de la IA
        for sprite in self.ai_hand_sprites:
            sprite.draw(self.screen, self.font_small, self.font_tiny)
    
    def draw_deck_preview(self):
        """Dibuja la vista previa de los mazos (TODAS las cartas)"""
        # Configuración de visualización
        y_start = 100 # Empezar más arriba
        line_height = 15 # Menos espacio entre líneas
        max_chars = 22 # Más caracteres visibles
        
        # --- TU MAZO (Columna Derecha) ---
        x_pos = SCREEN_WIDTH - 250 # Más adentro
        
        # Fondo semi-transparente para la lista
        bg_rect = pygame.Rect(x_pos - 10, y_start - 30, 240, SCREEN_HEIGHT - y_start + 20)
        s = pygame.Surface((bg_rect.width, bg_rect.height))
        s.set_alpha(100)
        s.fill(BLACK)
        self.screen.blit(s, (bg_rect.x, bg_rect.y))
        
        deck_label = self.font_tiny.render("TU MAZO (Orden):", True, GOLD)
        self.screen.blit(deck_label, (x_pos, y_start - 20))
        
        for i, sprite in enumerate(self.deck_preview_sprites):
            name = sprite.card.name[:max_chars]
            color = WHITE
            if i == 0: color = GREEN
            
            y_pos = y_start + i * line_height
            
            # Si llegamos al fondo, mostrar aviso y parar
            if y_pos > SCREEN_HEIGHT - 100: # Dejar espacio para botones
                more = self.font_micro.render(f"... y {len(self.deck_preview_sprites) - i} más", True, WHITE)
                self.screen.blit(more, (x_pos, y_pos))
                break
                
            text = self.font_micro.render(f"{i+1}. {name}", True, color)
            self.screen.blit(text, (x_pos, y_pos))
        
        # --- MAZO IA (Columna Izquierda) ---
        x_pos_ai = 20 # Más adentro
        
        # Fondo semi-transparente para la lista
        bg_rect_ai = pygame.Rect(x_pos_ai - 10, y_start - 30, 240, SCREEN_HEIGHT - y_start + 20)
        s_ai = pygame.Surface((bg_rect_ai.width, bg_rect_ai.height))
        s_ai.set_alpha(100)
        s_ai.fill(BLACK)
        self.screen.blit(s_ai, (bg_rect_ai.x, bg_rect_ai.y))
        
        ai_deck_label = self.font_tiny.render("MAZO IA (Orden):", True, GOLD)
        self.screen.blit(ai_deck_label, (x_pos_ai, y_start - 20))
        
        for i, sprite in enumerate(self.ai_deck_preview_sprites):
            name = sprite.card.name[:max_chars]
            color = WHITE
            if i == 0: color = RED
            
            y_pos = y_start + i * line_height
            
            if y_pos > SCREEN_HEIGHT - 100:
                more = self.font_micro.render(f"... y {len(self.ai_deck_preview_sprites) - i} más", True, WHITE)
                self.screen.blit(more, (x_pos_ai, y_pos))
                break
                
            text = self.font_micro.render(f"{i+1}. {name}", True, color)
            self.screen.blit(text, (x_pos_ai, y_pos))
    
    def update_button_states(self):
        """Actualiza el estado de los botones según el contexto y la fase actual"""
        is_human_turn = self.game_state.current_player == self.game_state.human
        is_main_phase = self.current_phase == "MAIN_PHASE"
        is_battle_phase = self.current_phase == "BATTLE_PHASE"
        is_end_phase = self.current_phase == "END_PHASE"
        
        # Solo permitir jugar carta en FASE PRINCIPAL y si NO hay carta en el campo
        can_play = (is_human_turn and is_main_phase and 
                    self.selected_card_index is not None and 
                    self.game_state.human.field is None)
        
        # Fusionar solo en fase principal
        can_fuse = is_human_turn and is_main_phase and len(self.game_state.human.hand) >= 2
        
        # Batalla solo en fase de batalla cuando hay 2 cartas
        can_battle = is_human_turn and is_battle_phase and self.waiting_for_battle
        
        # Fin de turno: en fase principal (sin carta en campo enemigo) o fase final
        can_end = is_human_turn and (is_end_phase or (is_main_phase and not self.waiting_for_battle))
        
        self.btn_play_card.enabled = can_play
        self.btn_fuse.enabled = can_fuse
        self.btn_battle.enabled = can_battle
        self.btn_end_turn.enabled = can_end
        self.btn_position.enabled = is_human_turn and is_main_phase
        self.btn_star.enabled = is_human_turn and is_main_phase
        
        # Botón deshacer: En fase principal O fase de batalla (antes de atacar)
        # Permite deshacer la jugada y volver a elegir otra carta/posición
        can_undo = is_human_turn and self.card_played_this_turn and (is_main_phase or is_battle_phase)
        self.btn_undo.enabled = can_undo
        
        # Actualizar texto del botón de batalla según fase
        if is_battle_phase:
            self.btn_battle.text = "¡ATACAR!"
            self.btn_battle.color = RED
        else:
            self.btn_battle.text = "BATALLA"
            self.btn_battle.color = RED
    
    def draw_game_over(self):
        """Dibuja la pantalla de fin de juego"""
        # Fondo semi-transparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill(BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Mensaje de victoria/derrota
        if self.game_state.winner == self.game_state.human:
            result_text = "¡VICTORIA!"
            color = GOLD
        else:
            result_text = "DERROTA"
            color = RED
        
        result_surface = self.font_large.render(result_text, True, color)
        result_rect = result_surface.get_rect(centerx=SCREEN_WIDTH // 2, y=300)
        self.screen.blit(result_surface, result_rect)
        
        # Puntos de vida finales
        human_lp = self.font_medium.render(f"Tus LP: {self.game_state.human.life_points}", True, GREEN)
        ai_lp = self.font_medium.render(f"LP de IA: {self.game_state.ai.life_points}", True, RED)
        
        self.screen.blit(human_lp, (SCREEN_WIDTH // 2 - 80, 380))
        self.screen.blit(ai_lp, (SCREEN_WIDTH // 2 - 80, 420))
        
        # Instrucciones
        instructions = self.font_small.render("Presiona ESPACIO para jugar de nuevo o ESC para salir", True, WHITE)
        inst_rect = instructions.get_rect(centerx=SCREEN_WIDTH // 2, y=500)
        self.screen.blit(instructions, inst_rect)
    
    def handle_events(self):
        """Maneja los eventos de pygame"""
        pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in ["CONFIG", "RULES", "GAME", "GAME_OVER"]:
                        self.state = "MENU"
                elif event.key == pygame.K_SPACE and self.state == "GAME_OVER":
                    self.start_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Click izquierdo
                    self.handle_click(pos)
        
        # Actualizar hover de botones
        if self.state == "MENU":
            for btn in self.menu_buttons:
                btn.check_hover(pos)
        elif self.state == "CONFIG":
            for btn in self.config_buttons:
                btn.check_hover(pos)
        elif self.state == "GAME":
            for btn in self.game_buttons:
                btn.check_hover(pos)
            # Hover en cartas
            for sprite in self.hand_sprites:
                sprite.hover = sprite.rect.collidepoint(pos)
        
        return True
    
    def handle_click(self, pos):
        """Maneja los clicks del mouse"""
        if self.state == "MENU":
            if self.btn_play.is_clicked(pos):
                self.start_game()
            elif self.btn_config.is_clicked(pos):
                self.state = "CONFIG"
            elif self.btn_rules.is_clicked(pos):
                self.state = "RULES"
            elif self.btn_exit.is_clicked(pos):
                pygame.quit()
                sys.exit()
        
        elif self.state == "CONFIG":
            if self.btn_deck_minus.is_clicked(pos):
                self.deck_size = max(10, self.deck_size - 5)
            elif self.btn_deck_plus.is_clicked(pos):
                self.deck_size = min(40, self.deck_size + 5)
            elif self.btn_back.is_clicked(pos):
                self.state = "MENU"
        
        elif self.state == "DECK_VIEW":
            if self.btn_close_decks.is_clicked(pos):
                self.state = "GAME"
        
        elif self.state == "GAME":
            if self.game_state.current_player == self.game_state.human:
                # Click en cartas de la mano
                self.handle_card_click(pos)
                
                # Click en botones
                if self.btn_play_card.is_clicked(pos):
                    self.play_selected_card()
                elif self.btn_fuse.is_clicked(pos):
                    self.fusion_mode = True
                    self.fusion_first_card = None
                    self.selected_card_index = None # Limpiar selección de jugar
                    self.message = "Selecciona la primera carta para fusionar"
                    for s in self.hand_sprites:
                        s.selected = False
                elif self.btn_position.is_clicked(pos):
                    if "ATK" in self.btn_position.text:
                        self.btn_position.text = "POS: DEF"
                    else:
                        self.btn_position.text = "POS: ATK"
                elif self.btn_star.is_clicked(pos):
                    if "1" in self.btn_star.text:
                        self.btn_star.text = "ESTRELLA 2"
                    else:
                        self.btn_star.text = "ESTRELLA 1"
                elif self.btn_battle.is_clicked(pos):
                    self.resolve_battle()
                elif self.btn_view_decks.is_clicked(pos):
                    self.state = "DECK_VIEW"
                elif self.btn_undo.is_clicked(pos):
                    if self.game_state.human.undo_play_card():
                        self.card_played_this_turn = False
                        self.waiting_for_battle = False
                        self.current_phase = "MAIN_PHASE"  # Volver a fase principal
                        self.message = "↩️ Jugada deshecha - Fase Principal"
                        self.update_card_sprites()
                elif self.btn_end_turn.is_clicked(pos):
                    self.end_turn()
    
    def draw_deck_view_overlay(self):
        """Dibuja la vista completa de los mazos"""
        # Fondo oscuro
        self.screen.fill(DARK_BLUE)
        
        title = self.font_large.render("Vista Completa de Mazos (Información Perfecta)", True, GOLD)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)
        
        # Columnas
        col_width = SCREEN_WIDTH // 2 - 40
        
        # --- MAZO IA ---
        pygame.draw.rect(self.screen, (50, 0, 0), (20, 80, col_width, SCREEN_HEIGHT - 180), border_radius=10)
        pygame.draw.rect(self.screen, RED, (20, 80, col_width, SCREEN_HEIGHT - 180), 2, border_radius=10)
        
        ai_title = self.font_medium.render("Mazo IA (Orden de salida)", True, RED)
        self.screen.blit(ai_title, (40, 90))
        
        ai_cards = self.game_state.get_visible_upcoming_cards(self.game_state.ai, 100)
        
        # Listar cartas en columnas dentro del panel si son muchas
        y = 130
        x = 40
        col_limit = x + col_width - 20
        
        for i, card in enumerate(ai_cards):
            text = self.font_small.render(f"{i+1}. {card.name} ({card.atk}/{card.defense})", True, WHITE)
            self.screen.blit(text, (x, y))
            y += 25
            if y > SCREEN_HEIGHT - 200:
                y = 130
                x += 250 # Nueva columna
                if x > col_limit: break # Evitar salir del panel
        
        # --- TU MAZO ---
        x_start = SCREEN_WIDTH // 2 + 20
        pygame.draw.rect(self.screen, (0, 50, 0), (x_start, 80, col_width, SCREEN_HEIGHT - 180), border_radius=10)
        pygame.draw.rect(self.screen, GREEN, (x_start, 80, col_width, SCREEN_HEIGHT - 180), 2, border_radius=10)
        
        human_title = self.font_medium.render("Tu Mazo (Orden de salida)", True, GREEN)
        self.screen.blit(human_title, (x_start + 20, 90))
        
        human_cards = self.game_state.get_visible_upcoming_cards(self.game_state.human, 100)
        
        y = 130
        x = x_start + 20
        col_limit = x + col_width - 20
        
        for i, card in enumerate(human_cards):
            text = self.font_small.render(f"{i+1}. {card.name} ({card.atk}/{card.defense})", True, WHITE)
            self.screen.blit(text, (x, y))
            y += 25
            if y > SCREEN_HEIGHT - 200:
                y = 130
                x += 250
                if x > col_limit: break
                
        # Botón volver
        self.btn_close_decks.draw(self.screen, self.font_medium)
    
    def run(self):
        """Loop principal del juego"""
        running = True
        
        while running:
            running = self.handle_events()
            
            # Dibujar según el estado
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "CONFIG":
                self.draw_config()
            elif self.state == "RULES":
                self.draw_rules()
            elif self.state == "GAME":
                self.draw_game()
            elif self.state == "DECK_VIEW":
                self.draw_deck_view_overlay()
            elif self.state == "GAME_OVER":
                self.draw_game()
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()

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

# Inicializar Pygame
pygame.init()

# Constantes de pantalla
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
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

# Tamaños de carta
CARD_WIDTH = 100
CARD_HEIGHT = 140
SMALL_CARD_WIDTH = 80
SMALL_CARD_HEIGHT = 112

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
    """Representa una carta visual en la interfaz"""
    def __init__(self, card, x, y, width=CARD_WIDTH, height=CARD_HEIGHT, face_down=False):
        self.card = card
        self.rect = pygame.Rect(x, y, width, height)
        self.face_down = face_down
        self.selected = False
        self.hover = False
    
    def draw(self, screen, font_small, font_tiny):
        if self.face_down:
            # Carta boca abajo
            pygame.draw.rect(screen, BROWN, self.rect, border_radius=5)
            pygame.draw.rect(screen, GOLD, self.rect, 2, border_radius=5)
            # Patrón decorativo
            inner_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 10, 
                                     self.rect.width - 20, self.rect.height - 20)
            pygame.draw.rect(screen, DARK_BLUE, inner_rect, border_radius=3)
        else:
            # Fondo de carta según posición
            bg_color = DARK_GREEN if self.card.position == "ATK" else DARK_BLUE
            pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
            
            # Borde (dorado si seleccionada)
            border_color = GOLD if self.selected else WHITE
            border_width = 3 if self.selected or self.hover else 2
            pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=5)
            
            # Nombre de la carta
            name = self.card.name[:12] + "..." if len(self.card.name) > 12 else self.card.name
            name_surface = font_tiny.render(name, True, WHITE)
            name_rect = name_surface.get_rect(centerx=self.rect.centerx, top=self.rect.top + 5)
            screen.blit(name_surface, name_rect)
            
            # Imagen representativa (simulada con color según estrella)
            img_rect = pygame.Rect(self.rect.x + 10, self.rect.y + 25, 
                                   self.rect.width - 20, 50)
            star_color = STAR_COLORS.get(self.card.selected_star, GRAY)
            pygame.draw.rect(screen, star_color, img_rect, border_radius=3)
            
            # Estrella guardiana seleccionada
            star_text = font_tiny.render(self.card.selected_star[:3], True, BLACK)
            star_rect = star_text.get_rect(center=img_rect.center)
            screen.blit(star_text, star_rect)
            
            # ATK/DEF
            atk_text = font_tiny.render(f"ATK:{self.card.atk}", True, RED)
            def_text = font_tiny.render(f"DEF:{self.card.defense}", True, BLUE)
            
            screen.blit(atk_text, (self.rect.x + 5, self.rect.bottom - 35))
            screen.blit(def_text, (self.rect.x + 5, self.rect.bottom - 20))
            
            # Indicador de posición
            pos_text = font_tiny.render(self.card.position, True, YELLOW)
            screen.blit(pos_text, (self.rect.right - 30, self.rect.bottom - 20))
    
    def check_click(self, pos):
        return self.rect.collidepoint(pos)

class Game:
    """Clase principal del juego"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Yu-Gi-Oh! Forbidden Memories - Minimax AI")
        self.clock = pygame.time.Clock()
        
        # Fuentes
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Estado del juego
        self.game_state = None
        self.ai = MinimaxAI(max_depth=3)
        
        # Estado de la UI
        self.state = "MENU"  # MENU, CONFIG, GAME, GAME_OVER
        self.deck_size = 20
        self.selected_card_index = None
        self.fusion_mode = False
        self.fusion_first_card = None
        self.message = ""
        self.message_timer = 0
        self.ai_thinking = False
        self.waiting_for_battle = False
        
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
        
        self.btn_play = Button(center_x - 100, 300, 200, 50, "JUGAR", GREEN)
        self.btn_config = Button(center_x - 100, 370, 200, 50, "CONFIGURACIÓN", BLUE)
        self.btn_rules = Button(center_x - 100, 440, 200, 50, "REGLAS", PURPLE)
        self.btn_exit = Button(center_x - 100, 510, 200, 50, "SALIR", RED)
        
        # Botones de configuración
        self.btn_deck_minus = Button(center_x - 150, 350, 50, 40, "-", RED)
        self.btn_deck_plus = Button(center_x + 100, 350, 50, 40, "+", GREEN)
        self.btn_back = Button(center_x - 100, 500, 200, 50, "VOLVER", GRAY)
        
        # Botones del juego
        self.btn_play_card = Button(50, SCREEN_HEIGHT - 70, 120, 40, "JUGAR", GREEN)
        self.btn_fuse = Button(180, SCREEN_HEIGHT - 70, 120, 40, "FUSIONAR", PURPLE)
        self.btn_position = Button(310, SCREEN_HEIGHT - 70, 120, 40, "POS: ATK", BLUE)
        self.btn_star = Button(440, SCREEN_HEIGHT - 70, 120, 40, "ESTRELLA 1", ORANGE)
        self.btn_battle = Button(570, SCREEN_HEIGHT - 70, 120, 40, "BATALLA", RED)
        self.btn_end_turn = Button(700, SCREEN_HEIGHT - 70, 120, 40, "FIN TURNO", GRAY)
        
        self.menu_buttons = [self.btn_play, self.btn_config, self.btn_rules, self.btn_exit]
        self.config_buttons = [self.btn_deck_minus, self.btn_deck_plus, self.btn_back]
        self.game_buttons = [self.btn_play_card, self.btn_fuse, self.btn_position, 
                            self.btn_star, self.btn_battle, self.btn_end_turn]
    
    def start_game(self):
        """Inicia una nueva partida"""
        self.game_state = GameState(self.deck_size)
        self.game_state.setup_game()
        self.state = "GAME"
        self.selected_card_index = None
        self.fusion_mode = False
        self.fusion_first_card = None
        self.message = "¡Tu turno! Selecciona una carta para jugar."
        self.message_timer = 180
        self.waiting_for_battle = False
        self.update_card_sprites()
        print(f"[Juego] Partida iniciada con {self.deck_size} cartas por mazo")
        print(f"[Juego] Total de cartas disponibles: {len(CARD_DATABASE)}")
        print(f"[Juego] Total de fusiones disponibles: {len(FUSIONS)}")
    
    def update_card_sprites(self):
        """Actualiza los sprites de las cartas"""
        # Mano del jugador
        self.hand_sprites = []
        hand = self.game_state.human.hand
        start_x = (SCREEN_WIDTH - len(hand) * (CARD_WIDTH + 10)) // 2
        for i, card in enumerate(hand):
            sprite = CardSprite(card, start_x + i * (CARD_WIDTH + 10), 
                              SCREEN_HEIGHT - 220, CARD_WIDTH, CARD_HEIGHT)
            self.hand_sprites.append(sprite)
        
        # Mano de la IA (visible en esta versión)
        self.ai_hand_sprites = []
        ai_hand = self.game_state.ai.hand
        start_x = (SCREEN_WIDTH - len(ai_hand) * (SMALL_CARD_WIDTH + 5)) // 2
        for i, card in enumerate(ai_hand):
            sprite = CardSprite(card, start_x + i * (SMALL_CARD_WIDTH + 5), 
                              10, SMALL_CARD_WIDTH, SMALL_CARD_HEIGHT)
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
        
        # Preview de mazos
        self.deck_preview_sprites = []
        upcoming = self.game_state.get_visible_upcoming_cards(self.game_state.human, 3)
        for i, card in enumerate(upcoming):
            sprite = CardSprite(card, SCREEN_WIDTH - 100, 
                              SCREEN_HEIGHT // 2 + 100 + i * 35,
                              70, 30)
            self.deck_preview_sprites.append(sprite)
        
        self.ai_deck_preview_sprites = []
        ai_upcoming = self.game_state.get_visible_upcoming_cards(self.game_state.ai, 3)
        for i, card in enumerate(ai_upcoming):
            sprite = CardSprite(card, 30, 
                              SCREEN_HEIGHT // 2 - 50 + i * 35,
                              70, 30)
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
        if self.selected_card_index is not None:
            position = "ATK" if "ATK" in self.btn_position.text else "DEF"
            star = 1 if "1" in self.btn_star.text else 2
            
            self.game_state.human.play_card(self.selected_card_index, position, star)
            self.selected_card_index = None
            self.update_card_sprites()
            
            # Si hay cartas en ambos campos, esperar para batalla
            if self.game_state.human.field and self.game_state.ai.field:
                self.waiting_for_battle = True
                self.message = "¡Cartas listas! Presiona BATALLA para combatir"
            else:
                self.message = "Carta jugada. Puedes terminar tu turno."
    
    def resolve_battle(self):
        """Resuelve la batalla entre cartas"""
        if self.game_state.human.field and self.game_state.ai.field:
            result = self.game_state.resolve_battle()
            self.waiting_for_battle = False
            
            if result:
                if result["winner"] == "human":
                    self.message = f"¡Ganaste! {result['human_card']} ({result['human_value']}) vs {result['ai_card']} ({result['ai_value']}). Daño: {result['damage']}"
                elif result["winner"] == "ai":
                    self.message = f"¡Perdiste! {result['ai_card']} ({result['ai_value']}) vs {result['human_card']} ({result['human_value']}). Daño: {result['damage']}"
                else:
                    self.message = "¡Empate! Ambas cartas fueron destruidas"
            
            self.update_card_sprites()
            
            if self.game_state.game_over:
                self.state = "GAME_OVER"
    
    def end_turn(self):
        """Termina el turno del jugador"""
        self.game_state.next_turn()
        self.ai_turn()
    
    def ai_turn(self):
        """Ejecuta el turno de la IA"""
        self.ai_thinking = True
        self.message = "La IA está pensando..."
        
        # Actualizar la pantalla para mostrar el mensaje
        self.draw_game()
        pygame.display.flip()
        
        # Obtener mejor movimiento de la IA
        best_action = self.ai.get_best_move(self.game_state)
        
        if best_action:
            if best_action["type"] == "fuse":
                result = self.game_state.ai.fuse_cards(best_action["idx1"], best_action["idx2"])
                if result:
                    self.message = f"La IA fusionó y obtuvo {result.name} (ATK: {result.atk})"
                    self.update_card_sprites()
                    self.draw_game()
                    pygame.display.flip()
                    pygame.time.wait(1500)
                    # La IA puede hacer otra acción después de fusionar
                    best_action = self.ai.get_best_move(self.game_state)
            
            if best_action and best_action["type"] == "play":
                self.game_state.apply_action(self.game_state.ai, best_action)
                card_name = self.game_state.ai.field.name if self.game_state.ai.field else "una carta"
                position = best_action.get("position", "ATK")
                self.message = f"La IA jugó {card_name} en {position}"
        
        self.update_card_sprites()
        
        # Resolver batalla si es posible
        if self.game_state.human.field and self.game_state.ai.field:
            self.draw_game()
            pygame.display.flip()
            pygame.time.wait(1000)
            self.resolve_battle()
        
        self.ai_thinking = False
        
        if not self.game_state.game_over:
            # Pasar turno al jugador
            self.game_state.next_turn()
            self.message = "¡Tu turno! Selecciona una carta."
            self.update_card_sprites()
        else:
            self.state = "GAME_OVER"
    
    def draw_menu(self):
        """Dibuja el menú principal"""
        # Fondo
        self.screen.fill(DARK_BLUE)
        
        # Título
        title = self.font_large.render("Yu-Gi-Oh! Forbidden Memories", True, GOLD)
        title_rect = title.get_rect(centerx=SCREEN_WIDTH // 2, y=100)
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Minimax AI Edition", True, WHITE)
        subtitle_rect = subtitle.get_rect(centerx=SCREEN_WIDTH // 2, y=160)
        self.screen.blit(subtitle, subtitle_rect)
        
        # Info del proyecto
        info = self.font_small.render("Universidad del Valle - Introducción a la IA", True, LIGHT_GRAY)
        info_rect = info.get_rect(centerx=SCREEN_WIDTH // 2, y=220)
        self.screen.blit(info, info_rect)
        
        # Botones
        for btn in self.menu_buttons:
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
        """Dibuja la pantalla del juego"""
        # Fondo
        self.screen.fill((20, 60, 20))
        
        # Línea divisoria del campo
        pygame.draw.line(self.screen, GOLD, (0, SCREEN_HEIGHT // 2), 
                        (SCREEN_WIDTH, SCREEN_HEIGHT // 2), 3)
        
        # Información de jugadores
        self.draw_player_info()
        
        # Campo de batalla
        self.draw_field()
        
        # Manos de cartas
        self.draw_hands()
        
        # Preview de mazos
        self.draw_deck_preview()
        
        # Botones de acción
        self.update_button_states()
        for btn in self.game_buttons:
            btn.draw(self.screen, self.font_small)
        
        # Mensaje
        if self.message:
            msg_surface = self.font_medium.render(self.message, True, YELLOW)
            msg_rect = msg_surface.get_rect(centerx=SCREEN_WIDTH // 2, y=SCREEN_HEIGHT // 2 - 80)
            pygame.draw.rect(self.screen, BLACK, msg_rect.inflate(20, 10))
            self.screen.blit(msg_surface, msg_rect)
        
        # Indicador de turno
        turn_text = "TU TURNO" if self.game_state.current_player == self.game_state.human else "TURNO IA"
        turn_surface = self.font_medium.render(turn_text, True, GREEN if "TU" in turn_text else RED)
        self.screen.blit(turn_surface, (SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2 - 20))
    
    def draw_player_info(self):
        """Dibuja información de los jugadores"""
        # Jugador humano (abajo)
        human_lp = self.font_medium.render(f"LP: {self.game_state.human.life_points}", True, GREEN)
        self.screen.blit(human_lp, (20, SCREEN_HEIGHT - 250))
        
        human_deck = self.font_small.render(f"Mazo: {len(self.game_state.human.deck)}", True, WHITE)
        self.screen.blit(human_deck, (20, SCREEN_HEIGHT - 220))
        
        human_grave = self.font_small.render(f"Cementerio: {len(self.game_state.human.graveyard)}", True, GRAY)
        self.screen.blit(human_grave, (20, SCREEN_HEIGHT - 195))
        
        # IA (arriba)
        ai_lp = self.font_medium.render(f"LP: {self.game_state.ai.life_points}", True, RED)
        self.screen.blit(ai_lp, (20, 130))
        
        ai_deck = self.font_small.render(f"Mazo: {len(self.game_state.ai.deck)}", True, WHITE)
        self.screen.blit(ai_deck, (20, 160))
        
        ai_grave = self.font_small.render(f"Cementerio: {len(self.game_state.ai.graveyard)}", True, GRAY)
        self.screen.blit(ai_grave, (20, 185))
        
        # Turno
        turn = self.font_small.render(f"Turno: {self.game_state.turn_number}", True, GOLD)
        self.screen.blit(turn, (SCREEN_WIDTH - 100, 130))
    
    def draw_field(self):
        """Dibuja el campo de batalla"""
        # Zona de campo del jugador
        player_zone = pygame.Rect(SCREEN_WIDTH // 2 - CARD_WIDTH - 30, 
                                  SCREEN_HEIGHT // 2 + 10,
                                  CARD_WIDTH + 20, CARD_HEIGHT + 20)
        pygame.draw.rect(self.screen, DARK_GREEN, player_zone, 2, border_radius=5)
        
        # Zona de campo de la IA
        ai_zone = pygame.Rect(SCREEN_WIDTH // 2 + 10,
                              SCREEN_HEIGHT // 2 - CARD_HEIGHT - 30,
                              CARD_WIDTH + 20, CARD_HEIGHT + 20)
        pygame.draw.rect(self.screen, DARK_BLUE, ai_zone, 2, border_radius=5)
        
        # Etiquetas
        player_label = self.font_tiny.render("TU CAMPO", True, GREEN)
        self.screen.blit(player_label, (player_zone.x, player_zone.bottom + 5))
        
        ai_label = self.font_tiny.render("CAMPO IA", True, RED)
        self.screen.blit(ai_label, (ai_zone.x, ai_zone.y - 20))
        
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
        self.screen.blit(ai_hand_label, (50, 130))
        
        # Mano de la IA
        for sprite in self.ai_hand_sprites:
            sprite.draw(self.screen, self.font_small, self.font_tiny)
    
    def draw_deck_preview(self):
        """Dibuja la vista previa de los mazos"""
        # Tu mazo
        deck_label = self.font_tiny.render("Próximas cartas:", True, GOLD)
        self.screen.blit(deck_label, (SCREEN_WIDTH - 120, SCREEN_HEIGHT // 2 + 70))
        
        for i, sprite in enumerate(self.deck_preview_sprites):
            # Solo mostrar nombre
            name = sprite.card.name[:10]
            text = self.font_tiny.render(f"{i+1}. {name}", True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH - 120, SCREEN_HEIGHT // 2 + 95 + i * 20))
        
        # Mazo IA
        ai_deck_label = self.font_tiny.render("Próximas IA:", True, GOLD)
        self.screen.blit(ai_deck_label, (20, SCREEN_HEIGHT // 2 - 100))
        
        for i, sprite in enumerate(self.ai_deck_preview_sprites):
            name = sprite.card.name[:10]
            text = self.font_tiny.render(f"{i+1}. {name}", True, WHITE)
            self.screen.blit(text, (20, SCREEN_HEIGHT // 2 - 75 + i * 20))
    
    def update_button_states(self):
        """Actualiza el estado de los botones según el contexto"""
        is_human_turn = self.game_state.current_player == self.game_state.human
        
        self.btn_play_card.enabled = is_human_turn and self.selected_card_index is not None
        self.btn_fuse.enabled = is_human_turn and len(self.game_state.human.hand) >= 2
        self.btn_battle.enabled = is_human_turn and self.waiting_for_battle
        self.btn_end_turn.enabled = is_human_turn and not self.waiting_for_battle
        self.btn_position.enabled = is_human_turn
        self.btn_star.enabled = is_human_turn
    
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
                elif self.btn_end_turn.is_clicked(pos):
                    self.end_turn()
    
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

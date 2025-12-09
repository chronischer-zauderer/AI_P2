# card_image_manager.py - Sistema de gestión de imágenes de cartas
# Yu-Gi-Oh! Forbidden Memories - Minimax AI Edition

import os
import json
import pygame
from urllib.parse import quote
from io import BytesIO

# Configuración
CACHE_DIR = os.path.join(os.path.dirname(__file__), "card_images")
CACHE_INDEX_FILE = os.path.join(CACHE_DIR, "cache_index.json")
API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?name={}"

# Crear directorio de caché si no existe
os.makedirs(CACHE_DIR, exist_ok=True)


class CardImageManager:
    """
    Gestor de imágenes de cartas Yu-Gi-Oh!
    
    Funcionalidades:
    - Descarga imágenes de la API de Yu-Gi-Oh! Pro Deck
    - Caché local para evitar descargas repetidas
    - Fallback a imágenes generadas si falla la descarga
    - Redimensionamiento automático
    """
    
    def __init__(self):
        self.cache_index = self._load_cache_index()
        self.loaded_images = {}  # {card_name: pygame.Surface}
        self.default_image = None
        
    def _load_cache_index(self):
        """Carga el índice de caché desde el archivo JSON"""
        if os.path.exists(CACHE_INDEX_FILE):
            try:
                with open(CACHE_INDEX_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache_index(self):
        """Guarda el índice de caché en el archivo JSON"""
        try:
            with open(CACHE_INDEX_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
        except:
            pass
    
    def get_card_image_path(self, card_name):
        """Obtiene la ruta del archivo de imagen para una carta"""
        # Sanitizar el nombre de archivo
        safe_name = "".join(c for c in card_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        return os.path.join(CACHE_DIR, f"{safe_name}.png")
    
    def download_card_image(self, card_name):
        """
        Intenta descargar la imagen de una carta desde la API
        Retorna True si tuvo éxito, False si falló
        
        NOTA: En este entorno, las descargas externas están bloqueadas,
        pero el código está preparado para cuando se ejecute en un
        entorno con acceso a internet.
        """
        try:
            # Intentar usar urllib (built-in de Python)
            import urllib.request
            
            url = API_URL.format(quote(card_name))
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read())
            
            if data and 'data' in data and len(data['data']) > 0:
                card_data = data['data'][0]
                if 'card_images' in card_data and len(card_data['card_images']) > 0:
                    image_url = card_data['card_images'][0]['image_url']
                    
                    # Descargar la imagen
                    img_response = urllib.request.urlopen(image_url, timeout=5)
                    img_data = img_response.read()
                    
                    # Guardar en caché
                    img_path = self.get_card_image_path(card_name)
                    with open(img_path, 'wb') as f:
                        f.write(img_data)
                    
                    # Actualizar índice
                    self.cache_index[card_name] = img_path
                    self._save_cache_index()
                    return True
        except Exception as e:
            # Si falla la descarga (esperado en este entorno), no hacer nada
            pass
        
        return False
    
    def create_fallback_image(self, card, width, height):
        """
        Crea una imagen de carta mejorada cuando no hay imagen real disponible
        """
        # Crear superficie
        surface = pygame.Surface((width, height))
        
        # Colores según atributo
        attribute_colors = {
            "Light": (255, 230, 150),
            "Dark": (100, 80, 130),
            "Fire": (255, 100, 80),
            "Water": (80, 150, 255),
            "Earth": (150, 120, 80),
            "Wind": (150, 255, 150),
            "Divine": (255, 215, 0)
        }
        
        bg_color = attribute_colors.get(card.attribute, (200, 200, 200))
        surface.fill(bg_color)
        
        # Borde decorativo
        border_color = (50, 50, 50)
        pygame.draw.rect(surface, border_color, surface.get_rect(), 3, border_radius=5)
        
        # Borde interno dorado
        inner_rect = pygame.Rect(5, 5, width - 10, height - 10)
        pygame.draw.rect(surface, (218, 165, 32), inner_rect, 2, border_radius=4)
        
        # Área de imagen (superior)
        img_area = pygame.Rect(10, 10, width - 20, int(height * 0.5))
        
        # Gradiente simple para el área de imagen
        for i in range(img_area.height):
            alpha = i / img_area.height
            color_start = tuple(int(c * 0.7) for c in bg_color)
            color_end = tuple(int(c * 1.2) for c in bg_color)
            color = tuple(int(color_start[j] + (color_end[j] - color_start[j]) * alpha) 
                         for j in range(3))
            pygame.draw.line(surface, color, 
                           (img_area.left, img_area.top + i),
                           (img_area.right, img_area.top + i))
        
        pygame.draw.rect(surface, border_color, img_area, 2, border_radius=3)
        
        # Nombre de la carta (con fondo)
        font_name = pygame.font.Font(None, max(16, int(height * 0.12)))
        name_text = card.name[:18] + "..." if len(card.name) > 18 else card.name
        text_surface = font_name.render(name_text, True, (255, 255, 255))
        text_bg = pygame.Surface((width - 20, text_surface.get_height() + 6))
        text_bg.fill((0, 0, 0))
        text_bg.set_alpha(180)
        
        name_y = img_area.bottom + 5
        surface.blit(text_bg, (10, name_y))
        surface.blit(text_surface, (15, name_y + 3))
        
        # Tipo/Atributo
        font_small = pygame.font.Font(None, max(14, int(height * 0.10)))
        type_text = f"{card.card_type} / {card.attribute}"
        type_surface = font_small.render(type_text, True, (50, 50, 50))
        surface.blit(type_surface, (15, name_y + text_surface.get_height() + 8))
        
        # ATK/DEF (parte inferior)
        stats_y = height - 35
        
        # Fondo para stats
        stats_bg = pygame.Surface((width - 20, 30))
        stats_bg.fill((240, 240, 240))
        pygame.draw.rect(stats_bg, border_color, stats_bg.get_rect(), 1)
        surface.blit(stats_bg, (10, stats_y))
        
        font_stats = pygame.font.Font(None, max(16, int(height * 0.11)))
        atk_text = font_stats.render(f"ATK/{card.atk}", True, (200, 50, 50))
        def_text = font_stats.render(f"DEF/{card.defense}", True, (50, 50, 200))
        
        surface.blit(atk_text, (15, stats_y + 7))
        surface.blit(def_text, (width - def_text.get_width() - 15, stats_y + 7))
        
        # Estrellas guardianas (iconos pequeños)
        star_y = stats_y - 20
        star_colors = {
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
        
        star1_color = star_colors.get(card.star1, (200, 200, 0))
        star2_color = star_colors.get(card.star2, (200, 200, 0))
        
        # Dibujar estrella seleccionada con círculo más grande
        if card.selected_star == card.star1:
            pygame.draw.circle(surface, star1_color, (20, star_y), 8)
            pygame.draw.circle(surface, (255, 255, 255), (20, star_y), 8, 2)
            pygame.draw.circle(surface, star2_color, (40, star_y), 6)
        else:
            pygame.draw.circle(surface, star1_color, (20, star_y), 6)
            pygame.draw.circle(surface, star2_color, (40, star_y), 8)
            pygame.draw.circle(surface, (255, 255, 255), (40, star_y), 8, 2)
        
        # Indicador de posición (esquina superior derecha)
        pos_color = (50, 200, 50) if card.position == "ATK" else (50, 50, 200)
        pos_rect = pygame.Rect(width - 25, 15, 20, 20)
        pygame.draw.circle(surface, pos_color, pos_rect.center, 10)
        pygame.draw.circle(surface, (255, 255, 255), pos_rect.center, 10, 2)
        
        font_tiny = pygame.font.Font(None, 16)
        pos_char = "A" if card.position == "ATK" else "D"
        pos_text = font_tiny.render(pos_char, True, (255, 255, 255))
        pos_text_rect = pos_text.get_rect(center=pos_rect.center)
        surface.blit(pos_text, pos_text_rect)
        
        return surface
    
    def get_card_image(self, card, width, height):
        """
        Obtiene la imagen de una carta (descargada o generada)
        
        Args:
            card: Objeto Card
            width: Ancho deseado
            height: Alto deseado
            
        Returns:
            pygame.Surface con la imagen de la carta
        """
        cache_key = f"{card.name}_{width}_{height}"
        
        # Si ya está cargada en memoria, devolverla
        if cache_key in self.loaded_images:
            return self.loaded_images[cache_key]
        
        # Verificar si existe en caché local
        img_path = self.get_card_image_path(card.name)
        
        if os.path.exists(img_path):
            try:
                # Cargar desde caché
                image = pygame.image.load(img_path)
                image = pygame.transform.scale(image, (width, height))
                self.loaded_images[cache_key] = image
                return image
            except:
                pass
        
        # Si no está en caché, intentar descargar (probablemente fallará en este entorno)
        # pero el código está preparado para cuando se ejecute con acceso a internet
        if card.name not in self.cache_index:
            self.download_card_image(card.name)
            
            # Verificar nuevamente si se descargó
            if os.path.exists(img_path):
                try:
                    image = pygame.image.load(img_path)
                    image = pygame.transform.scale(image, (width, height))
                    self.loaded_images[cache_key] = image
                    return image
                except:
                    pass
        
        # Fallback: crear imagen generada
        image = self.create_fallback_image(card, width, height)
        self.loaded_images[cache_key] = image
        return image
    
    def clear_cache(self):
        """Limpia la caché de imágenes en memoria"""
        self.loaded_images.clear()


# Instancia global del gestor
_card_image_manager = None

def get_card_image_manager():
    """Obtiene la instancia global del gestor de imágenes"""
    global _card_image_manager
    if _card_image_manager is None:
        _card_image_manager = CardImageManager()
    return _card_image_manager

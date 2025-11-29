# cards.py - Base de datos de cartas de Yu-Gi-Oh! Forbidden Memories
# Carga las cartas desde los archivos CSV

import csv
import os

# Directorio de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Estrellas Guardianas y sus relaciones
# Según las reglas de Forbidden Memories
GUARDIAN_STARS = {
    "Sol": {"strong": "Luna", "weak": "Mercurio"},
    "Luna": {"strong": "Venus", "weak": "Sol"},
    "Venus": {"strong": "Mercurio", "weak": "Luna"},
    "Mercurio": {"strong": "Sol", "weak": "Venus"},
    "Marte": {"strong": "Jupiter", "weak": "Neptuno"},
    "Jupiter": {"strong": "Saturno", "weak": "Marte"},
    "Saturno": {"strong": "Urano", "weak": "Jupiter"},
    "Urano": {"strong": "Pluton", "weak": "Saturno"},
    "Pluton": {"strong": "Neptuno", "weak": "Urano"},
    "Neptuno": {"strong": "Marte", "weak": "Pluton"}
}

# Mapeo de atributos a estrellas guardianas
ATTRIBUTE_TO_STARS = {
    "Light": ("Sol", "Mercurio"),
    "Dark": ("Luna", "Venus"),
    "Fire": ("Marte", "Sol"),
    "Water": ("Neptuno", "Luna"),
    "Earth": ("Urano", "Jupiter"),
    "Wind": ("Saturno", "Jupiter"),
    "Divine": ("Sol", "Luna")
}

# Mapeo de tipos a estrellas guardianas secundarias
TYPE_TO_STARS = {
    "Dragon": ("Marte", "Luna"),
    "Spellcaster": ("Mercurio", "Venus"),
    "Warrior": ("Urano", "Sol"),
    "Beast": ("Jupiter", "Saturno"),
    "Beast-Warrior": ("Jupiter", "Urano"),
    "Winged-Beast": ("Saturno", "Jupiter"),
    "Fiend": ("Luna", "Venus"),
    "Zombie": ("Luna", "Pluton"),
    "Machine": ("Pluton", "Urano"),
    "Aqua": ("Neptuno", "Luna"),
    "Fish": ("Neptuno", "Saturno"),
    "Sea-Serpent": ("Neptuno", "Marte"),
    "Reptile": ("Urano", "Neptuno"),
    "Pyro": ("Marte", "Sol"),
    "Thunder": ("Pluton", "Saturno"),
    "Rock": ("Urano", "Marte"),
    "Plant": ("Jupiter", "Sol"),
    "Insect": ("Jupiter", "Luna"),
    "Fairy": ("Sol", "Venus"),
    "Dinosaur": ("Urano", "Marte")
}


class Card:
    """Clase para representar una carta de monstruo"""
    def __init__(self, card_id, name, card_type, atk, defense, attribute, level):
        self.id = card_id
        self.name = name
        self.card_type = card_type
        self.atk = int(atk)
        self.defense = int(defense)
        self.attribute = attribute
        self.level = int(level)
        
        # Asignar estrellas guardianas basándose en atributo y tipo
        self.star1, self.star2 = self._assign_guardian_stars()
        self.selected_star = self.star1
        self.position = "ATK"  # ATK o DEF
    
    def _assign_guardian_stars(self):
        """Asigna estrellas guardianas según atributo y tipo"""
        # Primera estrella por atributo
        if self.attribute in ATTRIBUTE_TO_STARS:
            star1 = ATTRIBUTE_TO_STARS[self.attribute][0]
        else:
            star1 = "Urano"
        
        # Segunda estrella por tipo
        if self.card_type in TYPE_TO_STARS:
            star2 = TYPE_TO_STARS[self.card_type][1]
        else:
            star2 = "Jupiter"
        
        # Evitar estrellas iguales
        if star1 == star2:
            star2 = ATTRIBUTE_TO_STARS.get(self.attribute, ("Urano", "Jupiter"))[1]
        
        return star1, star2
    
    def get_battle_value(self):
        """Retorna el valor de batalla según la posición"""
        return self.atk if self.position == "ATK" else self.defense
    
    def set_position(self, position):
        """Establece la posición de la carta (ATK/DEF)"""
        self.position = position
    
    def select_star(self, star_num):
        """Selecciona la estrella guardiana (1 o 2)"""
        self.selected_star = self.star1 if star_num == 1 else self.star2
    
    def copy(self):
        """Crea una copia de la carta"""
        new_card = Card(self.id, self.name, self.card_type, self.atk, 
                       self.defense, self.attribute, self.level)
        new_card.star1 = self.star1
        new_card.star2 = self.star2
        new_card.selected_star = self.selected_star
        new_card.position = self.position
        return new_card
    
    def __str__(self):
        return f"{self.name} (ATK:{self.atk}/DEF:{self.defense}) [{self.star1}/{self.star2}]"
    
    def __repr__(self):
        return self.__str__()


class Fusion:
    """Clase para representar una fusión"""
    def __init__(self, material1, material2, result_name, result_atk, result_def, result_attr, result_type):
        self.material1 = material1
        self.material2 = material2
        self.result_name = result_name
        self.result_atk = int(result_atk)
        self.result_def = int(result_def)
        self.result_attr = result_attr
        self.result_type = result_type


# Variables globales para almacenar los datos
CARD_DATABASE = []
FUSIONS = []
CARD_BY_NAME = {}
CARD_BY_ID = {}


def load_monsters_from_csv():
    """Carga los monstruos desde el archivo CSV"""
    global CARD_DATABASE, CARD_BY_NAME, CARD_BY_ID
    
    filepath = os.path.join(DATA_DIR, "monsters.csv")
    CARD_DATABASE = []
    CARD_BY_NAME = {}
    CARD_BY_ID = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            card = Card(
                card_id=int(row['id']),
                name=row['name'],
                card_type=row['type'],
                atk=row['atk'],
                defense=row['def'],
                attribute=row['attribute'],
                level=row['level']
            )
            CARD_DATABASE.append(card)
            CARD_BY_NAME[card.name.lower()] = card
            CARD_BY_ID[card.id] = card
    
    print(f"[Cards] Cargadas {len(CARD_DATABASE)} cartas")
    return CARD_DATABASE


def load_fusions_from_csv():
    """Carga las fusiones desde el archivo CSV"""
    global FUSIONS
    
    filepath = os.path.join(DATA_DIR, "fusions.csv")
    FUSIONS = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fusion = Fusion(
                material1=row['Material1'],
                material2=row['Material2'],
                result_name=row['Result'],
                result_atk=row['Result_Attack'],
                result_def=row['Result_Defense'],
                result_attr=row['Result_Attribute'],
                result_type=row['Result_Type']
            )
            FUSIONS.append(fusion)
    
    print(f"[Cards] Cargadas {len(FUSIONS)} fusiones")
    return FUSIONS


def initialize_card_database():
    """Inicializa la base de datos de cartas"""
    load_monsters_from_csv()
    load_fusions_from_csv()


def get_card_by_id(card_id):
    """Obtiene una carta por su ID"""
    if card_id in CARD_BY_ID:
        return CARD_BY_ID[card_id].copy()
    return None


def get_card_by_name(name):
    """Obtiene una carta por su nombre"""
    name_lower = name.lower()
    if name_lower in CARD_BY_NAME:
        return CARD_BY_NAME[name_lower].copy()
    return None


def check_fusion(card1_name, card2_name):
    """
    Verifica si dos cartas pueden fusionarse y retorna el resultado.
    Args:
        card1_name: Nombre de la primera carta
        card2_name: Nombre de la segunda carta
    Returns:
        Card: La carta resultante de la fusión, o None si no hay fusión
    """
    for fusion in FUSIONS:
        # Verificar ambas combinaciones (orden no importa)
        if (fusion.material1.lower() == card1_name.lower() and 
            fusion.material2.lower() == card2_name.lower()) or \
           (fusion.material1.lower() == card2_name.lower() and 
            fusion.material2.lower() == card1_name.lower()):
            
            # Crear la carta resultado
            result_card = Card(
                card_id=9000 + FUSIONS.index(fusion),  # ID especial para fusiones
                name=fusion.result_name,
                card_type=fusion.result_type,
                atk=fusion.result_atk,
                defense=fusion.result_def,
                attribute=fusion.result_attr,
                level=7  # Nivel por defecto para fusiones
            )
            return result_card
    
    return None


def check_fusion_by_cards(card1, card2):
    """
    Verifica si dos objetos Card pueden fusionarse.
    """
    return check_fusion(card1.name, card2.name)


def calculate_star_bonus(attacker_star, defender_star):
    """
    Calcula el bonus de estrella guardiana.
    +500 si tiene ventaja, -500 si tiene desventaja, 0 si neutral.
    """
    if attacker_star not in GUARDIAN_STARS:
        return 0
    
    if GUARDIAN_STARS[attacker_star]["strong"] == defender_star:
        return 500
    elif GUARDIAN_STARS[attacker_star]["weak"] == defender_star:
        return -500
    return 0


def get_all_cards():
    """Retorna una copia de todas las cartas"""
    return [card.copy() for card in CARD_DATABASE]


def get_random_deck(size):
    """Genera un mazo aleatorio del tamaño especificado"""
    import random
    all_cards = get_all_cards()
    random.shuffle(all_cards)
    return all_cards[:size]


def get_possible_fusions_for_hand(hand):
    """
    Encuentra todas las fusiones posibles para una mano de cartas.
    Args:
        hand: Lista de cartas en la mano
    Returns:
        Lista de tuplas (idx1, idx2, resultado)
    """
    possible = []
    for i in range(len(hand)):
        for j in range(i + 1, len(hand)):
            result = check_fusion_by_cards(hand[i], hand[j])
            if result:
                possible.append((i, j, result))
    return possible


# Inicializar al importar el módulo
initialize_card_database()


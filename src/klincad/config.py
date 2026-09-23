from PyQt5.QtGui import QColor


# Tamaño de la cuadrícula principal del editor.
GRID_SIZE = 20

# Distancia máxima utilizada para detectar conexiones cercanas.
SNAP_THRESHOLD = 15.0

# Escala física de la escena.
SCENE_UNITS_PER_MM = 1.0

# Conversión de milímetros a puntos PDF.
PDF_PT_PER_MM = 72.0 / 25.4


# Configuración visual y orden de las capas del PCB.
CAPAS_CONFIG = {
    "Top Copper": {
        "color": QColor("#ef4444"),
        "z_index": 10
    },
    "Bottom Copper": {
        "color": QColor("#2563eb"),
        "z_index": 9
    },
    "General / Jumpers": {
        "color": QColor("#22c55e"),
        "z_index": 8
    },
    "Power / Notes": {
        "color": QColor("#f59e0b"),
        "z_index": 7
    }
}

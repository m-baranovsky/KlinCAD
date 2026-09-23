# =============================================================================
# KlinCAD - Utilidades geométricas
# =============================================================================

from PyQt5.QtCore import QPointF

from klincad.config import GRID_SIZE


def snap_to_grid(pos_o_val):
    """
    Ajusta una posición o un valor numérico a la cuadrícula de KlinCAD.

    Acepta:
    - QPointF: devuelve una nueva QPointF ajustada.
    - Valor numérico: devuelve el valor ajustado.
    """
    if isinstance(pos_o_val, QPointF):
        x = round(pos_o_val.x() / GRID_SIZE) * GRID_SIZE
        y = round(pos_o_val.y() / GRID_SIZE) * GRID_SIZE
        return QPointF(x, y)

    return round(pos_o_val / GRID_SIZE) * GRID_SIZE

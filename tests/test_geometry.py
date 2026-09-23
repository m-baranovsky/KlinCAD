from PyQt5.QtCore import QPointF

from klincad.config import GRID_SIZE
from klincad.utils.geometry import snap_to_grid


def test_snap_to_grid_qpointf():
    punto = QPointF(43, 57)

    resultado = snap_to_grid(punto)

    assert resultado.x() == round(43 / GRID_SIZE) * GRID_SIZE
    assert resultado.y() == round(57 / GRID_SIZE) * GRID_SIZE


def test_snap_to_grid_numero():
    resultado = snap_to_grid(43)

    assert resultado == round(43 / GRID_SIZE) * GRID_SIZE

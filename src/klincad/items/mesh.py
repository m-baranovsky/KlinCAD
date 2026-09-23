# =============================================================================
# KlinCAD - Malla
# =============================================================================

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
)

from klincad.items.component import BaseItemRotable
from klincad.utils.geometry import snap_to_grid

class Malla(QGraphicsRectItem, BaseItemRotable):
    def __init__(self, x, y):
        super().__init__(0, 0, 100, 80)

        # Sin caché para evitar rastros visuales durante el movimiento.
        self.setCacheMode(QGraphicsItem.NoCache)

        pos_snapped = snap_to_grid(
            QPointF(x, y)
        )
        self.setPos(pos_snapped)

        self.setBrush(
            QBrush(QColor(240, 200, 80, 30))
        )

        self.setPen(
            QPen(
                QColor("#d97706"),
                1,
                Qt.DashLine,
            )
        )

        self.label = QGraphicsTextItem(
            "Malla",
            self,
        )

        self.label.setDefaultTextColor(
            QColor("#f59e0b")
        )

        self.label.setPos(2, 2)

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
        )

        self.preparar_origen_rotacion()

    def obtener_puntos_conexion(self):
        return []

    def itemChange(
        self,
        change,
        value,
    ):
        if change == QGraphicsItem.ItemPositionChange:
            return snap_to_grid(value)

        return super().itemChange(
            change,
            value,
        )

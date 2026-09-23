# =============================================================================
# KlinCAD - Nodos
# =============================================================================

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsItem

from klincad.items.component import BaseItemRotable
from klincad.utils.geometry import snap_to_grid


class Nodo(QGraphicsEllipseItem, BaseItemRotable):
    def __init__(self, x, y):
        super().__init__(-5, -5, 10, 10)

        self.setCacheMode(QGraphicsItem.NoCache)

        pos_snapped = snap_to_grid(
            QPointF(x, y)
        )
        self.setPos(pos_snapped)

        self.setBrush(
            QBrush(QColor("#38bdf8"))
        )

        self.setPen(
            QPen(QColor("#0284c7"))
        )

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
        )

        self.preparar_origen_rotacion()
        self.is_highlighted = False

    def paint(
        self,
        painter,
        option,
        widget=None,
    ):
        if getattr(
            self,
            "is_highlighted",
            False,
        ):
            self.setBrush(
                QBrush(QColor("#facc15"))
            )
            self.setPen(
                QPen(QColor("#ca8a04"), 2)
            )
        else:
            self.setBrush(
                QBrush(QColor("#38bdf8"))
            )
            self.setPen(
                QPen(QColor("#0284c7"), 1)
            )

        super().paint(
            painter,
            option,
            widget,
        )

    def obtener_puntos_conexion(self):
        return [self.scenePos()]

    def itemChange(
        self,
        change,
        value,
    ):
        if (
            change == QGraphicsItem.ItemPositionChange
            and self.scene()
        ):
            new_pos = snap_to_grid(value)
            self.scene().actualizar_indicadores_conexion()
            return new_pos

        return super().itemChange(
            change,
            value,
        )

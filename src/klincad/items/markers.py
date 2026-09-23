# =============================================================================
# KlinCAD - Marcadores visuales
# =============================================================================

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QBrush, QColor, QPen, QPolygonF
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsPolygonItem,
)


class FlechaError(QGraphicsPolygonItem):
    def __init__(self, x, y):
        poly = QPolygonF([
            QPointF(0, 0),
            QPointF(10, -15),
            QPointF(4, -15),
            QPointF(4, -35),
            QPointF(-4, -35),
            QPointF(-4, -15),
            QPointF(-10, -15),
        ])

        super().__init__(poly)

        self.setBrush(QBrush(QColor("#ef4444")))
        self.setPen(QPen(QColor("#000000"), 1.5))
        self.setPos(x, y)

        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable
        )

        self.setZValue(100)

        self.setToolTip(
            "Pin Flotante / Error. "
            "Borra esta flecha (Supr) tras corregirlo."
        )


class IndicadorConexion(QGraphicsEllipseItem):
    def __init__(self, x, y):
        super().__init__(-4, -4, 8, 8)

        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setPos(x, y)

        self.setBrush(QBrush(QColor("#ef4444")))
        self.setPen(QPen(QColor("#b91c1c"), 1.5))

        self.setZValue(50)

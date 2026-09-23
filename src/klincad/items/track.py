# =============================================================================
# KlinCAD - Pistas de PCB
# =============================================================================

from PyQt5.QtCore import QPointF, QLineF, Qt, QTransform
from PyQt5.QtGui import QColor, QPainterPathStroker, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
)

from klincad.config import CAPAS_CONFIG
from klincad.items.component import BaseItemRotable
from klincad.utils.geometry import snap_to_grid


class PuntoExtremoPista(QGraphicsEllipseItem):
    """
    Handle interactivo de un extremo de PistaInteractiva.
    """

    def __init__(self, indice_extremo, pista_padre):
        super().__init__(-6, -6, 12, 12, pista_padre)

        self.indice_extremo = indice_extremo
        self.pista_padre = pista_padre

        self.setBrush(QColor("#ffffff"))
        self.setPen(QPen(QColor("#000000"), 1.5))
        self.setZValue(30)
        self.setVisible(False)

        self._moviendose = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pista = self.pista_padre

            if pista is None or pista.scene() is None:
                event.ignore()
                return

            self._moviendose = True

            if (
                pista.scene().views()
                and hasattr(
                    pista.scene().views()[0].window(),
                    "registrar_accion_inicio",
                )
            ):
                pista.scene().views()[0].window().registrar_accion_inicio()

            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pista = self.pista_padre

        if pista is None or pista.scene() is None:
            event.ignore()
            return

        if event.buttons() & Qt.LeftButton:
            pos_escena = event.scenePos()

            pin_cercano = pista.scene().buscar_terminal_cercano(
                pos_escena,
                ignorar_item=pista,
            )

            pos_final = (
                pin_cercano
                if pin_cercano
                else snap_to_grid(pos_escena)
            )

            pista.mover_extremo(
                self.indice_extremo,
                pos_final,
            )

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        pista = self.pista_padre

        if event.button() == Qt.LeftButton:
            if (
                self._moviendose
                and pista is not None
                and pista.scene() is not None
            ):
                escena = pista.scene()

                if (
                    escena.views()
                    and hasattr(
                        escena.views()[0].window(),
                        "registrar_accion_fin",
                    )
                ):
                    escena.views()[0].window().registrar_accion_fin()

                self._moviendose = False
                escena.actualizar_indicadores_conexion()

            event.accept()
        else:
            super().mouseReleaseEvent(event)


class PistaInteractiva(QGraphicsLineItem, BaseItemRotable):
    """
    Representa una pista de cobre.

    La orientación se conserva mediante los extremos de QLineF, evitando
    acumular transformaciones de rotación sobre el QGraphicsItem.
    """

    def __init__(
        self,
        x1,
        y1,
        x2,
        y2,
        capa="Top Copper",
    ):
        super().__init__(x1, y1, x2, y2)

        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

        self.capa = capa

        cfg = CAPAS_CONFIG.get(
            capa,
            CAPAS_CONFIG["Top Copper"],
        )

        self.color = cfg["color"]

        self.pen_normal = QPen(
            self.color,
            3,
        )

        self.pen_normal.setCapStyle(
            Qt.RoundCap
        )

        self.pen_normal.setJoinStyle(
            Qt.RoundJoin
        )

        self.setPen(self.pen_normal)
        self.setZValue(cfg["z_index"])

        self.setFlags(
            QGraphicsItem.ItemIsMovable
            | QGraphicsItem.ItemIsSelectable
        )

        self.preparar_origen_rotacion()

        self.handle_p1 = PuntoExtremoPista(
            0,
            self,
        )

        self.handle_p2 = PuntoExtremoPista(
            1,
            self,
        )

        self.actualizar_posicion_handles()

        self.is_highlighted = False
        self._disposed = False

    def liberar_recursos(self):
        """
        Rompe referencias cruzadas y retira los handles antes de eliminar
        la pista.
        """
        if getattr(self, "_disposed", False):
            return

        self._disposed = True

        escena = self.scene()

        for attr in (
            "handle_p1",
            "handle_p2",
        ):
            handle = getattr(
                self,
                attr,
                None,
            )

            if handle is None:
                continue

            if (
                escena is not None
                and handle.scene() is escena
            ):
                escena.removeItem(handle)

            handle._moviendose = False
            handle.pista_padre = None
            handle.setParentItem(None)

            setattr(
                self,
                attr,
                None,
            )

        if (
            escena is not None
            and self.scene() is escena
        ):
            escena.removeItem(self)

        self.update()

    def paint(
        self,
        painter,
        option,
        widget=None,
    ):
        pen = QPen(
            self.color,
            3,
        )

        if getattr(
            self,
            "is_highlighted",
            False,
        ):
            pen.setColor(
                QColor("#facc15")
            )
            pen.setWidth(6)

        elif self.isSelected():
            pen.setColor(
                QColor("#ffffff")
                if getattr(
                    self.scene(),
                    "modo_oscuro",
                    False,
                )
                else QColor("#000000")
            )

            pen.setWidth(4)

        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        painter.setPen(pen)
        painter.drawLine(self.line())

    def actualizar_posicion_handles(self):
        linea = self.line()

        if self.handle_p1 is not None:
            self.handle_p1.setPos(
                linea.p1()
            )

        if self.handle_p2 is not None:
            self.handle_p2.setPos(
                linea.p2()
            )

    def mover_extremo(
        self,
        indice_extremo,
        pos_global,
    ):
        """
        Mueve un extremo usando siempre coordenadas absolutas de escena.

        Las pistas no mantienen una transformación de rotación acumulativa:
        su orientación se representa directamente por los dos extremos del
        QLineF.
        """
        if (
            self.scene() is None
            or getattr(
                self,
                "_disposed",
                False,
            )
        ):
            return

        linea = self.line()

        p1_scene = self.mapToScene(
            linea.p1()
        )

        p2_scene = self.mapToScene(
            linea.p2()
        )

        if indice_extremo == 0:
            p1_scene = QPointF(
                pos_global
            )
        else:
            p2_scene = QPointF(
                pos_global
            )

        self.setRotation(0.0)

        self.setTransformOriginPoint(
            QPointF(0.0, 0.0)
        )

        nueva_p1 = self.mapFromScene(
            p1_scene
        )

        nueva_p2 = self.mapFromScene(
            p2_scene
        )

        self.setLine(
            QLineF(
                nueva_p1,
                nueva_p2,
            )
        )

        self.preparar_origen_rotacion()
        self.actualizar_posicion_handles()

        self.scene().actualizar_indicadores_conexion()

    def rotar_geometria(
        self,
        grados=1.0,
    ):
        """
        Rota la geometría de la pista alrededor de su centro en escena.

        La rotación se materializa en los extremos del QLineF y no en la
        transformación del QGraphicsItem.
        """
        if (
            self.scene() is None
            or getattr(
                self,
                "_disposed",
                False,
            )
        ):
            return

        linea = self.line()

        p1_scene = self.mapToScene(
            linea.p1()
        )

        p2_scene = self.mapToScene(
            linea.p2()
        )

        centro = (
            p1_scene + p2_scene
        ) / 2.0

        transform = QTransform()

        transform.translate(
            centro.x(),
            centro.y(),
        )

        transform.rotate(
            grados
        )

        transform.translate(
            -centro.x(),
            -centro.y(),
        )

        nuevo_p1_scene = transform.map(
            p1_scene
        )

        nuevo_p2_scene = transform.map(
            p2_scene
        )

        self.setRotation(0.0)

        self.setTransformOriginPoint(
            QPointF(0.0, 0.0)
        )

        self.setLine(
            QLineF(
                self.mapFromScene(
                    nuevo_p1_scene
                ),
                self.mapFromScene(
                    nuevo_p2_scene
                ),
            )
        )

        self.preparar_origen_rotacion()
        self.actualizar_posicion_handles()

    def shape(self):
        path = super().shape()

        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        stroker.setCapStyle(Qt.RoundCap)
        stroker.setJoinStyle(Qt.RoundJoin)

        return stroker.createStroke(path)

    def itemChange(
        self,
        change,
        value,
    ):
        if (
            change
            == QGraphicsItem.ItemSelectedHasChanged
        ):
            seleccionado = bool(value)

            if self.handle_p1 is not None:
                self.handle_p1.setVisible(
                    seleccionado
                )

            if self.handle_p2 is not None:
                self.handle_p2.setVisible(
                    seleccionado
                )

        return super().itemChange(
            change,
            value,
        )

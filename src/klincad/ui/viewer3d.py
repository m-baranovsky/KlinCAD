# =============================================================================
# KlinCAD - Visor isométrico 2.5D
# =============================================================================

import math

from PyQt5.QtCore import QPoint, QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from klincad.items.component import ComponenteLiviano
from klincad.items.track import PistaInteractiva


# -----------------------------------------------------------------------------
# Renderizador 2.5D.
# La geometría se cachea para evitar recalcularla en cada repaint.
class VisorIsometricoWidget(QWidget):

    def __init__(self, scene, parent=None):
        super().__init__(parent)

        self.scene = scene

        self.angle_yaw = 45.0
        self.angle_pitch = 35.0
        self.scale_factor = 0.35

        self._dragging_3d = False
        self._last_mouse_pos = QPoint()

        self._geometry_cache = None

        self.actualizar_trigonometria()

    def invalidar_cache_geometria(self):
        self._geometry_cache = None
        self.update()

    def actualizar_trigonometria(self):
        rad_yaw = math.radians(
            self.angle_yaw
        )

        rad_pitch = math.radians(
            self.angle_pitch
        )

        self._cos_yaw = math.cos(
            rad_yaw
        )

        self._sin_yaw = math.sin(
            rad_yaw
        )

        self._cos_pitch = math.cos(
            rad_pitch
        )

        self._sin_pitch = math.sin(
            rad_pitch
        )

    def _obtener_geometria_cacheada(self):
        if self._geometry_cache is not None:
            return self._geometry_cache

        pistas = []
        componentes = []

        bounds = None

        for item in self.scene.items():

            if not item.isVisible():
                continue

            if isinstance(
                item,
                PistaInteractiva
            ):
                linea = item.line()

                p1 = item.mapToScene(
                    linea.p1()
                )

                p2 = item.mapToScene(
                    linea.p2()
                )

                pistas.append(
                    (
                        p1,
                        p2,
                        item.capa,
                        item.color,
                    )
                )

                r = item.sceneBoundingRect()

                if bounds is None:
                    bounds = r
                else:
                    bounds = bounds.united(r)

            elif isinstance(
                item,
                ComponenteLiviano
            ):
                pos = item.scenePos()

                rect = item.rect()

                pins = tuple(
                    item.obtener_puntos_conexion()
                )

                componentes.append(
                    (
                        item.tipo,
                        pos,
                        rect.width(),
                        rect.height(),
                        pins,
                    )
                )

                r = item.mapRectToScene(
                    rect
                )

                if bounds is None:
                    bounds = r
                else:
                    bounds = bounds.united(r)

        if bounds is None:
            bounds = QRectF(
                -150,
                -150,
                300,
                300,
            )
        else:
            bounds = bounds.adjusted(
                -60,
                -60,
                60,
                60,
            )

        self._geometry_cache = {
            "pistas": pistas,
            "componentes": componentes,
            "bounds": bounds,
        }

        return self._geometry_cache

    def wheelEvent(self, event):
        delta = event.angleDelta().y()

        if delta > 0:
            self.scale_factor *= 1.15
        else:
            self.scale_factor /= 1.15

        self.scale_factor = max(
            0.15,
            min(
                2.0,
                self.scale_factor,
            ),
        )

        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.RightButton
            or event.button() == Qt.LeftButton
        ):
            self._dragging_3d = True
            self._last_mouse_pos = event.pos()
            self.setCursor(
                Qt.ClosedHandCursor
            )
            event.accept()

        else:
            super().mousePressEvent(
                event
            )

    def mouseMoveEvent(self, event):
        if self._dragging_3d:
            delta = (
                event.pos()
                - self._last_mouse_pos
            )

            self._last_mouse_pos = event.pos()

            self.angle_yaw = (
                self.angle_yaw
                + delta.x() * 0.5
            ) % 360

            self.angle_pitch = max(
                5.0,
                min(
                    85.0,
                    self.angle_pitch
                    - delta.y() * 0.5,
                ),
            )

            self.actualizar_trigonometria()
            self.update()

            event.accept()

        else:
            super().mouseMoveEvent(
                event
            )

    def mouseReleaseEvent(self, event):
        if (
            (
                event.button()
                == Qt.RightButton
                or event.button()
                == Qt.LeftButton
            )
            and self._dragging_3d
        ):
            self._dragging_3d = False

            self.setCursor(
                Qt.ArrowCursor
            )

            event.accept()

        else:
            super().mouseReleaseEvent(
                event
            )

    def proyectar_3d(self, x, y, z):
        x_rot = (
            x * self._cos_yaw
            - y * self._sin_yaw
        )

        y_rot = (
            x * self._sin_yaw
            + y * self._cos_yaw
        )

        y_proj = (
            y_rot * self._sin_pitch
            - z * self._cos_pitch
        )

        cx = self.width() / 2
        cy = self.height() / 2 + 15

        return QPointF(
            cx
            + x_rot * self.scale_factor,
            cy
            + y_proj * self.scale_factor,
        )

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.fillRect(
            self.rect(),
            QColor("#0f172a")
        )

        cache = (
            self._obtener_geometria_cacheada()
        )

        pistas = cache["pistas"]
        componentes = cache["componentes"]
        bounds = cache["bounds"]

        c_x = bounds.center().x()
        c_y = bounds.center().y()

        l = bounds.left() - c_x
        r = bounds.right() - c_x
        t = bounds.top() - c_y
        b = bounds.bottom() - c_y

        thickness = 12

        p_top_fl = self.proyectar_3d(
            l, t, 0
        )

        p_top_fr = self.proyectar_3d(
            r, t, 0
        )

        p_top_br = self.proyectar_3d(
            r, b, 0
        )

        p_top_bl = self.proyectar_3d(
            l, b, 0
        )

        p_bot_fl = self.proyectar_3d(
            l, t, -thickness
        )

        p_bot_fr = self.proyectar_3d(
            r, t, -thickness
        )

        p_bot_br = self.proyectar_3d(
            r, b, -thickness
        )

        p_bot_bl = self.proyectar_3d(
            l, b, -thickness
        )

        # Laterales de la placa.
        painter.setPen(
            QPen(
                QColor("#064e3b"),
                1,
            )
        )

        painter.setBrush(
            QBrush(
                QColor("#0f3d2b")
            )
        )

        painter.drawPolygon(
            QPolygonF([
                p_top_bl,
                p_top_fl,
                p_bot_fl,
                p_bot_bl,
            ])
        )

        painter.drawPolygon(
            QPolygonF([
                p_top_fl,
                p_top_fr,
                p_bot_fr,
                p_bot_fl,
            ])
        )

        # Superficie superior.
        painter.setBrush(
            QColor("#047857")
        )

        painter.setPen(
            QPen(
                QColor("#059669"),
                1.5,
            )
        )

        painter.drawPolygon(
            QPolygonF([
                p_top_fl,
                p_top_fr,
                p_top_br,
                p_top_bl,
            ])
        )

        # Pistas.
        for (
            p1_abs,
            p2_abs,
            capa,
            color,
        ) in pistas:

            z_pos = (
                -thickness - 2
                if capa != "Top Copper"
                else 2
            )

            painter.setPen(
                QPen(
                    color,
                    4,
                )
            )

            rel1 = (
                p1_abs
                - QPointF(c_x, c_y)
            )

            rel2 = (
                p2_abs
                - QPointF(c_x, c_y)
            )

            painter.drawLine(
                self.proyectar_3d(
                    rel1.x(),
                    rel1.y(),
                    z_pos,
                ),
                self.proyectar_3d(
                    rel2.x(),
                    rel2.y(),
                    z_pos,
                ),
            )

        # Componentes.
        for (
            tipo,
            pos,
            w,
            h,
            pins,
        ) in componentes:

            pos_rel = (
                pos
                - QPointF(c_x, c_y)
            )

            # Pads.
            for pin in pins:

                pin_rel = (
                    pin
                    - QPointF(c_x, c_y)
                )

                pad_center = self.proyectar_3d(
                    pin_rel.x(),
                    pin_rel.y(),
                    1,
                )

                painter.setBrush(
                    QBrush(
                        QColor("#fbbf24")
                    )
                )

                painter.setPen(
                    Qt.NoPen
                )

                painter.drawEllipse(
                    pad_center,
                    4,
                    4,
                )

            x0 = pos_rel.x()
            y0 = pos_rel.y()

            z_height = 25

            color_cuerpo = QColor(
                "#cbd5e1"
            )

            if tipo == "Resistor":
                z_height = 10
                color_cuerpo = QColor(
                    "#d97706"
                )

            elif tipo == "LED":
                z_height = 30
                color_cuerpo = QColor(
                    "#22c55e"
                )

            elif tipo == "Capacitor":
                z_height = 35
                color_cuerpo = QColor(
                    "#0284c7"
                )

            elif tipo == "Circuito Integrado":
                z_height = 15
                color_cuerpo = QColor(
                    "#1e293b"
                )

            elif tipo == "Transistor":
                z_height = 25
                color_cuerpo = QColor(
                    "#334155"
                )

            elif tipo == "Display 7 Segmentos":
                z_height = 15
                color_cuerpo = QColor(
                    "#27272a"
                )

            elif tipo == "Conector de Placa":
                z_height = 40
                color_cuerpo = QColor(
                    "#22c55e"
                )

            c_fl = self.proyectar_3d(
                x0,
                y0,
                2,
            )

            c_fr = self.proyectar_3d(
                x0 + w,
                y0,
                2,
            )

            c_br = self.proyectar_3d(
                x0 + w,
                y0 + h,
                2,
            )

            c_bl = self.proyectar_3d(
                x0,
                y0 + h,
                2,
            )

            cz_fl = self.proyectar_3d(
                x0,
                y0,
                2 + z_height,
            )

            cz_fr = self.proyectar_3d(
                x0 + w,
                y0,
                2 + z_height,
            )

            cz_br = self.proyectar_3d(
                x0 + w,
                y0 + h,
                2 + z_height,
            )

            cz_bl = self.proyectar_3d(
                x0,
                y0 + h,
                2 + z_height,
            )

            painter.setPen(
                QPen(
                    QColor("#0f172a"),
                    1,
                )
            )

            painter.setBrush(
                QBrush(
                    color_cuerpo.darker(
                        120
                    )
                )
            )

            painter.drawPolygon(
                QPolygonF([
                    c_fl,
                    c_fr,
                    cz_fr,
                    cz_fl,
                ])
            )

            painter.setBrush(
                QBrush(
                    color_cuerpo.darker(
                        140
                    )
                )
            )

            painter.drawPolygon(
                QPolygonF([
                    c_fr,
                    c_br,
                    cz_br,
                    cz_fr,
                ])
            )

            painter.setBrush(
                QBrush(
                    color_cuerpo
                )
            )

            painter.drawPolygon(
                QPolygonF([
                    cz_fl,
                    cz_fr,
                    cz_br,
                    cz_bl,
                ])
            )

        painter.end()


# -----------------------------------------------------------------------------
# Wrapper visual del visor isométrico.
class Visor3DParentWidget(QWidget):

    def __init__(
        self,
        scene,
        parent=None
    ):
        super().__init__(parent)

        self.setObjectName(
            "Visor3DParent"
        )

        self.setStyleSheet(
            """
            #Visor3DParent {
                background-color: rgba(15, 23, 42, 0.9);
                border: 1px solid #334155;
                border-radius: 8px;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(0)

        self.visor = VisorIsometricoWidget(
            scene,
            self
        )

        layout.addWidget(
            self.visor
        )

# =============================================================================
# KlinCAD - Escena y vista interactiva
# =============================================================================

import gc

from PyQt5.QtCore import QPointF, QRectF, QLineF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPixmap
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView

from klincad.config import GRID_SIZE, SNAP_THRESHOLD, CAPAS_CONFIG
from klincad.items.component import ComponenteLiviano, BaseItemRotable
from klincad.items.track import PistaInteractiva
from klincad.items.node import Nodo
from klincad.items.markers import IndicadorConexion


# Prefijos utilizados para renumerar referencias como R1, C1, U1, etc.
PREFIJOS = {
    "Resistor": "R",
    "Capacitor": "C",
    "Inductor / Bobina": "L",
    "Diodo": "D",
    "Zener": "Z",
    "Transistor": "Q",
    "Circuito Integrado": "U",
    "LED": "D",
    "Buzzer / Zumbador": "BZ",
    "Display 7 Segmentos": "DISP",
    "Pulsador / Push Button": "SW",
    "Interruptor / Switch": "SW",
    "Batería / Pila": "BT",
    "Terminal Alimentación": "PWR",
    "Conector de Placa": "J",
    "Agujero de Montaje": "H",
}


# -----------------------------------------------------------------------------
# Escena central del editor.
# Coordina objetos PCB, conexiones, limpieza y capas.
class EscenaDotGrid(QGraphicsScene):

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)

        self.grid_size = GRID_SIZE
        self.modo_oscuro = False
        self.lang = "es"
        self.mostrar_etiquetas = True
        self.orden_capas = list(CAPAS_CONFIG.keys())

        self.crear_patron_puntos()

        self.indicadores_net = []
        self.visor_iso_ref = None

        self.changed.connect(self._avisar_cambio_visor)

    def _avisar_cambio_visor(self, *_):
        if self.visor_iso_ref is not None:
            self.visor_iso_ref.invalidar_cache_geometria()

    def eliminar_item_seguro(self, item):
        if item is None:
            return

        if isinstance(item, PistaInteractiva):
            item.liberar_recursos()

        elif item in self.indicadores_net:
            self.indicadores_net.remove(item)

            if item.scene() is self:
                super().removeItem(item)

        elif item.scene() is self:
            super().removeItem(item)

        self.update()

    def eliminar_items_seguros(self, items):
        for item in list(items):
            self.eliminar_item_seguro(item)

        self.actualizar_indicadores_conexion()
        gc.collect()

    def limpiar_escena(self):
        # Limpieza explícita de pistas/handles + clear de Qt
        # para evitar referencias stale.
        pistas = [
            i for i in self.items()
            if isinstance(i, PistaInteractiva)
        ]

        for pista in pistas:
            pista.liberar_recursos()

        self.indicadores_net.clear()

        super().clear()

        gc.collect()

        self.crear_patron_puntos()

    def crear_patron_puntos(self):
        pixmap = QPixmap(
            self.grid_size,
            self.grid_size
        )

        color_fondo = (
            QColor("#0f172a")
            if self.modo_oscuro
            else QColor("#f1f5f9")
        )

        color_punto = (
            QColor("#475569")
            if self.modo_oscuro
            else QColor("#718096")
        )

        pixmap.fill(color_fondo)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(color_punto))
        painter.setPen(Qt.NoPen)

        radio_punto = 1.25

        painter.drawEllipse(
            QPointF(0, 0),
            radio_punto,
            radio_punto
        )

        painter.end()

        self.brush_puntos = QBrush(pixmap)
        self.setBackgroundBrush(self.brush_puntos)

    def set_modo_oscuro(self, oscuro):
        self.modo_oscuro = oscuro
        self.crear_patron_puntos()

        for item in self.items():
            if isinstance(item, ComponenteLiviano):
                item.actualizar_texto_etiqueta()
                item.update()

        self.update()

    def set_idioma(self, lang):
        self.lang = lang

        for item in self.items():
            if isinstance(item, ComponenteLiviano):
                item.actualizar_tooltip()

    def buscar_terminal_cercano(self, pos, ignorar_item=None):
        rect_busqueda = QRectF(
            pos.x() - SNAP_THRESHOLD,
            pos.y() - SNAP_THRESHOLD,
            SNAP_THRESHOLD * 2,
            SNAP_THRESHOLD * 2
        )

        candidatos = self.items(rect_busqueda)

        cercano = None
        dist_min = SNAP_THRESHOLD

        for item in candidatos:
            if item == ignorar_item:
                continue

            if (
                isinstance(item, BaseItemRotable)
                and not isinstance(item, PistaInteractiva)
            ):
                for pin in item.obtener_puntos_conexion():
                    dist = QLineF(pos, pin).length()

                    if dist < dist_min:
                        dist_min = dist
                        cercano = pin

            elif isinstance(item, PistaInteractiva) and item.isVisible():
                for pin in [
                    item.mapToScene(item.line().p1()),
                    item.mapToScene(item.line().p2()),
                ]:
                    dist = QLineF(pos, pin).length()

                    if dist < dist_min:
                        dist_min = dist
                        cercano = pin

        return cercano

    def actualizar_indicadores_conexion(self):
        for ind in list(self.indicadores_net):
            if ind.scene() is self:
                super().removeItem(ind)

        self.indicadores_net.clear()

        pistas = [
            i
            for i in self.items()
            if isinstance(i, PistaInteractiva) and i.isVisible()
        ]

        for pista in pistas:
            linea = pista.line()

            for extremo in [
                pista.mapToScene(linea.p1()),
                pista.mapToScene(linea.p2()),
            ]:
                rect_busqueda = QRectF(
                    extremo.x() - 5,
                    extremo.y() - 5,
                    10,
                    10
                )

                candidatos = self.items(rect_busqueda)
                conectado = False

                for comp in candidatos:
                    if comp == pista:
                        continue

                    if isinstance(comp, (ComponenteLiviano, Nodo)):
                        if comp.contains(
                            comp.mapFromScene(extremo)
                        ):
                            conectado = True
                            break

                        for pin in comp.obtener_puntos_conexion():
                            if QLineF(extremo, pin).length() < 4.0:
                                conectado = True
                                break

                    elif (
                        isinstance(comp, PistaInteractiva)
                        and comp.isVisible()
                    ):
                        for pin in [
                            comp.mapToScene(comp.line().p1()),
                            comp.mapToScene(comp.line().p2()),
                        ]:
                            if QLineF(extremo, pin).length() < 4.0:
                                conectado = True
                                break

                    if conectado:
                        break

                if conectado:
                    ind = IndicadorConexion(
                        extremo.x(),
                        extremo.y()
                    )

                    self.addItem(ind)
                    self.indicadores_net.append(ind)

        if self.visor_iso_ref and self.visor_iso_ref.isVisible():
            self.visor_iso_ref.update()

    def renumerar_componentes(self):
        componentes = [
            i
            for i in self.items()
            if isinstance(i, ComponenteLiviano)
        ]

        componentes.sort(
            key=lambda c: (c.y(), c.x())
        )

        contadores = {}

        for comp in componentes:
            pref = PREFIJOS.get(
                comp.tipo,
                "X"
            )

            contadores[pref] = (
                contadores.get(pref, 0) + 1
            )

            comp.ref_id = (
                f"{pref} {contadores[pref]}"
            )

            comp.actualizar_texto_etiqueta()


# -----------------------------------------------------------------------------
# Vista del editor: zoom, pan y registro de acciones para undo/redo.
class VistaInteractiva(QGraphicsView):

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)

        # Al mover elementos se necesita repintar también
        # el área que queda libre.
        self.setCacheMode(QGraphicsView.CacheNone)

        self.setOptimizationFlags(
            QGraphicsView.DontSavePainterState
            | QGraphicsView.DontAdjustForAntialiasing
        )

        self.setViewportUpdateMode(
            QGraphicsView.FullViewportUpdate
        )

        self._pan_activo = False
        self._pan_inicio = None

        self.zoom_min = 0.2
        self.zoom_max = 5.0
        self.zoom_actual = 1.0

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = (
                1.15
                if event.angleDelta().y() > 0
                else (1 / 1.15)
            )

            nuevo_zoom = (
                self.zoom_actual * factor
            )

            if (
                self.zoom_min
                <= nuevo_zoom
                <= self.zoom_max
            ):
                self.zoom_actual = nuevo_zoom

                self.setTransformationAnchor(
                    QGraphicsView.AnchorUnderMouse
                )

                self.scale(
                    factor,
                    factor
                )

            event.accept()

        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._pan_activo = True
            self._pan_inicio = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()

        else:
            if (
                self.scene().selectedItems()
                and hasattr(
                    self.window(),
                    "registrar_accion_inicio"
                )
            ):
                self.window().registrar_accion_inicio()

            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan_activo:
            delta = (
                event.pos()
                - self._pan_inicio
            )

            self._pan_inicio = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value()
                - delta.x()
            )

            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value()
                - delta.y()
            )

            event.accept()

        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if (
            event.button() == Qt.RightButton
            and self._pan_activo
        ):
            self._pan_activo = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()

        else:
            if hasattr(
                self.window(),
                "registrar_accion_fin"
            ):
                self.window().registrar_accion_fin()

            super().mouseReleaseEvent(event)

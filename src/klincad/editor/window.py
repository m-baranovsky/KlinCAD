# =============================================================================
# KlinCAD - Ventana principal del editor
# =============================================================================

import json
import math
import os
import sys

from PyQt5.QtCore import (
    QEvent, QLineF, QPoint, QPointF, QRectF, QSettings, QThread, QTimer, Qt,
)
from PyQt5.QtGui import (
    QBrush, QColor, QFont, QImage, QKeySequence, QPainter, QPageSize,
    QPdfWriter, QPen, QPixmap, QTransform,
)
from PyQt5.QtWidgets import (
    QAction, QApplication, QComboBox, QFileDialog, QGraphicsItem,
    QGraphicsScene, QGraphicsView, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMenu, QMessageBox, QShortcut, QTextEdit, QToolBar,
    QToolButton, QVBoxLayout, QWidget,
)

from klincad.config import CAPAS_CONFIG
from klincad.i18n import LANG_DICT
from klincad.items.component import BaseItemRotable, ComponenteLiviano
from klincad.items.mesh import Malla
from klincad.items.node import Nodo
from klincad.items.track import PistaInteractiva
from klincad.items.markers import FlechaError, IndicadorConexion
from klincad.editor.scene import EscenaDotGrid, VistaInteractiva
from klincad.utils.geometry import snap_to_grid
from klincad.editor.drc import DRCWorker, DialogoDRC
from klincad.ui.dialogs import (
    CalculadoraDialog, GuiaDialog, PaginaPrecargaWidget, SeleccionCapaDialog, SplashDialog,
)
from klincad.ui.toolbars import OverlayContainer, PanelCapasWidget
from klincad.ui.viewer3d import Visor3DParentWidget


# Catálogo usado por el menú de componentes.
VALORES_POR_COMPONENTE = {
    "Resistor": ["100 Ω", "220 Ω", "330 Ω", "1 KΩ", "2.2 KΩ", "4.7 KΩ", "10 KΩ", "47 KΩ", "100 KΩ"],
    "Capacitor": ["10 pF", "100 pF", "1 nF", "10 nF", "100 nF", "1 uF", "10 uF", "100 uF"],
    "Inductor / Bobina": ["10 μH", "100 μH", "1 mH"],
    "Diodo": ["1N4148", "1N4001", "1N4007", "1N5819"],
    "Zener": ["Zener 3.3V", "Zener 5.1V", "Zener 9.1V", "Zener 12V"],
    "Transistor": ["BC547 (NPN genérico)", "BC557 (PNP genérico)", "2N2222", "2N3904", "MOSFET IRFZ44N"],
    "Circuito Integrado": ["NE555 (Temporizador)", "LM7805 (Regulador 5V)", "LM358 (Op-Amp)", "ATmega328P (Micro)"],
    "LED": ["LED Rojo", "LED Verde", "LED Azul", "LED Amarillo", "LED Blanco"],
    "Buzzer / Zumbador": ["Activo 5V", "Activo 12V", "Pasivo"],
    "Display 7 Segmentos": ["Cátodo Común", "Ánodo Común"],
    "Pulsador / Push Button": ["Normal Abierto (NO)"],
    "Interruptor / Switch": ["Deslizante SPDT (1 polo, 2 tiros)"],
    "Batería / Pila": ["Pila 1.5V (AA/AAA)", "Batería 9V", "Pack 5V (USB)", "Li-ion 3.7V"],
    "Terminal Alimentación": ["+5V", "+12V", "+3.3V", "GND (Tierra)"],
    "Conector de Placa": ["Clema de tornillo (2 pines)", "Pin Header macho (1x2)", "Pin Header macho (1x4)"],
    "Agujero de Montaje": ["M2.5", "M3", "M4"],
}



class EditorCircuito(QMainWindow):
    # ------------------------------------------------------------------------
    # Inicialización y ciclo de vida
    # ------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self.titulo_base = "KlinCAD - Diseña tu primer circuito a la velocidad de la luz"
        self.setWindowTitle(self.titulo_base)
        self.setGeometry(100, 100, 1100, 750)
        self.lang = "es"

        # Configuración de deshacer/rehacer y portapapeles
        self.historial_undo = []
        self.historial_redo = []
        self._historial_indice = -1
        self.estado_guardado = None
        self._estado_accion_inicio = None

        ANCHO_LIENZO = 5000
        ALTO_LIENZO = 5000
        self.scene = EscenaDotGrid(-ANCHO_LIENZO // 2, -ALTO_LIENZO // 2, ANCHO_LIENZO, ALTO_LIENZO)
        self.scene.setItemIndexMethod(QGraphicsScene.BspTreeIndex)
        
        self.view = VistaInteractiva(self.scene, self)
        self.view.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        self.view.setStyleSheet("background-color: #f1f5f9; border: none;")

        self.visor_3d_parent = Visor3DParentWidget(self.scene)
        self.scene.visor_iso_ref = self.visor_3d_parent.visor
        self.panel_capas = PanelCapasWidget(self.scene)

        self.preload_widget = PaginaPrecargaWidget(self)
        self.preload_widget.btn_nuevo.clicked.connect(self.nuevo_proyecto)
        self.preload_widget.btn_abrir.clicked.connect(self.abrir_proyecto)

        self.overlay_container = OverlayContainer(self.view, self.visor_3d_parent, self.panel_capas, self.preload_widget)
        self.setCentralWidget(self.overlay_container)

        self.modo_linea = False
        self.capa_activa = "Top Copper"
        self.puntero_inicio = None
        self.linea_temporal = None
        
        self.portapapeles = []
        self.archivo_actual = None
        self.modo_oscuro = False
        self.proyecto_activo = False

        # Preferencias persistentes de la aplicación.
        self.configuracion = QSettings("KlinCAD", "KlinCAD")
        self.mostrar_guias_inicio = self.configuracion.value(
            "interfaz/mostrar_guias_inicio", True, type=bool
        )

        self._drc_thread = None
        self._drc_worker = None
        self._drc_dialog = None
        self._drc_generation = 0
        self._shortcuts = []
        self._capa_shortcut_pendiente = False

        self.crear_barra_herramientas()
        self.actualizar_textos()
        self.view.viewport().installEventFilter(self)
        self.configurar_atajos()
        QApplication.instance().installEventFilter(self)
        
        self.aplicar_estilo_aplicacion()
        self.set_proyecto_activo(False)
        QTimer.singleShot(200, self.mostrar_aviso_inicial)

    # ------------------------------------------------------------------------
    # Atajos y selección de capas
    # ------------------------------------------------------------------------
    # Los atajos se mantienen centralizados para evitar conexiones dispersas.
    # Las combinaciones X+1..X+4 seleccionan directamente una capa de pista.
    def configurar_atajos(self):
        """
        La gestión de teclado se centraliza en eventFilter.

        Evitamos depender de QShortcut para los atajos principales porque
        así el comportamiento es uniforme entre Windows y Linux y podemos
        capturar errores sin terminar silenciosamente la aplicación.
        """
        self._shortcuts.clear()


    def _ejecutar_atajo_seguro(self, callback):
        """
        Ejecuta un atajo evitando que una excepción cierre silenciosamente
        la aplicación empaquetada.
        """
        try:
            callback()
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Error en atajo de teclado",
                f"No se pudo ejecutar la acción solicitada.\n\n"
                f"{type(exc).__name__}: {exc}"
            )

    # Cambia la capa activa y deja la herramienta Pista preparada para dibujar.
    def seleccionar_capa(self, nombre_capa):
        if not self.proyecto_activo or nombre_capa not in CAPAS_CONFIG:
            return
        self.capa_activa = nombre_capa
        self.modo_linea = True
        self.btn_puntero.setChecked(False)
        self.btn_wire.setChecked(True)
        self.view.setCursor(Qt.CrossCursor)
        self.view.setDragMode(QGraphicsView.NoDrag)

    # Abre el mismo menú que utiliza el botón de Componentes; así el teclado
    # y la interfaz gráfica comparten una única fuente de verdad.
    def mostrar_menu_componentes_atajo(self):
        if not self.proyecto_activo:
            return
        self.action_btn_componentes.setFocus(Qt.ShortcutFocusReason)
        self.action_btn_componentes.showMenu()

    # ------------------------------------------------------------------------
    # Historial / Undo / Redo y serialización
    # ------------------------------------------------------------------------
    # Capturamos el snapshot ANTES de una edición interactiva. Esto es clave para
    # que Ctrl+Z vuelva a la posición exacta, sin aplicar offsets acumulativos.
    def registrar_accion_inicio(self):
        """Marca el inicio de una edición interactiva sin duplicar estados."""
        if not self.proyecto_activo:
            self._estado_accion_inicio = None
            return
        self._estado_accion_inicio = self.serializar_escena()

    # El estado final solo se incorpora al historial si realmente cambió.
    def registrar_accion_fin(self):
        """Registra solamente el estado final si hubo una modificación real."""
        if not self.proyecto_activo:
            self._estado_accion_inicio = None
            return

        estado_final = self.serializar_escena()
        estado_inicio = self._estado_accion_inicio
        self._estado_accion_inicio = None

        if estado_inicio is None or estado_inicio != estado_final:
            self.guardar_estado(estado_final)

    # El historial almacena snapshots serializados, no referencias a QGraphicsItem.
    def guardar_estado(self, estado=None):
        """Añade un snapshot único y elimina la rama posterior de rehacer."""
        if not self.proyecto_activo:
            return

        if estado is None:
            estado = self.serializar_escena()

        if (
            0 <= self._historial_indice < len(self.historial_undo)
            and self.historial_undo[self._historial_indice] == estado
        ):
            return

        if self._historial_indice < len(self.historial_undo) - 1:
            del self.historial_undo[self._historial_indice + 1:]

        self.historial_undo.append(estado)
        self._historial_indice = len(self.historial_undo) - 1
        self.historial_redo.clear()

    # La serialización usa coordenadas absolutas de escena. Estas coordenadas son
    # la fuente de verdad para guardar, deshacer/rehacer y reabrir proyectos.
    def serializar_escena(self):
        data = {
            "version": "1.0",
            "layer_config": self.scene.orden_capas,
            "components": [],
            "tracks": [],
            "nodes": [],
            "meshes": []
        }
        for item in self.scene.items():
            if isinstance(item, ComponenteLiviano):
                data["components"].append({
                    "type": item.tipo, "value": item.valor, "ref_id": item.ref_id,
                    "x": item.scenePos().x(), "y": item.scenePos().y(), "rotation": item.rotation()
                })
            elif isinstance(item, PistaInteractiva):
                line = item.line()
                p1 = item.mapToScene(line.p1())
                p2 = item.mapToScene(line.p2())
                data["tracks"].append({
                    "layer": item.capa, "x1": p1.x(), "y1": p1.y(),
                    "x2": p2.x(), "y2": p2.y()
                })
            elif isinstance(item, Nodo):
                data["nodes"].append({"x": item.scenePos().x(), "y": item.scenePos().y(), "rotation": item.rotation()})
            elif isinstance(item, Malla):
                data["meshes"].append({"x": item.scenePos().x(), "y": item.scenePos().y(), "rotation": item.rotation()})

        # Orden determinista: la escena puede devolver items en distinto orden
        # después de reconstruirse, pero el snapshot debe representar exactamente
        # la misma geometría para que undo/redo no genere estados fantasma.
        data["components"].sort(key=lambda d: (d["ref_id"], d["type"], d["value"], d["x"], d["y"], d["rotation"]))
        data["tracks"].sort(key=lambda d: (d["layer"], d["x1"], d["y1"], d["x2"], d["y2"]))
        data["nodes"].sort(key=lambda d: (d["x"], d["y"], d["rotation"]))
        data["meshes"].sort(key=lambda d: (d["x"], d["y"], d["rotation"]))

        return json.dumps(data, ensure_ascii=False, sort_keys=True)

    # Reconstruye la escena desde datos puros. No debe introducir desplazamientos
    # implícitos ni aplicar snap adicional durante la restauración.
    def cargar_estado(self, estado_str):
        data = json.loads(estado_str)
        self.limpiar_marcas_drc()
        self.scene.limpiar_escena()
        
        for comp_data in data.get("components", []):
            item = ComponenteLiviano(comp_data["x"], comp_data["y"], comp_data["type"], comp_data["value"], comp_data.get("ref_id", ""))
            self.scene.addItem(item)
            item.setPos(QPointF(comp_data["x"], comp_data["y"]))
            item.setRotation(comp_data.get("rotation", 0))
            
        for track_data in data.get("tracks", []):
            item = PistaInteractiva(track_data["x1"], track_data["y1"], track_data["x2"], track_data["y2"], track_data.get("layer", "Top Copper"))
            self.scene.addItem(item)
            
        for node_data in data.get("nodes", []):
            item = Nodo(node_data["x"], node_data["y"])
            self.scene.addItem(item)
            item.setPos(QPointF(node_data["x"], node_data["y"]))
            item.setRotation(node_data.get("rotation", 0))
            
        for mesh_data in data.get("meshes", []):
            item = Malla(mesh_data["x"], mesh_data["y"])
            self.scene.addItem(item)
            item.setPos(QPointF(mesh_data["x"], mesh_data["y"]))
            item.setRotation(mesh_data.get("rotation", 0))
            
        self.scene.orden_capas = data.get("layer_config", list(CAPAS_CONFIG.keys()))
        self.panel_capas.orden_capas = self.scene.orden_capas
        self.panel_capas.reconstruir_ui()
        # No renumerar aquí: undo/redo debe restaurar exactamente el estado guardado.
        for item in self.scene.items():
            if isinstance(item, ComponenteLiviano):
                item.actualizar_texto_etiqueta()
        self.scene.actualizar_indicadores_conexion()

    # Navega hacia atrás en la pila de snapshots. Restaurar un snapshot no crea
    # una nueva entrada de historial.
    def deshacer(self):
        """Retrocede exactamente un snapshot sin introducir offsets."""
        if not self.proyecto_activo:
            return
        if self._historial_indice <= 0:
            return
        self._historial_indice -= 1
        self._estado_accion_inicio = None
        self.cargar_estado(self.historial_undo[self._historial_indice])

    # Navega hacia adelante usando la pila redo.
    def rehacer(self):
        """Avanza exactamente un snapshot."""
        if not self.proyecto_activo:
            return
        if self._historial_indice >= len(self.historial_undo) - 1:
            return
        self._historial_indice += 1
        self._estado_accion_inicio = None
        self.cargar_estado(self.historial_undo[self._historial_indice])

    # ------------------------------------------------------------------------
    # Portapapeles y edición
    # ------------------------------------------------------------------------
    def _serializar_items(self, items):
        datos = []
        for item in items:
            if isinstance(item, ComponenteLiviano):
                datos.append({
                    "kind": "component", "type": item.tipo, "value": item.valor,
                    "ref_id": item.ref_id, "x": item.scenePos().x(), "y": item.scenePos().y(),
                    "rotation": item.rotation()
                })
            elif isinstance(item, PistaInteractiva):
                line = item.line()
                p1 = item.mapToScene(line.p1())
                p2 = item.mapToScene(line.p2())
                datos.append({
                    "kind": "track", "layer": item.capa,
                    "x1": p1.x(), "y1": p1.y(), "x2": p2.x(), "y2": p2.y()
                })
            elif isinstance(item, Nodo):
                datos.append({"kind": "node", "x": item.scenePos().x(), "y": item.scenePos().y(), "rotation": item.rotation()})
            elif isinstance(item, Malla):
                datos.append({"kind": "mesh", "x": item.scenePos().x(), "y": item.scenePos().y(), "rotation": item.rotation()})
        return datos

    def copiar_seleccion(self):
        if not self.proyecto_activo:
            return
        items = [i for i in self.scene.selectedItems()
                 if isinstance(i, (ComponenteLiviano, PistaInteractiva, Nodo, Malla))]
        if not items:
            return
        self.portapapeles = self._serializar_items(items)
        QApplication.clipboard().setText(json.dumps({"klincad_clipboard": self.portapapeles}, ensure_ascii=False))

    def pegar_seleccion(self):
        if not self.proyecto_activo:
            return
        if not self.portapapeles:
            try:
                data_portapapeles = json.loads(QApplication.clipboard().text())
                self.portapapeles = data_portapapeles.get("klincad_clipboard", [])
            except (TypeError, json.JSONDecodeError):
                self.portapapeles = []
        if not self.portapapeles:
            return
        # Pegar conserva exactamente las coordenadas absolutas copiadas.
        # No se aplica offset acumulativo, por lo que Ctrl+X/Ctrl+V restaura
        # el objeto en el mismo lugar donde estaba antes de cortar.
        self.scene.clearSelection()
        nuevos = []
        for data in self.portapapeles:
            kind = data["kind"]
            if kind == "component":
                item = ComponenteLiviano(
                    data["x"],
                    data["y"],
                    data["type"],
                    data["value"],
                    data.get("ref_id", "")
                )
                self.scene.addItem(item)
                item.setPos(QPointF(data["x"], data["y"]))
                item.setRotation(data.get("rotation", 0))
            elif kind == "track":
                item = PistaInteractiva(
                    data["x1"],
                    data["y1"],
                    data["x2"],
                    data["y2"],
                    data.get("layer", "Top Copper")
                )
                self.scene.addItem(item)
            elif kind == "node":
                item = Nodo(data["x"], data["y"])
                self.scene.addItem(item)
                item.setPos(QPointF(data["x"], data["y"]))
                item.setRotation(data.get("rotation", 0))
            elif kind == "mesh":
                item = Malla(data["x"], data["y"])
                self.scene.addItem(item)
                item.setPos(QPointF(data["x"], data["y"]))
                item.setRotation(data.get("rotation", 0))
            else:
                continue
            item.setSelected(True)
            nuevos.append(item)
        self.scene.renumerar_componentes()
        self.scene.actualizar_indicadores_conexion()
        if nuevos:
            self.guardar_estado()

    def cortar_seleccion(self):
        if not self.proyecto_activo or not self.scene.selectedItems():
            return
        self.copiar_seleccion()
        self.eliminar_seleccion()

    def eliminar_seleccion(self):
        items = [i for i in self.scene.selectedItems()
                 if isinstance(i, (ComponenteLiviano, PistaInteractiva, Nodo, Malla, FlechaError))]
        if not items:
            return
        self.scene.eliminar_items_seguros(items)
        self.scene.renumerar_componentes()
        self.guardar_estado()

    def rotar_seleccion(self):
        items = self.scene.selectedItems()
        modificado = False

        for item in items:
            if isinstance(item, PistaInteractiva):
                item.rotar_geometria(1.0)
                modificado = True
                continue

            if isinstance(item, BaseItemRotable):
                item.setTransformOriginPoint(
                    item.boundingRect().center()
                )
                item.setRotation(
                    item.rotation() + 1.0
                )
                modificado = True

        if modificado:
            self.scene.actualizar_indicadores_conexion()
            self.guardar_estado()

    # ------------------------------------------------------------------------
    # Eventos de interacción
    # ------------------------------------------------------------------------
    # Punto central para atajos/secuencias que no son fiables como QShortcut,
    # especialmente X+1..X+4. Mantener aquí la lógica evita conflictos de foco.
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            foco = QApplication.focusWidget()

            # No interceptar teclas mientras se escribe en un control de texto.
            es_editor_texto = isinstance(
                foco,
                (QLineEdit, QTextEdit, QComboBox)
            )

            # No capturar teclas mientras haya un diálogo modal abierto.
            ventana_modal = QApplication.activeModalWidget()
            if ventana_modal is not None and ventana_modal is not self:
                return super().eventFilter(obj, event)

            # ============================================================
            # ATAJOS Ctrl + tecla
            # ============================================================

            if not es_editor_texto and modifiers == Qt.ControlModifier:
                atajos_ctrl = {
                    Qt.Key_C: self.copiar_seleccion,
                    Qt.Key_V: self.pegar_seleccion,
                    Qt.Key_X: self.cortar_seleccion,
                    Qt.Key_Z: self.deshacer,
                    Qt.Key_Y: self.rehacer,
                    Qt.Key_S: self.guardar_proyecto,
                }

                callback = atajos_ctrl.get(key)

                if callback is not None:
                    self._ejecutar_atajo_seguro(callback)
                    event.accept()
                    return True

            # ============================================================
            # ATAJOS DE UNA SOLA TECLA
            # ============================================================

            if not es_editor_texto and modifiers == Qt.NoModifier:
                atajos_directos = {
                    Qt.Key_R: self.rotar_seleccion,
                    Qt.Key_Escape: self.set_modo_puntero,
                    Qt.Key_Delete: self.eliminar_seleccion,
                    Qt.Key_Backspace: self.eliminar_seleccion,
                    Qt.Key_A: self.mostrar_menu_componentes_atajo,
                }

                callback = atajos_directos.get(key)

                if callback is not None:
                    self._ejecutar_atajo_seguro(callback)
                    event.accept()
                    return True

            # ============================================================
            # X + 1..4 PARA SELECCIÓN DE CAPA
            # ============================================================

            if (
                self.proyecto_activo
                and not es_editor_texto
                and modifiers == Qt.NoModifier
                and key == Qt.Key_X
            ):
                self._capa_shortcut_pendiente = True
                event.accept()
                return True

            if (
                getattr(self, "_capa_shortcut_pendiente", False)
                and modifiers == Qt.NoModifier
                and key in (
                    Qt.Key_1,
                    Qt.Key_2,
                    Qt.Key_3,
                    Qt.Key_4,
                )
            ):
                capas = {
                    Qt.Key_1: "Top Copper",
                    Qt.Key_2: "Bottom Copper",
                    Qt.Key_3: "General / Jumpers",
                    Qt.Key_4: "Power / Notes",
                }

                self._capa_shortcut_pendiente = False

                self._ejecutar_atajo_seguro(
                    lambda: self.seleccionar_capa(capas[key])
                )

                event.accept()
                return True

            # Una tecla distinta rompe la secuencia X + número.
            if getattr(self, "_capa_shortcut_pendiente", False):
                self._capa_shortcut_pendiente = False

        # Lógica existente de dibujo de pistas.
        if obj == self.view.viewport():
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if self.modo_linea:
                    self.registrar_accion_inicio()
                    pos = self.view.mapToScene(event.pos())
                    snapped_pos = snap_to_grid(pos)
                    cercano = self.scene.buscar_terminal_cercano(snapped_pos)
                    start_pos = cercano if cercano else snapped_pos
                    self.puntero_inicio = start_pos

                    self.linea_temporal = PistaInteractiva(
                        start_pos.x(),
                        start_pos.y(),
                        start_pos.x(),
                        start_pos.y(),
                        self.capa_activa
                    )

                    self.scene.addItem(self.linea_temporal)
                    return True

            elif event.type() == QEvent.MouseMove and self.modo_linea and self.linea_temporal:
                pos = self.view.mapToScene(event.pos())
                snapped_pos = snap_to_grid(pos)

                cercano = self.scene.buscar_terminal_cercano(
                    snapped_pos,
                    ignorar_item=self.linea_temporal
                )

                end_pos = cercano if cercano else snapped_pos
                linea = self.linea_temporal.line()
                linea.setP2(end_pos)
                self.linea_temporal.setLine(linea)

                return True

            elif event.type() == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if self.modo_linea and self.linea_temporal:
                    if self.linea_temporal.line().p1() == self.linea_temporal.line().p2():
                        self.scene.eliminar_item_seguro(self.linea_temporal)
                    else:
                        self.linea_temporal.actualizar_posicion_handles()
                        self.scene.actualizar_indicadores_conexion()

                    self.linea_temporal = None
                    self.puntero_inicio = None
                    self.registrar_accion_fin()

                    return True

        return super().eventFilter(obj, event)

    # ------------------------------------------------------------------------
    # Interfaz y apariencia
    # ------------------------------------------------------------------------
    def actualizar_textos(self):
        t = LANG_DICT[self.lang]
        self.btn_proyecto.setText(t["menu_project"])
        self.btn_utilidades.setText(t["menu_utils"])
        
        if hasattr(self, 'btn_ayuda'):
            self.btn_ayuda.setText(t["menu_help"])
            self.accion_comunidad.setText(t["community"])
            
        self.accion_nuevo.setText(t["new_proj"])
        self.accion_abrir.setText(t["open_proj"])
        self.accion_guardar.setText(t["save_proj"])
        self.accion_bom.setText(t["bom"])
        self.accion_drc.setText(t["drc"])
        self.accion_visor_3d.setText(t["visor"])
        self.accion_panel_capas.setText(t["layers"])
        self.accion_etiquetas.setText(t["labels"])
        self.accion_modo_oscuro.setText(t["dark"])
        self.accion_exportar_png.setText(t["exp_png"])
        self.accion_exportar_pdf.setText(t["exp_pdf"])
        self.accion_aviso.setText(t["start"])
        self.accion_toggle_guias.setText(t["guide_toggle"])
        self.accion_cambio_idioma.setText(t["lang_toggle"])
        self.accion_calc.setText(t["calc"])
        
        self.btn_puntero.setText(t["pointer"])
        self.btn_wire.setText(t["track"])
        self.action_btn_componentes.setText(t["components"])

        traducciones_componentes = {
            "es": {
                "Resistor": "Resistor",
                "Capacitor": "Capacitor",
                "Inductor / Bobina": "Inductor / Bobina",
                "Diodo": "Diodo",
                "Zener": "Zener",
                "Transistor": "Transistor",
                "Circuito Integrado": "Circuito Integrado",
                "LED": "LED",
                "Buzzer / Zumbador": "Buzzer / Zumbador",
                "Display 7 Segmentos": "Display de 7 Segmentos",
                "Pulsador / Push Button": "Pulsador",
                "Interruptor / Switch": "Interruptor",
                "Batería / Pila": "Batería / Pila",
                "Terminal Alimentación": "Terminal de Alimentación",
                "Conector de Placa": "Conector de Placa",
                "Agujero de Montaje": "Agujero de Montaje",
            },
            "en": {
                "Resistor": "Resistor",
                "Capacitor": "Capacitor",
                "Inductor / Bobina": "Inductor / Coil",
                "Diodo": "Diode",
                "Zener": "Zener",
                "Transistor": "Transistor",
                "Circuito Integrado": "Integrated Circuit",
                "LED": "LED",
                "Buzzer / Zumbador": "Buzzer",
                "Display 7 Segmentos": "7-Segment Display",
                "Pulsador / Push Button": "Push Button",
                "Interruptor / Switch": "Switch",
                "Batería / Pila": "Battery",
                "Terminal Alimentación": "Power Terminal",
                "Conector de Placa": "Board Connector",
                "Agujero de Montaje": "Mounting Hole",
            },
        }

        for cat, submenu in self._menus_componentes.items():
            submenu.setTitle(
                traducciones_componentes[self.lang].get(cat, cat)
            )

        self.accion_nodo.setText(t["node"])
        self.accion_malla.setText(t["mesh"])
        
        self.accion_nodo.setText(t["node"])
        self.accion_malla.setText(t["mesh"])
        
        self.preload_widget.actualizar_idioma(self.lang)
        self.scene.set_idioma(self.lang)

    def aplicar_estilo_aplicacion(self):
        if self.modo_oscuro:
            self.setStyleSheet("""
                QMainWindow, QToolBar { background: #0b1220; color: #f8fafc; border: 0; }
                QToolButton { color: #f8fafc; background: #111827; border: 1px solid #334155; padding: 6px 10px; }
                QToolButton:hover { background: #1e293b; }
                QMenu { background: #111827; color: #f8fafc; border: 1px solid #334155; }
                QMenu::item { padding: 7px 24px; }
                QMenu::item:selected { background: #1d4ed8; }
                QMenu::item:disabled { color: #64748b; }
                QScrollBar:vertical, QScrollBar:horizontal { background: #0f172a; border: none; }
                QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #334155; border-radius: 4px; min-height: 20px; min-width: 20px; }
                QScrollBar::add-line, QScrollBar::sub-line { background: #0f172a; }
                QToolTip { color: #f8fafc; background: #0f172a; border: 1px solid #38bdf8; padding: 4px; }
            """)
            self.view.setStyleSheet("background-color: #0f172a; border: none;")
        else:
            self.setStyleSheet("""
                QMainWindow, QToolBar { background: #f8fafc; color: #0f172a; border: 0; }
                QToolButton { color: #0f172a; background: #ffffff; border: 1px solid #cbd5e1; padding: 6px 10px; }
                QToolButton:hover { background: #e2e8f0; }
                QMenu { background: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; }
                QMenu::item { padding: 7px 24px; }
                QMenu::item:selected { background: #dbeafe; }
                QMenu::item:disabled { color: #94a3b8; }
                QScrollBar:vertical, QScrollBar:horizontal { background: #e2e8f0; border: none; }
                QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #94a3b8; border-radius: 4px; min-height: 20px; min-width: 20px; }
                QToolTip { color: #000000; background: #ffffff; border: 1px solid #0284c7; padding: 4px; }
            """)
            self.view.setStyleSheet("background-color: #f1f5f9; border: none;")

    # Esta bandera controla qué partes de la UI son utilizables antes/después de
    # crear o abrir un proyecto. Nuevo/Abrir permanecen disponibles en la portada.
    def set_proyecto_activo(self, activo):
        self.proyecto_activo = activo

        acciones_bloqueadas = (
            self.accion_guardar,
            self.accion_bom,
            self.accion_drc,
            self.accion_visor_3d,
            self.accion_panel_capas,
            self.accion_etiquetas,
            self.accion_toggle_guias,
            self.accion_exportar_png,
            self.accion_exportar_pdf,
        )

        # Proyecto / Ayuda / Utilidades siguen accesibles desde el inicio.
        self.btn_proyecto.setEnabled(True)
        self.btn_utilidades.setEnabled(True)
        self.btn_ayuda.setEnabled(True)
        self.accion_nuevo.setEnabled(True)
        self.accion_abrir.setEnabled(True)
        self.accion_modo_oscuro.setEnabled(True)
        self.accion_cambio_idioma.setEnabled(True)
        self.accion_calc.setEnabled(True)
        self.accion_comunidad.setEnabled(True)
        self.accion_aviso.setEnabled(True)

        # Solo se bloquean herramientas que dependen de un proyecto cargado.
        controles_edicion = (
            self.btn_puntero,
            self.btn_wire,
            self.action_btn_componentes,
            self.accion_calc,
            self.accion_nodo,
            self.accion_malla,
        )

        for control in controles_edicion:
            control.setEnabled(bool(activo))

        if activo:
            self.preload_widget.hide()
            for widget in (
                self.btn_puntero,
                self.btn_wire,
                self.action_btn_componentes,
                self.sep_edicion,
                self.sep_componentes,
            ):
                widget.setVisible(True)

            for accion in acciones_bloqueadas:
                accion.setEnabled(True)

            self.accion_calc.setEnabled(True)
            self.accion_nodo.setEnabled(True)
            self.accion_malla.setEnabled(True)

            if self.accion_visor_3d.isChecked():
                self.visor_3d_parent.show()
            if self.accion_panel_capas.isChecked():
                self.panel_capas.show()
            if self.mostrar_guias_inicio:
                GuiaDialog(self, lang=self.lang).exec_()
            self.guardar_estado()
        else:
            self.preload_widget.show()
            self.preload_widget.raise_()
            self.overlay_container.watermark.raise_()

            for widget in (
                self.btn_puntero,
                self.btn_wire,
                self.action_btn_componentes,
                self.sep_edicion,
                self.sep_componentes,
            ):
                widget.setVisible(False)

            for accion in acciones_bloqueadas:
                accion.setEnabled(False)

            self.accion_calc.setEnabled(False)
            self.accion_nodo.setEnabled(False)
            self.accion_malla.setEnabled(False)

            # Estas acciones siguen deliberadamente habilitadas durante el inicio.
            self.accion_nuevo.setEnabled(True)
            self.accion_abrir.setEnabled(True)
            self.accion_modo_oscuro.setEnabled(True)
            self.accion_cambio_idioma.setEnabled(True)
            self.accion_comunidad.setEnabled(True)
            self.accion_aviso.setEnabled(True)

            self.visor_3d_parent.hide()
            self.panel_capas.hide()

    def mostrar_aviso_inicial(self):
        dlg = SplashDialog(self)
        dlg.exec_()

    def toggle_lang(self):
        self.lang = "en" if self.lang == "es" else "es"
        self.actualizar_textos()

    def toggle_guias_inicio(self, checked):
        self.mostrar_guias_inicio = bool(checked)
        self.configuracion.setValue(
            "interfaz/mostrar_guias_inicio", self.mostrar_guias_inicio
        )
        self.configuracion.sync()

    # ------------------------------------------------------------------------
    # Herramientas y menús
    # ------------------------------------------------------------------------
    # Toda la barra se construye aquí, pero las acciones dependientes del proyecto
    # se habilitan/deshabilitan desde set_proyecto_activo().
    def crear_barra_herramientas(self):
        tb = QToolBar("Herramientas")
        self.barra_herramientas = tb
        self.addToolBar(tb)
        estilo_sin_flecha = "QToolButton::menu-indicator { image: none; width: 0px; }"

        # 1) Proyecto
        self.btn_proyecto = QToolButton(self)
        self.btn_proyecto.setPopupMode(QToolButton.InstantPopup)
        self.btn_proyecto.setStyleSheet(estilo_sin_flecha)
        menu_proyecto = QMenu(self)

        self.accion_nuevo = QAction(self, triggered=self.nuevo_proyecto)
        self.accion_abrir = QAction(self, triggered=self.abrir_proyecto)
        self.accion_guardar = QAction(self, triggered=self.guardar_proyecto)
        menu_proyecto.addAction(self.accion_nuevo)
        menu_proyecto.addAction(self.accion_abrir)
        menu_proyecto.addAction(self.accion_guardar)
        menu_proyecto.addSeparator()

        self.accion_bom = QAction(self, triggered=self.mostrar_bom)
        self.accion_drc = QAction(self, triggered=self.ejecutar_drc)
        menu_proyecto.addAction(self.accion_bom)
        menu_proyecto.addAction(self.accion_drc)
        menu_proyecto.addSeparator()

        self.accion_visor_3d = QAction(self, checkable=True)
        self.accion_visor_3d.setChecked(True)
        self.accion_visor_3d.toggled.connect(self.visor_3d_parent.setVisible)
        menu_proyecto.addAction(self.accion_visor_3d)

        self.accion_panel_capas = QAction(self, checkable=True)
        self.accion_panel_capas.setChecked(True)
        self.accion_panel_capas.toggled.connect(self.panel_capas.setVisible)
        menu_proyecto.addAction(self.accion_panel_capas)

        self.accion_etiquetas = QAction(self, checkable=True)
        self.accion_etiquetas.setChecked(True)
        self.accion_etiquetas.toggled.connect(self.toggle_etiquetas)
        menu_proyecto.addAction(self.accion_etiquetas)

        self.accion_modo_oscuro = QAction(
            self,
            checkable=True,
            triggered=self.toggle_modo_oscuro
        )
        menu_proyecto.addAction(self.accion_modo_oscuro)
        menu_proyecto.addSeparator()

        self.accion_toggle_guias = QAction(
            self,
            checkable=True,
            triggered=self.toggle_guias_inicio
        )
        self.accion_toggle_guias.setChecked(self.mostrar_guias_inicio)
        menu_proyecto.addAction(self.accion_toggle_guias)

        self.accion_cambio_idioma = QAction(
            self,
            triggered=self.toggle_lang
        )
        menu_proyecto.addAction(self.accion_cambio_idioma)
        menu_proyecto.addSeparator()

        self.accion_exportar_png = QAction(self, triggered=self.exportar_png)
        self.accion_exportar_pdf = QAction(self, triggered=self.exportar_pdf)
        menu_proyecto.addAction(self.accion_exportar_png)
        menu_proyecto.addAction(self.accion_exportar_pdf)

        self.btn_proyecto.setMenu(menu_proyecto)
        tb.addWidget(self.btn_proyecto)

        # 2) Ayuda: queda inmediatamente al lado de Proyecto y accesible al inicio.
        self.btn_ayuda = QToolButton(self)
        self.btn_ayuda.setPopupMode(QToolButton.InstantPopup)
        self.btn_ayuda.setStyleSheet(estilo_sin_flecha)

        menu_ayuda = QMenu(self)
        self.accion_comunidad = QAction(self, triggered=self.mostrar_ayuda)
        self.accion_aviso = QAction(self, triggered=self.mostrar_aviso_inicial)
        menu_ayuda.addAction(self.accion_comunidad)
        menu_ayuda.addAction(self.accion_aviso)
        self.btn_ayuda.setMenu(menu_ayuda)
        tb.addWidget(self.btn_ayuda)

        # 3) Utilidades: ocupa ahora el lugar que antes tenía Ayuda.
        self.btn_utilidades = QToolButton(self)
        self.btn_utilidades.setPopupMode(QToolButton.InstantPopup)
        self.btn_utilidades.setStyleSheet(estilo_sin_flecha)

        menu_utilidades = QMenu(self)
        self.accion_calc = QAction(self, triggered=self.abrir_calculadora)
        menu_utilidades.addAction(self.accion_calc)
        self.btn_utilidades.setMenu(menu_utilidades)
        tb.addWidget(self.btn_utilidades)

        self.sep_edicion = tb.addSeparator()

        self.btn_puntero = QToolButton(self)
        self.btn_puntero.setCheckable(True)
        self.btn_puntero.setChecked(True)
        self.btn_puntero.clicked.connect(self.set_modo_puntero)
        tb.addWidget(self.btn_puntero)

        self.btn_wire = QToolButton(self)
        self.btn_wire.setCheckable(True)
        self.btn_wire.clicked.connect(self.set_modo_pista)
        tb.addWidget(self.btn_wire)

        self.sep_componentes = tb.addSeparator()
        self.action_btn_componentes = QToolButton(self)
        self.action_btn_componentes.setPopupMode(QToolButton.InstantPopup)
        self.action_btn_componentes.setStyleSheet(estilo_sin_flecha)

        self.menu_componentes = QMenu(self)

        traducciones_componentes = {
            "es": {
                "Resistor": "Resistor",
                "Capacitor": "Capacitor",
                "Inductor / Bobina": "Inductor / Bobina",
                "Diodo": "Diodo",
                "Zener": "Zener",
                "Transistor": "Transistor",
                "Circuito Integrado": "Circuito Integrado",
                "LED": "LED",
                "Buzzer / Zumbador": "Buzzer / Zumbador",
                "Display 7 Segmentos": "Display de 7 Segmentos",
                "Pulsador / Push Button": "Pulsador",
                "Interruptor / Switch": "Interruptor",
                "Batería / Pila": "Batería / Pila",
                "Terminal Alimentación": "Terminal de Alimentación",
                "Conector de Placa": "Conector de Placa",
                "Agujero de Montaje": "Agujero de Montaje",
            },
            "en": {
                "Resistor": "Resistor",
                "Capacitor": "Capacitor",
                "Inductor / Bobina": "Inductor / Coil",
                "Diodo": "Diode",
                "Zener": "Zener",
                "Transistor": "Transistor",
                "Circuito Integrado": "Integrated Circuit",
                "LED": "LED",
                "Buzzer / Zumbador": "Buzzer",
                "Display 7 Segmentos": "7-Segment Display",
                "Pulsador / Push Button": "Push Button",
                "Interruptor / Switch": "Switch",
                "Batería / Pila": "Battery",
                "Terminal Alimentación": "Power Terminal",
                "Conector de Placa": "Board Connector",
                "Agujero de Montaje": "Mounting Hole",
            },
        }

        self._menus_componentes = {}

        for cat, valores in VALORES_POR_COMPONENTE.items():
            texto_cat = traducciones_componentes[self.lang].get(cat, cat)

            sub = QMenu(texto_cat, self)

            for v in valores:
                accion = QAction(v, self)
                accion.triggered.connect(
                    lambda checked, c=cat, val=v:
                    self.agregar_componente(c, val)
                )
                sub.addAction(accion)

            self.menu_componentes.addMenu(sub)
            self._menus_componentes[cat] = sub

        self.menu_componentes.addSeparator()

        self.accion_nodo = QAction(self)
        self.accion_nodo.triggered.connect(self.agregar_nodo)

        self.accion_malla = QAction(self)
        self.accion_malla.triggered.connect(self.agregar_malla)

        self.menu_componentes.addAction(self.accion_nodo)
        self.menu_componentes.addAction(self.accion_malla)

        self.action_btn_componentes.setMenu(self.menu_componentes)
        tb.addWidget(self.action_btn_componentes)

    def set_modo_pista(self):
        if not self.proyecto_activo:
            return
        dlg = SeleccionCapaDialog(self.capa_activa, self)
        if dlg.exec_():
            self.capa_activa = dlg.obtener_capa()
            self.modo_linea = True
            self.btn_puntero.setChecked(False)
            self.btn_wire.setChecked(True)
            self.view.setCursor(Qt.CrossCursor)
            self.view.setDragMode(QGraphicsView.NoDrag)

    def set_modo_puntero(self):
        self.modo_linea = False
        self.btn_puntero.setChecked(True)
        self.btn_wire.setChecked(False)
        self.view.setCursor(Qt.ArrowCursor)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
        if self.linea_temporal:
            self.scene.removeItem(self.linea_temporal)
            self.linea_temporal = None
            self.puntero_inicio = None

    # ------------------------------------------------------------------------
    # Gestión de proyectos y entidades
    # ------------------------------------------------------------------------
    # Crea un documento vacío y reinicia el historial; después habilita la edición.
    def nuevo_proyecto(self):
        self.limpiar_marcas_drc()
        self.scene.limpiar_escena()
        self.archivo_actual = None
        self.historial_undo.clear()
        self.historial_redo.clear()
        self._historial_indice = -1
        self._estado_accion_inicio = None
        self.set_proyecto_activo(True)

    # El formato .klincad es JSON legible para facilitar depuración y colaboración.
    def guardar_proyecto(self):
        if not self.proyecto_activo:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Guardar Proyecto KlinCAD", "", "KlinCAD Project (*.klincad);;JSON (*.json)")
        if not path: return
        
        if not path.endswith('.klincad') and not path.endswith('.json'):
            path += '.klincad'
            
        try:
            data = json.loads(self.serializar_escena())
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.archivo_actual = path
            QMessageBox.information(self, "Guardado", "Proyecto guardado con éxito.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"Hubo un error al guardar el archivo:\n{str(e)}")

    # Carga datos JSON y solo activa el proyecto cuando toda la reconstrucción termina.
    def abrir_proyecto(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Proyecto KlinCAD", "", "KlinCAD Project (*.klincad);;JSON (*.json)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.cargar_estado(json.dumps(data))
            
            self.archivo_actual = path
            self.historial_undo.clear()
            self.historial_redo.clear()
            self._historial_indice = -1
            self._estado_accion_inicio = None
            self.set_proyecto_activo(True)
            QMessageBox.information(self, "Abierto", "Proyecto abierto con éxito.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Abrir", f"Hubo un error al abrir el archivo:\n{str(e)}")

    def agregar_componente(self, categoria, valor):
        centro = self.view.mapToScene(self.view.viewport().rect().center())
        comp = ComponenteLiviano(centro.x(), centro.y(), categoria, valor)
        self.scene.addItem(comp)
        self.scene.renumerar_componentes()
        self.guardar_estado()
        self.set_modo_puntero()

    def agregar_nodo(self):
        centro = self.view.mapToScene(self.view.viewport().rect().center())
        nodo = Nodo(centro.x(), centro.y())
        self.scene.addItem(nodo)
        self.guardar_estado()
        self.set_modo_puntero()

    def agregar_malla(self):
        centro = self.view.mapToScene(self.view.viewport().rect().center())
        malla = Malla(centro.x(), centro.y())
        self.scene.addItem(malla)
        self.guardar_estado()
        self.set_modo_puntero()

    def toggle_etiquetas(self, checked):
        self.scene.mostrar_etiquetas = checked
        for item in self.scene.items():
            if isinstance(item, ComponenteLiviano):
                item.label.setVisible(checked)
                for lbl in item.pin_labels:
                    lbl.setVisible(checked)

    def toggle_modo_oscuro(self, checked):
        self.modo_oscuro = checked
        self.scene.set_modo_oscuro(checked)
        self.aplicar_estilo_aplicacion()
        self.visor_3d_parent.visor.update()

    # ------------------------------------------------------------------------
    # DRC
    # ------------------------------------------------------------------------
    def limpiar_marcas_drc(self):
        marcas = [i for i in self.scene.items() if isinstance(i, FlechaError)]
        for item in marcas:
            self.scene.eliminar_item_seguro(item)
        self.scene.update()

    # El DRC es explícitamente bajo demanda. Primero se toma un snapshot de geometría
    # y solo después se crea el worker para no tocar la escena desde el hilo secundario.
    def ejecutar_drc(self):
        # DRC es estrictamente on-demand. Solo se crea el hilo tras la solicitud explícita.
        if self._drc_dialog is not None and self._drc_dialog.isVisible():
            self._drc_dialog.raise_()
            self._drc_dialog.activateWindow()
            return

        self._drc_generation += 1
        generation = self._drc_generation

        pins = []
        tracks = []
        nodes = []
        for item in self.scene.items():
            if isinstance(item, ComponenteLiviano):
                pins.extend(item.obtener_puntos_conexion())
            elif isinstance(item, PistaInteractiva) and item.isVisible():
                line = item.line()
                tracks.append((item.mapToScene(line.p1()), item.mapToScene(line.p2())))
            elif isinstance(item, Nodo) and item.isVisible():
                nodes.append(item.scenePos())

        dlg = DialogoDRC(self)
        dlg.cerrado.connect(self._cerrar_drc)
        self._drc_dialog = dlg
        dlg.show()

        thread = QThread(self)
        worker = DRCWorker(generation, tuple(pins), tuple(tracks), tuple(nodes))
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.terminado.connect(self._finalizar_drc, type=Qt.QueuedConnection)
        worker.error.connect(self._fallo_drc, type=Qt.QueuedConnection)
        worker.terminado.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._drc_thread_finalizado, type=Qt.QueuedConnection)
        self._drc_thread = thread
        self._drc_worker = worker
        thread.start()

    # Este callback vuelve al hilo GUI y es el único lugar donde se crean las
    # FlechaError. El worker nunca manipula widgets.
    def _finalizar_drc(self, generation, errores):
        if generation != self._drc_generation or self._drc_dialog is None:
            return

        # Las marcas permanecen en la escena, pero no duplicamos una flecha
        # si el mismo DRC se ejecuta varias veces sobre el mismo punto.
        existentes = [
            item.scenePos()
            for item in self.scene.items()
            if isinstance(item, FlechaError)
        ]

        for x, y in errores:
            punto = QPointF(x, y)
            if any(QLineF(punto, p).length() < 6.0 for p in existentes):
                continue
            self.scene.addItem(FlechaError(x, y))
            existentes.append(punto)

        self.scene.update()
        self._drc_dialog.mostrar_resultado(errores)

    def _fallo_drc(self, generation, mensaje):
        if generation != self._drc_generation or self._drc_dialog is None:
            return
        self._drc_dialog.mostrar_error(mensaje)

    def _drc_thread_finalizado(self):
        self._drc_thread = None
        self._drc_worker = None

    # Cerrar el diálogo no elimina las marcas: se consideran anotaciones persistentes
    # hasta que el usuario las borre manualmente.
    def _cerrar_drc(self):
        # Las FlechaError son objetos persistentes de la escena; cerrar el diálogo
        # no las elimina. El usuario puede seleccionarlas y usar Supr/Delete.
        self._drc_generation += 1
        self._drc_dialog = None
        if self._drc_thread is not None and self._drc_thread.isRunning():
            self._drc_thread.requestInterruption()

    # ------------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------------
    def mostrar_bom(self):
        conteo = {}
        for item in self.scene.items():
            if isinstance(item, ComponenteLiviano):
                key = f"{item.tipo} - {item.valor}"
                conteo[key] = conteo.get(key, 0) + 1
        
        if not conteo:
            QMessageBox.information(self, "BOM", "El proyecto no contiene componentes.")
            return
            
        texto_bom = "Lista de Materiales (BOM):\n\n"
        for k, v in conteo.items():
            texto_bom += f"- {k} x{v}\n"
            
        QMessageBox.information(self, "BOM", texto_bom)

    def abrir_calculadora(self):
        calc = CalculadoraDialog(self, self.modo_oscuro)
        calc.exec_()

    def mostrar_ayuda(self):
        QMessageBox.information(self, "Comunidad", LANG_DICT[self.lang]["help_msg"])

    # ------------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------------
    # No usamos sceneRect() porque representa el lienzo completo, no el diseño real.
    def _bbox_exportable(self):
        """Bounding box real de los elementos de diseño visibles.

        Se excluyen indicadores visuales del DRC/conexión para que no alteren
        el encuadre de PNG/PDF. No utiliza sceneRect() fijo.
        """
        rect = QRectF()
        inicializado = False
        excluidos = (FlechaError, IndicadorConexion)

        for item in self.scene.items():
            if isinstance(item, excluidos) or not item.isVisible():
                continue

            item_rect = item.sceneBoundingRect()
            if not item_rect.isValid() or item_rect.isNull():
                continue

            rect = item_rect if not inicializado else rect.united(item_rect)
            inicializado = True

        if not inicializado:
            return QRectF(-50, -50, 100, 100)

        return rect

    def _visibilidad_temporal_exportacion(self):
        estados = []
        for item in self.scene.items():
            if isinstance(item, (FlechaError, IndicadorConexion)) and item.isVisible():
                estados.append((item, True))
                item.setVisible(False)
        return estados

    def _restaurar_visibilidad_exportacion(self, estados):
        for item, visible in estados:
            if item.scene() is self.scene:
                item.setVisible(visible)

    # Render intermedio a QImage: evita problemas de coordenadas negativas y permite
    # reutilizar el mismo encuadre para PNG y PDF.
    def _render_exportacion(self, source_rect, scale=2.0):
        """Renderiza el diseño a un QImage sin hoja ni grilla, con margen seguro."""
        width = max(1, int(math.ceil(source_rect.width() * scale)))
        height = max(1, int(math.ceil(source_rect.height() * scale)))

        image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)

        original_bg = self.scene.backgroundBrush()
        estados = self._visibilidad_temporal_exportacion()

        seleccionados = list(self.scene.selectedItems())
        painter = QPainter(image)
        try:
            painter.setRenderHints(
                QPainter.Antialiasing | QPainter.SmoothPixmapTransform,
                True
            )
            self.scene.clearSelection()
            self.scene.setBackgroundBrush(QBrush(Qt.NoBrush))
            self.scene.render(
                painter,
                QRectF(0, 0, width, height),
                source_rect
            )
        finally:
            painter.end()
            self.scene.setBackgroundBrush(original_bg)
            self._restaurar_visibilidad_exportacion(estados)
            for item in seleccionados:
                if item.scene() is self.scene:
                    item.setSelected(True)
            self.scene.update()

        return image

    # PNG se guarda verificando retorno de Qt y existencia/tamaño del archivo.
    def exportar_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a PNG",
            "",
            "PNG (*.png)"
        )
        if not path:
            return

        path = os.path.abspath(os.path.expanduser(path))
        if not path.lower().endswith('.png'):
            path += '.png'

        rect = self._bbox_exportable().adjusted(
            -20, -20, 20, 20
        )

        # Evita generar imágenes gigantes cuando el diseño ocupa una gran área
        # de escena. Se mantiene una resolución alta para un diseño normal.
        max_dimension = 8000.0
        max_side = max(rect.width(), rect.height(), 1.0)
        scale = min(2.0, max_dimension / max_side)
        scale = max(scale, 0.5)

        image = self._render_exportacion(
            rect,
            scale=scale
        )

        if image.isNull():
            QMessageBox.critical(
                self,
                "Error al Exportar",
                "No se pudo crear la imagen del diseño."
            )
            return

        # QImage usa el plugin PNG de Qt. Comprobamos tanto el retorno como
        # la existencia/tamaño real del archivo para no dar falso positivo.
        guardado = image.save(path, "PNG")
        existe = os.path.isfile(path)
        tiene_datos = existe and os.path.getsize(path) > 0

        if not guardado or not tiene_datos:
            QMessageBox.critical(
                self,
                "Error al Exportar",
                f"No se pudo guardar el PNG en:\n{path}"
            )
            return

        QMessageBox.information(
            self,
            "Exportado",
            f"PNG guardado correctamente en:\n{path}"
        )

    # PDF general utiliza el render intermedio para garantizar un encuadre completo.
    def exportar_pdf(self):
        """Exporta el diseño completo a A4 usando el bounding box real.

        El render intermedio evita páginas PDF vacías/cortadas provocadas por
        transformaciones de escena con coordenadas negativas.
        """
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", "", "PDF (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith('.pdf'):
            path += '.pdf'

        rect = self._bbox_exportable().adjusted(-20, -20, 20, 20)
        image = self._render_exportacion(rect, scale=2.0)

        writer = QPdfWriter(path)
        writer.setPageSize(QPageSize(QPageSize.A4))
        writer.setResolution(144)

        painter = QPainter(writer)
        try:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            page_w = float(writer.width())
            page_h = float(writer.height())
            margin = min(56.0, min(page_w, page_h) * 0.06)
            target = QRectF(
                margin,
                margin,
                max(1.0, page_w - margin * 2),
                max(1.0, page_h - margin * 2)
            )

            factor = min(
                target.width() / max(1, image.width()),
                target.height() / max(1, image.height())
            )

            draw_w = image.width() * factor
            draw_h = image.height() * factor
            draw_rect = QRectF(
                target.center().x() - draw_w / 2,
                target.center().y() - draw_h / 2,
                draw_w,
                draw_h
            )

            painter.drawImage(draw_rect, image)
        finally:
            painter.end()

        QMessageBox.information(
            self, "Exportado", "PDF exportado con éxito."
        )

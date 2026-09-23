# =============================================================================
# KlinCAD - Historial, Undo / Redo y snapshots
# =============================================================================

import json

from PyQt5.QtCore import QPointF

from klincad.config import CAPAS_CONFIG
from klincad.items.component import ComponenteLiviano
from klincad.items.track import PistaInteractiva
from klincad.items.node import Nodo
from klincad.items.mesh import Malla


class GestorHistorial:
    """
    Gestión de snapshots para Undo / Redo.

    La clase está pensada como mixin para EditorCircuito.
    Requiere que la clase anfitriona proporcione:
      - self.scene
      - self.panel_capas
      - self.proyecto_activo
      - self.limpiar_marcas_drc()
    """

    def inicializar_historial(self):
        self.historial_undo = []
        self.historial_redo = []
        self._historial_indice = -1
        self.estado_guardado = None
        self._estado_accion_inicio = None

    # -------------------------------------------------------------------------
    # Registro de acciones interactivas
    # -------------------------------------------------------------------------

    def registrar_accion_inicio(self):
        """
        Captura el estado anterior a una edición interactiva.
        """
        if not self.proyecto_activo:
            self._estado_accion_inicio = None
            return

        self._estado_accion_inicio = self.serializar_escena()

    def registrar_accion_fin(self):
        """
        Guarda únicamente el estado final si realmente hubo cambios.
        """
        if not self.proyecto_activo:
            self._estado_accion_inicio = None
            return

        estado_final = self.serializar_escena()
        estado_inicio = self._estado_accion_inicio
        self._estado_accion_inicio = None

        if (
            estado_inicio is None
            or estado_inicio != estado_final
        ):
            self.guardar_estado(estado_final)

    # -------------------------------------------------------------------------
    # Snapshots
    # -------------------------------------------------------------------------

    def guardar_estado(self, estado=None):
        """
        Añade un snapshot único y elimina la rama posterior de Redo.
        """
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
            del self.historial_undo[
                self._historial_indice + 1:
            ]

        self.historial_undo.append(estado)

        self._historial_indice = (
            len(self.historial_undo) - 1
        )

        self.historial_redo.clear()

    # -------------------------------------------------------------------------
    # Serialización de la escena
    # -------------------------------------------------------------------------

    def serializar_escena(self):
        """
        Convierte la escena actual en un snapshot JSON determinista.
        """
        data = {
            "version": "1.0",
            "layer_config": self.scene.orden_capas,
            "components": [],
            "tracks": [],
            "nodes": [],
            "meshes": [],
        }

        for item in self.scene.items():

            if isinstance(item, ComponenteLiviano):
                data["components"].append({
                    "type": item.tipo,
                    "value": item.valor,
                    "ref_id": item.ref_id,
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y(),
                    "rotation": item.rotation(),
                })

            elif isinstance(item, PistaInteractiva):
                line = item.line()

                p1 = item.mapToScene(line.p1())
                p2 = item.mapToScene(line.p2())

                data["tracks"].append({
                    "layer": item.capa,
                    "x1": p1.x(),
                    "y1": p1.y(),
                    "x2": p2.x(),
                    "y2": p2.y(),
                })

            elif isinstance(item, Nodo):
                data["nodes"].append({
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y(),
                    "rotation": item.rotation(),
                })

            elif isinstance(item, Malla):
                data["meshes"].append({
                    "x": item.scenePos().x(),
                    "y": item.scenePos().y(),
                    "rotation": item.rotation(),
                })

        # Orden determinista para evitar snapshots equivalentes
        # con distinto orden interno.
        data["components"].sort(
            key=lambda d: (
                d["ref_id"],
                d["type"],
                d["value"],
                d["x"],
                d["y"],
                d["rotation"],
            )
        )

        data["tracks"].sort(
            key=lambda d: (
                d["layer"],
                d["x1"],
                d["y1"],
                d["x2"],
                d["y2"],
            )
        )

        data["nodes"].sort(
            key=lambda d: (
                d["x"],
                d["y"],
                d["rotation"],
            )
        )

        data["meshes"].sort(
            key=lambda d: (
                d["x"],
                d["y"],
                d["rotation"],
            )
        )

        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
        )

    # -------------------------------------------------------------------------
    # Restauración
    # -------------------------------------------------------------------------

    def cargar_estado(self, estado_str):
        """
        Reconstruye la escena exactamente desde un snapshot.
        """
        data = json.loads(estado_str)

        self.limpiar_marcas_drc()
        self.scene.limpiar_escena()

        for comp_data in data.get("components", []):
            item = ComponenteLiviano(
                comp_data["x"],
                comp_data["y"],
                comp_data["type"],
                comp_data["value"],
                comp_data.get("ref_id", ""),
            )

            self.scene.addItem(item)

            item.setPos(
                QPointF(
                    comp_data["x"],
                    comp_data["y"],
                )
            )

            item.setRotation(
                comp_data.get("rotation", 0)
            )

        for track_data in data.get("tracks", []):
            item = PistaInteractiva(
                track_data["x1"],
                track_data["y1"],
                track_data["x2"],
                track_data["y2"],
                track_data.get(
                    "layer",
                    "Top Copper",
                ),
            )

            self.scene.addItem(item)

        for node_data in data.get("nodes", []):
            item = Nodo(
                node_data["x"],
                node_data["y"],
            )

            self.scene.addItem(item)

            item.setPos(
                QPointF(
                    node_data["x"],
                    node_data["y"],
                )
            )

            item.setRotation(
                node_data.get("rotation", 0)
            )

        for mesh_data in data.get("meshes", []):
            item = Malla(
                mesh_data["x"],
                mesh_data["y"],
            )

            self.scene.addItem(item)

            item.setPos(
                QPointF(
                    mesh_data["x"],
                    mesh_data["y"],
                )
            )

            item.setRotation(
                mesh_data.get("rotation", 0)
            )

        self.scene.orden_capas = data.get(
            "layer_config",
            list(CAPAS_CONFIG.keys()),
        )

        self.panel_capas.orden_capas = (
            self.scene.orden_capas
        )

        self.panel_capas.reconstruir_ui()

        # No renumerar aquí: Undo / Redo debe restaurar
        # exactamente el estado guardado.
        for item in self.scene.items():
            if isinstance(item, ComponenteLiviano):
                item.actualizar_texto_etiqueta()

        self.scene.actualizar_indicadores_conexion()

    # -------------------------------------------------------------------------
    # Undo
    # -------------------------------------------------------------------------

    def deshacer(self):
        """
        Retrocede exactamente un snapshot.
        """
        if not self.proyecto_activo:
            return

        if self._historial_indice <= 0:
            return

        self._historial_indice -= 1
        self._estado_accion_inicio = None

        self.cargar_estado(
            self.historial_undo[
                self._historial_indice
            ]
        )

    # -------------------------------------------------------------------------
    # Redo
    # -------------------------------------------------------------------------

    def rehacer(self):
        """
        Avanza exactamente un snapshot.
        """
        if not self.proyecto_activo:
            return

        if (
            self._historial_indice
            >= len(self.historial_undo) - 1
        ):
            return

        self._historial_indice += 1
        self._estado_accion_inicio = None

        self.cargar_estado(
            self.historial_undo[
                self._historial_indice
            ]
        )

# =============================================================================
# KlinCAD - Panel de herramientas, capas y contenedores de interfaz
# =============================================================================

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from klincad.config import CAPAS_CONFIG
from klincad.items.track import PistaInteractiva


# -----------------------------------------------------------------------------
# Panel flotante para visibilidad y orden de las capas.
class PanelCapasWidget(QWidget):

    def __init__(self, scene, parent=None):
        super().__init__(parent)

        self.scene = scene

        if not hasattr(
            self.scene,
            "orden_capas"
        ):
            self.scene.orden_capas = list(
                CAPAS_CONFIG.keys()
            )

        self.orden_capas = (
            self.scene.orden_capas
        )

        self.setObjectName(
            "PanelCapas"
        )

        self.setStyleSheet(
            """
            #PanelCapas {
                background-color: rgba(15, 23, 42, 0.9);
                border: 1px solid #334155;
                border-radius: 8px;
            }

            QLabel {
                color: #f8fafc;
                font-weight: bold;
                font-size: 11px;
            }

            QCheckBox {
                color: #f8fafc;
                font-size: 11px;
            }

            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #475569;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
            }

            QPushButton:hover {
                background-color: #334155;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        layout.setSpacing(6)

        lbl_titulo = QLabel(
            "SISTEMA DE CAPAS"
        )

        layout.addWidget(
            lbl_titulo
        )

        self.filas_capas = []

        self.contenedor_filas = QVBoxLayout()

        self.contenedor_filas.setSpacing(
            4
        )

        layout.addLayout(
            self.contenedor_filas
        )

        self.reconstruir_ui()

    def reconstruir_ui(self):
        while self.contenedor_filas.count():
            child = (
                self.contenedor_filas.takeAt(0)
            )

            if child.widget():
                child.widget().deleteLater()

        self.filas_capas.clear()

        for idx, nombre_capa in enumerate(
            self.orden_capas
        ):
            row_widget = QWidget()

            row_layout = QHBoxLayout(
                row_widget
            )

            row_layout.setContentsMargins(
                0,
                0,
                0,
                0
            )

            row_layout.setSpacing(4)

            cb = QCheckBox(
                nombre_capa
            )

            cb.setChecked(True)

            c_hex = CAPAS_CONFIG[
                nombre_capa
            ]["color"].name()

            cb.setStyleSheet(
                "QCheckBox { "
                f"color: {c_hex}; "
                "font-weight: bold; "
                "}"
            )

            cb.toggled.connect(
                lambda chk, n=nombre_capa:
                    self.toggle_visibilidad_capa(
                        n,
                        chk
                    )
            )

            btn_up = QPushButton(
                "▲"
            )

            btn_down = QPushButton(
                "▼"
            )

            btn_up.setEnabled(
                idx > 0
            )

            btn_down.setEnabled(
                idx < len(self.orden_capas) - 1
            )

            btn_up.clicked.connect(
                lambda _, i=idx:
                    self.mover_capa(i, -1)
            )

            btn_down.clicked.connect(
                lambda _, i=idx:
                    self.mover_capa(i, 1)
            )

            row_layout.addWidget(
                cb
            )

            row_layout.addStretch()

            row_layout.addWidget(
                btn_up
            )

            row_layout.addWidget(
                btn_down
            )

            self.contenedor_filas.addWidget(
                row_widget
            )

    def toggle_visibilidad_capa(
        self,
        nombre_capa,
        visible
    ):
        for item in self.scene.items():
            if (
                isinstance(
                    item,
                    PistaInteractiva
                )
                and item.capa == nombre_capa
            ):
                item.setVisible(
                    visible
                )

        self.scene.actualizar_indicadores_conexion()

        if self.scene.visor_iso_ref:
            self.scene.visor_iso_ref.update()

    def mover_capa(
        self,
        index,
        direccion
    ):
        new_index = (
            index + direccion
        )

        if (
            0
            <= new_index
            < len(self.orden_capas)
        ):
            (
                self.orden_capas[index],
                self.orden_capas[new_index],
            ) = (
                self.orden_capas[new_index],
                self.orden_capas[index],
            )

            self.scene.orden_capas = (
                self.orden_capas
            )

            self.actualizar_z_indexes()
            self.reconstruir_ui()

    def actualizar_z_indexes(self):
        total = len(
            self.orden_capas
        )

        for idx, nombre_capa in enumerate(
            self.orden_capas
        ):
            z_val = (
                total - idx
            ) * 5

            for item in self.scene.items():
                if (
                    isinstance(
                        item,
                        PistaInteractiva
                    )
                    and item.capa == nombre_capa
                ):
                    item.setZValue(
                        z_val
                    )

        if (
            self.scene.visor_iso_ref
            and self.scene.visor_iso_ref.isVisible()
        ):
            self.scene.visor_iso_ref.update()


# -----------------------------------------------------------------------------
# Contenedor que superpone visor 3D, capas y pantalla de precarga.
class OverlayContainer(QWidget):

    def __init__(
        self,
        background_widget,
        overlay_visor,
        overlay_capas,
        preload_widget,
        parent=None,
    ):
        super().__init__(parent)

        self.background_widget = (
            background_widget
        )

        self.overlay_visor = (
            overlay_visor
        )

        self.overlay_capas = (
            overlay_capas
        )

        self.preload_widget = (
            preload_widget
        )

        self.watermark = QLabel(
            "KlinCAD",
            self
        )

        self.watermark.setStyleSheet(
            "font-size: 32px; "
            "font-weight: bold; "
            "font-family: sans-serif; "
            "color: rgba(148, 163, 184, 0.4);"
        )

        self.watermark.setAttribute(
            Qt.WA_TransparentForMouseEvents
        )

        self.background_widget.setParent(
            self
        )

        self.overlay_visor.setParent(
            self
        )

        self.overlay_capas.setParent(
            self
        )

        self.preload_widget.setParent(
            self
        )

        self.watermark.setParent(
            self
        )

        self.overlay_visor.raise_()
        self.overlay_capas.raise_()
        self.preload_widget.raise_()
        self.watermark.raise_()

    def resizeEvent(self, event):
        rect = self.rect()

        self.background_widget.setGeometry(
            rect
        )

        self.preload_widget.setGeometry(
            rect
        )

        w_overlay = 260
        h_visor = 260
        h_capas = 150
        margin = 15
        gap = 10

        y_visor = (
            rect.height()
            - h_visor
            - margin
        )

        self.overlay_visor.setGeometry(
            margin,
            y_visor,
            w_overlay,
            h_visor
        )

        y_capas = (
            y_visor
            - h_capas
            - gap
        )

        self.overlay_capas.setGeometry(
            margin,
            y_capas,
            w_overlay,
            h_capas
        )

        self.watermark.setGeometry(
            rect.width() - 150,
            rect.height() - 60,
            140,
            50
        )

        super().resizeEvent(
            event
        )

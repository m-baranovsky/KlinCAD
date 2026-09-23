# =============================================================================
# KlinCAD - Design Rule Check (DRC)
# =============================================================================

from PyQt5.QtCore import QLineF, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from klincad.config import SNAP_THRESHOLD


class DRCWorker(QObject):
    """
    Ejecuta el análisis DRC sobre datos simples.

    El worker no modifica QGraphicsItem ni la escena.
    """

    terminado = pyqtSignal(int, list)
    error = pyqtSignal(int, str)

    def __init__(self, generation, pins, tracks, nodes, parent=None):
        super().__init__(parent)

        self.generation = generation
        self.pins = pins
        self.tracks = tracks
        self.nodes = nodes

    def run(self):
        try:
            errores = []
            threshold = SNAP_THRESHOLD

            for p in self.pins:

                if QThread.currentThread().isInterruptionRequested():
                    return

                conectado = False

                # Comprobar conexión con extremos de pistas.
                for p1, p2 in self.tracks:
                    if (
                        QLineF(p, p1).length() < threshold
                        or QLineF(p, p2).length() < threshold
                    ):
                        conectado = True
                        break

                # Comprobar conexión con nodos.
                if not conectado:
                    for nodo in self.nodes:
                        if QLineF(p, nodo).length() < threshold:
                            conectado = True
                            break

                if not conectado:
                    errores.append(
                        (p.x(), p.y())
                    )

            self.terminado.emit(
                self.generation,
                errores
            )

        except Exception as exc:
            self.error.emit(
                self.generation,
                str(exc)
            )


class DialogoDRC(QDialog):
    """
    Ventana no modal que muestra el resultado del DRC.
    """

    cerrado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Design Rule Check (DRC)"
        )

        self.setModal(False)

        self.setMinimumSize(
            520,
            170
        )

        self.resize(
            560,
            190
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            18,
            20,
            18
        )

        layout.setSpacing(14)

        self.lbl_estado = QLabel(
            "Calculando errores…"
        )

        self.lbl_estado.setWordWrap(True)

        self.lbl_estado.setMinimumHeight(
            54
        )

        self.lbl_estado.setMinimumWidth(
            460
        )

        layout.addWidget(
            self.lbl_estado,
            1
        )

        btn_layout = QHBoxLayout()

        btn_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        btn_layout.addStretch()

        self.btn_cerrar = QPushButton(
            "Cerrar"
        )

        self.btn_cerrar.setMinimumWidth(
            100
        )

        self.btn_cerrar.clicked.connect(
            self.close
        )

        btn_layout.addWidget(
            self.btn_cerrar
        )

        layout.addLayout(
            btn_layout
        )

    def mostrar_resultado(self, errores):
        if errores:
            self.lbl_estado.setText(
                f"Se encontraron {len(errores)} "
                "pines flotantes/desconectados. "
                "Se marcaron con flechas rojas."
            )
        else:
            self.lbl_estado.setText(
                "Sin errores: no se encontraron "
                "problemas de conexión."
            )

        self.adjustSize()

    def mostrar_error(self, mensaje):
        self.lbl_estado.setText(
            f"Error durante el DRC: {mensaje}"
        )

        self.adjustSize()

    def closeEvent(self, event):
        self.cerrado.emit()
        event.accept()

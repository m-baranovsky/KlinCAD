# =============================================================================
# KlinCAD - Diálogos y ventanas auxiliares
# =============================================================================

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
)

from klincad.config import CAPAS_CONFIG
from klincad.i18n import LANG_DICT


# -----------------------------------------------------------------------------
# Diálogo paginado de ayuda inicial.
class GuiaDialog(QDialog):

    def __init__(self, parent=None, lang="es"):
        super().__init__(parent)

        self.lang = lang
        t = LANG_DICT[lang]

        self.setWindowTitle(
            t["guide_title"]
        )

        self.setFixedSize(
            480,
            240
        )

        self.paginas = [
            {
                "title": t["g1_t"],
                "text": t["g1_c"],
            },
            {
                "title": t["g2_t"],
                "text": t["g2_c"],
            },
            {
                "title": t["g3_t"],
                "text": t["g3_c"],
            },
            {
                "title": t["g4_t"],
                "text": t["g4_c"],
            },
            {
                "title": t["g5_t"],
                "text": t["g5_c"],
            },
            {
                "title": t["g6_t"],
                "text": t["g6_c"],
            },
            {
                "title": t["g7_t"],
                "text": t["g7_c"],
            },
        ]

        self.idx = 0

        self.layout = QVBoxLayout(self)

        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet(
            "font-size: 18px; font-weight: bold;"
        )

        self.txt_content = QTextEdit()
        self.txt_content.setReadOnly(True)
        self.txt_content.setStyleSheet(
            "font-size: 14px; "
            "background: transparent; "
            "border: none;"
        )

        self.layout.addWidget(
            self.lbl_title
        )

        self.layout.addWidget(
            self.txt_content
        )

        btn_layout = QHBoxLayout()

        self.btn_next = QPushButton()
        self.btn_next.setCursor(
            Qt.PointingHandCursor
        )

        self.btn_next.clicked.connect(
            self.siguiente
        )

        btn_layout.addStretch()
        btn_layout.addWidget(
            self.btn_next
        )

        self.layout.addLayout(
            btn_layout
        )

        self.aplicar_estilos(parent)
        self.actualizar_vista()

    def aplicar_estilos(self, parent):
        oscuro = (
            parent
            and getattr(parent, "modo_oscuro", False)
        )

        if oscuro:
            self.setStyleSheet(
                """
                QDialog {
                    background-color: #1e293b;
                    color: #f8fafc;
                }

                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    padding: 6px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #1d4ed8;
                }
                """
            )

            self.lbl_title.setStyleSheet(
                "font-size: 18px; "
                "font-weight: bold; "
                "color: #38bdf8;"
            )

            self.txt_content.setStyleSheet(
                "font-size: 14px; "
                "background: transparent; "
                "border: none; "
                "color: #f8fafc;"
            )

        else:
            self.setStyleSheet(
                """
                QDialog {
                    background-color: #f8fafc;
                    color: #0f172a;
                }

                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    padding: 6px 15px;
                    border-radius: 4px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #2563eb;
                }
                """
            )

            self.lbl_title.setStyleSheet(
                "font-size: 18px; "
                "font-weight: bold; "
                "color: #0284c7;"
            )

            self.txt_content.setStyleSheet(
                "font-size: 14px; "
                "background: transparent; "
                "border: none; "
                "color: #0f172a;"
            )

    def actualizar_vista(self):
        t = LANG_DICT[self.lang]
        page = self.paginas[self.idx]

        self.lbl_title.setText(
            page["title"]
        )

        self.txt_content.setText(
            page["text"]
        )

        if self.idx == len(self.paginas) - 1:
            self.btn_next.setText(
                t["guide_finish"]
            )
        else:
            self.btn_next.setText(
                t["guide_next"]
            )

    def siguiente(self):
        if self.idx < len(self.paginas) - 1:
            self.idx += 1
            self.actualizar_vista()
        else:
            self.accept()


# -----------------------------------------------------------------------------
# Aviso y licencia inicial.
class SplashDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Bienvenido a KlinCAD v1.0"
        )

        self.setFixedSize(
            540,
            430
        )

        self.setStyleSheet(
            """
            QDialog {
                background-color: #0f172a;
                color: #f8fafc;
            }

            QLabel {
                color: #f8fafc;
            }

            QTextEdit {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }

            QPushButton#btn_aceptar {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 6px;
                border: none;
            }

            QPushButton#btn_aceptar:hover {
                background-color: #1d4ed8;
            }

            QPushButton#btn_cancelar {
                background-color: #334155;
                color: #f8fafc;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 6px;
                border: none;
            }

            QPushButton#btn_cancelar:hover {
                background-color: #475569;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        layout.setSpacing(10)

        lbl_titulo = QLabel(
            "KlinCAD v1.0"
        )

        lbl_titulo.setStyleSheet(
            "font-size: 20px; "
            "font-weight: bold; "
            "color: #38bdf8;"
        )

        lbl_subtitulo = QLabel(
            "Diseño sin rodeos. Electrónica sin ataduras."
        )

        lbl_subtitulo.setStyleSheet(
            "font-size: 14px; "
            "font-weight: bold; "
            "color: #94a3b8; "
            "margin-bottom: 5px;"
        )

        txt_contenido = QTextEdit()
        txt_contenido.setReadOnly(True)

        mensaje = (
            "¡Bienvenido al taller!\n\n"
            "Este software es de código abierto (Open Source) "
            "y fue creado con una misión clara: simplificar "
            "tus primeros pasos en el diseño de circuitos "
            "antes de dar el salto a herramientas pesadas.\n\n"
            "Condiciones de uso (Licencia Abierta):\n"
            "Puedes usarlo, modificarlo, estudiarlo y compartirlo "
            "libremente. Si decidís usar este código o este proyecto "
            "para crear algo nuevo, derivado o comercial, debes "
            "mantener el reconocimiento original incluyendo mi "
            "nombre (Matias Baranovsky) como autor del proyecto base.\n\n"
            "Al hacer clic en \"Aceptar y Diseñar\", reconocés que "
            "el software se entrega \"tal cual es\" "
            "(sin garantías formales) y aceptás los términos "
            "de esta licencia libre."
        )

        txt_contenido.setPlainText(
            mensaje
        )

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancelar = QPushButton(
            "Cancelar"
        )

        btn_cancelar.setObjectName(
            "btn_cancelar"
        )

        btn_cancelar.setCursor(
            Qt.PointingHandCursor
        )

        btn_cancelar.clicked.connect(
            self._salir_sin_aceptar
        )

        btn_aceptar = QPushButton(
            "Aceptar y Diseñar"
        )

        btn_aceptar.setObjectName(
            "btn_aceptar"
        )

        btn_aceptar.setCursor(
            Qt.PointingHandCursor
        )

        btn_aceptar.clicked.connect(
            self.accept
        )

        btn_layout.addWidget(
            btn_cancelar
        )

        btn_layout.addSpacing(
            10
        )

        btn_layout.addWidget(
            btn_aceptar
        )

        layout.addWidget(
            lbl_titulo
        )

        layout.addWidget(
            lbl_subtitulo
        )

        layout.addWidget(
            txt_contenido
        )

        layout.addLayout(
            btn_layout
        )

    def _salir_sin_aceptar(self):
        sys.exit(0)

    def reject(self):
        sys.exit(0)

    def closeEvent(self, event):
        event.ignore()
        sys.exit(0)


# -----------------------------------------------------------------------------
# Pantalla inicial antes de habilitar la edición.
class PaginaPrecargaWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName(
            "PaginaPrecarga"
        )

        self.setStyleSheet(
            """
            #PaginaPrecarga {
                background-color: #0f172a;
            }

            QLabel#lbl_logo {
                font-size: 42px;
                font-weight: bold;
                color: #38bdf8;
                font-family: sans-serif;
            }

            QLabel#lbl_frase {
                font-size: 19px;
                font-style: italic;
                color: #94a3b8;
                margin-top: 10px;
                margin-bottom: 35px;
            }

            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
                border-color: #3b82f6;
                color: #ffffff;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(
            Qt.AlignCenter
        )

        container = QWidget()

        c_layout = QVBoxLayout(
            container
        )

        c_layout.setAlignment(
            Qt.AlignCenter
        )

        lbl_logo = QLabel(
            "KlinCAD"
        )

        lbl_logo.setObjectName(
            "lbl_logo"
        )

        lbl_logo.setAlignment(
            Qt.AlignCenter
        )

        lbl_frase = QLabel(
            '"Tu primer circuito, a la velocidad de la luz."'
        )

        lbl_frase.setObjectName(
            "lbl_frase"
        )

        lbl_frase.setAlignment(
            Qt.AlignCenter
        )

        btn_box = QHBoxLayout()
        btn_box.setSpacing(15)

        self.btn_nuevo = QPushButton(
            "⚡ Nuevo Proyecto"
        )

        self.btn_nuevo.setCursor(
            Qt.PointingHandCursor
        )

        self.btn_abrir = QPushButton(
            "📂 Abrir Proyecto"
        )

        self.btn_abrir.setCursor(
            Qt.PointingHandCursor
        )

        btn_box.addWidget(
            self.btn_nuevo
        )

        btn_box.addWidget(
            self.btn_abrir
        )

        c_layout.addWidget(
            lbl_logo
        )

        c_layout.addWidget(
            lbl_frase
        )

        c_layout.addLayout(
            btn_box
        )

        layout.addWidget(
            container
        )

    def actualizar_idioma(self, lang):
        t = LANG_DICT[lang]

        self.btn_nuevo.setText(
            f"⚡ {t['new_proj']}"
        )

        self.btn_abrir.setText(
            f"📂 {t['open_proj']}"
        )

        self.findChild(
            QLabel,
            "lbl_frase"
        ).setText(
            t["phrase"]
        )


# -----------------------------------------------------------------------------
# Calculadora auxiliar.
class CalculadoraDialog(QDialog):

    def __init__(
        self,
        parent=None,
        modo_oscuro=False
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Calculadora Electrónica Lógica"
        )

        self.setFixedSize(
            380,
            260
        )

        if modo_oscuro:
            self.setStyleSheet(
                """
                QDialog {
                    background-color: #1e293b;
                    color: #f8fafc;
                }

                QLabel {
                    color: #f8fafc;
                }

                QComboBox,
                QLineEdit {
                    background-color: #0f172a;
                    color: #f8fafc;
                    border: 1px solid #334155;
                    padding: 4px;
                    border-radius: 4px;
                }

                QPushButton {
                    background-color: #2563eb;
                    color: #ffffff;
                    padding: 6px;
                    border-radius: 4px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #1d4ed8;
                }
                """
            )

        layout = QVBoxLayout(self)

        self.combo_tipo = QComboBox()

        self.combo_tipo.addItems([
            "Ley de Ohm: Voltaje (V = I * R)",
            "Ley de Ohm: Intensidad (I = V / R)",
            "Ley de Ohm: Resistencia (R = V / I)",
            "Potencia Eléctrica (P = V * I)",
            "Coeficiente de Resistividad (R = ρ * L / A)",
        ])

        layout.addWidget(
            QLabel(
                "Seleccione el cálculo a realizar:"
            )
        )

        layout.addWidget(
            self.combo_tipo
        )

        self.form_layout = QFormLayout()

        self.input1 = QLineEdit()
        self.input2 = QLineEdit()
        self.input3 = QLineEdit()

        self.lbl_in1 = QLabel()
        self.lbl_in2 = QLabel()
        self.lbl_in3 = QLabel()

        self.form_layout.addRow(
            self.lbl_in1,
            self.input1
        )

        self.form_layout.addRow(
            self.lbl_in2,
            self.input2
        )

        self.form_layout.addRow(
            self.lbl_in3,
            self.input3
        )

        layout.addLayout(
            self.form_layout
        )

        self.btn_calcular = QPushButton(
            "Calcular"
        )

        self.btn_calcular.clicked.connect(
            self.calcular
        )

        layout.addWidget(
            self.btn_calcular
        )

        self.lbl_resultado = QLabel(
            "Resultado: "
        )

        color_resultado = (
            "#4ade80"
            if modo_oscuro
            else "#16a34a"
        )

        self.lbl_resultado.setStyleSheet(
            "font-weight: bold; "
            "font-size: 15px; "
            f"color: {color_resultado}; "
            "margin-top: 10px;"
        )

        layout.addWidget(
            self.lbl_resultado
        )

        self.combo_tipo.currentIndexChanged.connect(
            self.actualizar_ui
        )

        self.actualizar_ui()

    def actualizar_ui(self):
        idx = self.combo_tipo.currentIndex()

        self.input3.setVisible(False)
        self.lbl_in3.setVisible(False)

        self.input1.clear()
        self.input2.clear()
        self.input3.clear()

        self.lbl_resultado.setText(
            "Resultado: "
        )

        if idx == 0:
            self.lbl_in1.setText(
                "Intensidad I (A):"
            )

            self.lbl_in2.setText(
                "Resistencia R (Ω):"
            )

        elif idx == 1:
            self.lbl_in1.setText(
                "Voltaje V (V):"
            )

            self.lbl_in2.setText(
                "Resistencia R (Ω):"
            )

        elif idx == 2:
            self.lbl_in1.setText(
                "Voltaje V (V):"
            )

            self.lbl_in2.setText(
                "Intensidad I (A):"
            )

        elif idx == 3:
            self.lbl_in1.setText(
                "Voltaje V (V):"
            )

            self.lbl_in2.setText(
                "Intensidad I (A):"
            )

        elif idx == 4:
            self.input3.setVisible(True)
            self.lbl_in3.setVisible(True)

            self.lbl_in1.setText(
                "Resistividad ρ (Ω·m):"
            )

            self.lbl_in2.setText(
                "Longitud L (m):"
            )

            self.lbl_in3.setText(
                "Sección A (m²):"
            )

    def calcular(self):
        idx = self.combo_tipo.currentIndex()

        try:
            v1 = float(
                self.input1.text().replace(",", ".")
            )

            v2 = float(
                self.input2.text().replace(",", ".")
            )

            if idx == 0:
                self.lbl_resultado.setText(
                    f"Resultado: {v1 * v2:.4f} V"
                )

            elif idx == 1:
                self.lbl_resultado.setText(
                    f"Resultado: {v1 / v2:.4f} A"
                )

            elif idx == 2:
                self.lbl_resultado.setText(
                    f"Resultado: {v1 / v2:.4f} Ω"
                )

            elif idx == 3:
                self.lbl_resultado.setText(
                    f"Resultado: {v1 * v2:.4f} W"
                )

            elif idx == 4:
                v3 = float(
                    self.input3.text().replace(",", ".")
                )

                self.lbl_resultado.setText(
                    f"Resultado: {(v1 * v2) / v3:.6f} Ω"
                )

        except ValueError:
            self.lbl_resultado.setText(
                "Error: Ingrese valores numéricos válidos."
            )

        except ZeroDivisionError:
            self.lbl_resultado.setText(
                "Error: División por cero."
            )


# -----------------------------------------------------------------------------
# Selector visual de la capa utilizada para nuevas pistas.
class SeleccionCapaDialog(QDialog):

    def __init__(
        self,
        capa_actual="Top Copper",
        parent=None
    ):
        super().__init__(parent)

        self.setWindowTitle(
            "Seleccionar Capa"
        )

        self.setFixedSize(
            280,
            220
        )

        self.capa_seleccionada = capa_actual

        if (
            parent
            and hasattr(parent, "modo_oscuro")
            and parent.modo_oscuro
        ):
            self.setStyleSheet(
                """
                QDialog {
                    background-color: #1e293b;
                    color: #f8fafc;
                }

                QLabel {
                    color: #f8fafc;
                }
                """
            )

        layout = QVBoxLayout(self)

        lbl = QLabel(
            "Elige la capa para la nueva pista:"
        )

        lbl.setStyleSheet(
            "font-weight: bold;"
        )

        layout.addWidget(
            lbl
        )

        self.btn_group = QButtonGroup(
            self
        )

        for i, (
            nombre_capa,
            cfg
        ) in enumerate(
            CAPAS_CONFIG.items()
        ):
            rb = QRadioButton(
                nombre_capa
            )

            c_hex = cfg["color"].name()

            rb.setStyleSheet(
                "QRadioButton { "
                f"color: {c_hex}; "
                "font-weight: bold; "
                "}"
            )

            if nombre_capa == capa_actual:
                rb.setChecked(True)

            self.btn_group.addButton(
                rb,
                i
            )

            layout.addWidget(
                rb
            )

        btn_ok = QPushButton(
            "Aceptar"
        )

        btn_ok.clicked.connect(
            self.accept
        )

        layout.addWidget(
            btn_ok
        )

    def obtener_capa(self):
        btn = self.btn_group.checkedButton()

        return (
            btn.text()
            if btn
            else self.capa_seleccionada
        )

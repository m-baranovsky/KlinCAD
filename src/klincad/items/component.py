# =============================================================================
# KlinCAD - Componentes electrónicos
# =============================================================================

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PyQt5.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
)

from klincad.i18n import LANG_DICT
from klincad.utils.geometry import snap_to_grid


# Mixin mínimo para objetos que necesitan un origen de rotación estable.
class BaseItemRotable:
    def preparar_origen_rotacion(self):
        rect = self.boundingRect()
        self.setTransformOriginPoint(rect.center())


class PinLogico:
    def __init__(self, id_pin, nombre, x, y):
        self.id_pin = id_pin
        self.nombre = nombre
        self.x = x
        self.y = y
        self.net_id = None


class ComponenteLiviano(QGraphicsRectItem, BaseItemRotable):
    def __init__(self, x, y, tipo, valor, ref_id=""):
        super().__init__(0, 0, 80, 40)

        # Los componentes se mueven continuamente durante el arrastre.
        # Sin caché evitamos que queden zonas antiguas de dibujo visibles.
        self.setCacheMode(QGraphicsItem.NoCache)
        self.setZValue(20)

        self.tipo = tipo
        self.valor = valor
        self.ref_id = ref_id
        self.pines_logicos = []
        self.pin_labels = []
        self.is_highlighted = False

        self.actualizar_tooltip()

        self.label = QGraphicsTextItem("", self)
        self.label.setFont(QFont("sans-serif", 9, QFont.Bold))
        self.label.setDefaultTextColor(QColor("#000000"))

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable
        )

        self.actualizar_dimensiones_y_posicion()
        self.generar_pines_logicos()
        self.actualizar_texto_etiqueta()
        self.preparar_origen_rotacion()

        pos_snapped = snap_to_grid(QPointF(x, y))
        self.setPos(pos_snapped)

    def actualizar_tooltip(self):
        lang = getattr(self.scene(), "lang", "es") if self.scene() else "es"
        t = LANG_DICT[lang]

        mapeo_tt = {
            "Resistor": t["tt_resistor"],
            "Capacitor": t["tt_cap"],
            "Inductor / Bobina": t["tt_ind"],
            "Diodo": t["tt_diode"],
            "Zener": t["tt_zener"],
            "Transistor": t["tt_trans"],
            "Circuito Integrado": t["tt_ic"],
            "LED": t["tt_led"],
            "Buzzer / Zumbador": t["tt_buzzer"],
            "Display 7 Segmentos": t["tt_display"],
            "Pulsador / Push Button": t["tt_push"],
            "Interruptor / Switch": t["tt_switch"],
            "Batería / Pila": t["tt_batt"],
            "Terminal Alimentación": t["tt_term"],
            "Conector de Placa": t["tt_con"],
            "Agujero de Montaje": t["tt_hole"],
        }

        self.setToolTip(mapeo_tt.get(self.tipo, "Componente"))

    def actualizar_dimensiones_y_posicion(self):
        if self.tipo in [
            "Resistor",
            "Capacitor",
            "Inductor / Bobina",
            "Diodo",
            "Zener",
            "LED",
            "Pulsador / Push Button",
            "Interruptor / Switch",
            "Batería / Pila",
        ]:
            self.setRect(0, 0, 80, 40)
            self.label.setPos(0, -35)

        elif self.tipo == "Transistor":
            self.setRect(0, 0, 60, 60)
            self.label.setPos(0, -35)

        elif self.tipo in [
            "Buzzer / Zumbador",
            "Terminal Alimentación",
            "Agujero de Montaje",
        ]:
            self.setRect(0, 0, 40, 40)
            self.label.setPos(-10, -35)

        elif self.tipo == "Circuito Integrado":
            self.setRect(0, 0, 80, 80)
            self.label.setPos(0, -35)

        elif self.tipo == "Display 7 Segmentos":
            self.setRect(0, 0, 60, 100)
            self.label.setPos(0, -35)

        elif self.tipo == "Conector de Placa":
            num_pines = 4 if "1x4" in self.valor else 2
            self.setRect(0, 0, 40, num_pines * 20 + 20)
            self.label.setPos(-10, -35)

    def generar_pines_logicos(self):
        w = self.rect().width()
        h = self.rect().height()

        self.pines_logicos.clear()

        for lbl in self.pin_labels:
            if lbl.scene():
                lbl.scene().removeItem(lbl)

        self.pin_labels.clear()

        if self.tipo == "Display 7 Segmentos":
            for i, n in enumerate(["G", "F", "COM1", "A", "B"]):
                self.pines_logicos.append(
                    PinLogico(i + 1, n, 10 + i * 10, 0)
                )

            for i, n in enumerate(["E", "D", "COM2", "C", "DP"]):
                self.pines_logicos.append(
                    PinLogico(i + 6, n, 10 + i * 10, h)
                )

        elif self.tipo == "Conector de Placa":
            num_pines = 4 if "1x4" in self.valor else 2

            for i in range(num_pines):
                self.pines_logicos.append(
                    PinLogico(i + 1, str(i + 1), 20, 20 + i * 20)
                )

        elif self.tipo in ["Diodo", "Zener", "LED"]:
            self.pines_logicos.append(
                PinLogico(1, "A", 0, h / 2)
            )
            self.pines_logicos.append(
                PinLogico(2, "K", w, h / 2)
            )

        elif self.tipo == "Transistor":
            self.pines_logicos.append(
                PinLogico(1, "Base", 0, h / 2)
            )
            self.pines_logicos.append(
                PinLogico(2, "Colector", w, 10)
            )
            self.pines_logicos.append(
                PinLogico(3, "Emisor", w, h - 10)
            )

        elif self.tipo == "Circuito Integrado":
            for idx, y_pos in enumerate([20, 40, 60]):
                self.pines_logicos.append(
                    PinLogico(idx + 1, f"L{idx + 1}", 0, y_pos)
                )
                self.pines_logicos.append(
                    PinLogico(idx + 4, f"R{idx + 1}", w, y_pos)
                )

        elif self.tipo == "Terminal Alimentación":
            self.pines_logicos.append(
                PinLogico(1, "IN/OUT", w / 2, h)
            )

        elif self.tipo == "Batería / Pila":
            self.pines_logicos.append(
                PinLogico(1, "+", 0, h / 2)
            )
            self.pines_logicos.append(
                PinLogico(2, "-", w, h / 2)
            )

        elif self.tipo == "Agujero de Montaje":
            pass

        elif self.tipo == "Resistor":
            self.pines_logicos.append(
                PinLogico(1, "1", 0, h / 2)
            )
            self.pines_logicos.append(
                PinLogico(2, "2", w, h / 2)
            )

        else:
            self.pines_logicos.append(
                PinLogico(1, "1", 0, h / 2)
            )
            self.pines_logicos.append(
                PinLogico(2, "2", w, h / 2)
            )

        for p in self.pines_logicos:
            lbl = QGraphicsTextItem(p.nombre, self)
            lbl.setFont(QFont("sans-serif", 9, QFont.Bold))
            lbl.setZValue(35)

            self._posicionar_etiqueta_pin(lbl, p, w, h)
            self.pin_labels.append(lbl)

    def _posicionar_etiqueta_pin(self, lbl, pin, w, h):
        """Sitúa la etiqueta fuera del dibujo siempre que sea posible."""
        fm = QFontMetrics(lbl.font())

        tw = (
            fm.horizontalAdvance(pin.nombre)
            if hasattr(fm, "horizontalAdvance")
            else fm.width(pin.nombre)
        )

        th = fm.height()
        margen = 5

        if pin.y <= 0:
            lbl.setPos(
                pin.x - tw / 2.0,
                pin.y - th - margen,
            )

        elif pin.y >= h:
            lbl.setPos(
                pin.x - tw / 2.0,
                pin.y + margen,
            )

        elif pin.x <= 0:
            lbl.setPos(
                pin.x - tw - margen,
                pin.y - th / 2.0,
            )

        elif pin.x >= w:
            lbl.setPos(
                pin.x + margen,
                pin.y - th / 2.0,
            )

        else:
            lbl.setPos(
                w + margen,
                pin.y - th / 2.0,
            )

    def actualizar_texto_etiqueta(self):
        traducciones_tipo = {
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

        traducciones_valor = {
            "es": {
                "100 Ω": "100 Ω",
                "220 Ω": "220 Ω",
                "330 Ω": "330 Ω",
                "1 KΩ": "1 KΩ",
                "2.2 KΩ": "2.2 KΩ",
                "4.7 KΩ": "4.7 KΩ",
                "10 KΩ": "10 KΩ",
                "47 KΩ": "47 KΩ",
                "100 KΩ": "100 KΩ",

                "10 pF": "10 pF",
                "100 pF": "100 pF",
                "1 nF": "1 nF",
                "10 nF": "10 nF",
                "100 nF": "100 nF",
                "1 uF": "1 uF",
                "10 uF": "10 uF",
                "100 uF": "100 uF",

                "10 μH": "10 μH",
                "100 μH": "100 μH",
                "1 mH": "1 mH",

                "1N4148": "1N4148",
                "1N4001": "1N4001",
                "1N4007": "1N4007",
                "1N5819": "1N5819",

                "Zener 3.3V": "Zener 3.3V",
                "Zener 5.1V": "Zener 5.1V",
                "Zener 9.1V": "Zener 9.1V",
                "Zener 12V": "Zener 12V",

                "BC547 (NPN genérico)": "BC547 (NPN genérico)",
                "BC557 (PNP genérico)": "BC557 (PNP genérico)",
                "2N2222": "2N2222",
                "2N3904": "2N3904",
                "MOSFET IRFZ44N": "MOSFET IRFZ44N",

                "NE555 (Temporizador)": "NE555 (Temporizador)",
                "LM7805 (Regulador 5V)": "LM7805 (Regulador 5V)",
                "LM358 (Op-Amp)": "LM358 (Op-Amp)",
                "ATmega328P (Micro)": "ATmega328P (Micro)",

                "LED Rojo": "LED Rojo",
                "LED Verde": "LED Verde",
                "LED Azul": "LED Azul",
                "LED Amarillo": "LED Amarillo",
                "LED Blanco": "LED Blanco",

                "Activo 5V": "Activo 5V",
                "Activo 12V": "Activo 12V",
                "Pasivo": "Pasivo",

                "Cátodo Común": "Cátodo Común",
                "Ánodo Común": "Ánodo Común",

                "Normal Abierto (NO)": "Normal Abierto (NO)",

                "Deslizante SPDT (1 polo, 2 tiros)":
                    "Deslizante SPDT (1 polo, 2 tiros)",

                "Pila 1.5V (AA/AAA)": "Pila 1.5V (AA/AAA)",
                "Batería 9V": "Batería 9V",
                "Pack 5V (USB)": "Pack 5V (USB)",
                "Li-ion 3.7V": "Li-ion 3.7V",

                "GND (Tierra)": "GND (Tierra)",

                "Clema de tornillo (2 pines)": "Clema de tornillo (2 pines)",
                "Pin Header macho (1x2)": "Pin Header macho (1x2)",
                "Pin Header macho (1x4)": "Pin Header macho (1x4)",

                "M2.5": "M2.5",
                "M3": "M3",
                "M4": "M4",
            },

            "en": {
                "100 Ω": "100 Ω",
                "220 Ω": "220 Ω",
                "330 Ω": "330 Ω",
                "1 KΩ": "1 KΩ",
                "2.2 KΩ": "2.2 KΩ",
                "4.7 KΩ": "4.7 KΩ",
                "10 KΩ": "10 KΩ",
                "47 KΩ": "47 KΩ",
                "100 KΩ": "100 KΩ",

                "10 pF": "10 pF",
                "100 pF": "100 pF",
                "1 nF": "1 nF",
                "10 nF": "10 nF",
                "100 nF": "100 nF",
                "1 uF": "1 uF",
                "10 uF": "10 uF",
                "100 uF": "100 uF",

                "10 μH": "10 μH",
                "100 μH": "100 μH",
                "1 mH": "1 mH",

                "1N4148": "1N4148",
                "1N4001": "1N4001",
                "1N4007": "1N4007",
                "1N5819": "1N5819",

                "Zener 3.3V": "Zener 3.3V",
                "Zener 5.1V": "Zener 5.1V",
                "Zener 9.1V": "Zener 9.1V",
                "Zener 12V": "Zener 12V",

                "BC547 (NPN genérico)": "BC547 (generic NPN)",
                "BC557 (PNP genérico)": "BC557 (generic PNP)",
                "2N2222": "2N2222",
                "2N3904": "2N3904",
                "MOSFET IRFZ44N": "MOSFET IRFZ44N",

                "NE555 (Temporizador)": "NE555 (Timer)",
                "LM7805 (Regulador 5V)": "LM7805 (5V Regulator)",
                "LM358 (Op-Amp)": "LM358 (Op-Amp)",
                "ATmega328P (Micro)": "ATmega328P (Microcontroller)",

                "LED Rojo": "Red LED",
                "LED Verde": "Green LED",
                "LED Azul": "Blue LED",
                "LED Amarillo": "Yellow LED",
                "LED Blanco": "White LED",

                "Activo 5V": "Active 5V",
                "Activo 12V": "Active 12V",
                "Pasivo": "Passive",

                "Cátodo Común": "Common Cathode",
                "Ánodo Común": "Common Anode",

                "Normal Abierto (NO)": "Normally Open (NO)",

                "Deslizante SPDT (1 polo, 2 tiros)":
                    "SPDT Slide Switch (1 pole, 2 throws)",

                "Pila 1.5V (AA/AAA)": "1.5V Battery (AA/AAA)",
                "Batería 9V": "9V Battery",
                "Pack 5V (USB)": "5V Pack (USB)",
                "Li-ion 3.7V": "Li-ion 3.7V",

                "+5V": "+5V",
                "+12V": "+12V",
                "+3.3V": "+3.3V",
                "GND (Tierra)": "GND (Ground)",

                "Clema de tornillo (2 pines)": "Screw Terminal (2 pins)",
                "Pin Header macho (1x2)": "Male Pin Header (1x2)",
                "Pin Header macho (1x4)": "Male Pin Header (1x4)",

                "M2.5": "M2.5",
                "M3": "M3",
                "M4": "M4",
            },
        }

        lang = getattr(
            self.scene(),
            "lang",
            "es"
        ) if self.scene() else "es"

        tipo_mostrado = traducciones_tipo.get(
            lang,
            traducciones_tipo["es"]
        ).get(
            self.tipo,
            self.tipo
        )

        valor_mostrado = traducciones_valor.get(
            lang,
            traducciones_valor["es"]
        ).get(
            self.valor,
            self.valor
        )

        self.label.setPlainText(
            f"{self.ref_id}: {tipo_mostrado}\n{valor_mostrado}"
        )

        self.label.setFont(
            QFont("sans-serif", 9, QFont.Bold)
        )

        modo_oscuro = (
            getattr(self.scene(), "modo_oscuro", False)
            if self.scene()
            else False
        )

        color_texto = (
            QColor("#ffffff")
            if modo_oscuro
            else QColor("#000000")
        )

        color_pin = (
            QColor("#67e8f9")
            if modo_oscuro
            else QColor("#0369a1")
        )

        self.label.setDefaultTextColor(color_texto)

        for pin, lbl in zip(
            self.pines_logicos,
            self.pin_labels
        ):
            lbl.setPlainText(pin.nombre)
            lbl.setFont(
                QFont("sans-serif", 9, QFont.Bold)
            )
            lbl.setDefaultTextColor(color_pin)

            self._posicionar_etiqueta_pin(
                lbl,
                pin,
                self.rect().width(),
                self.rect().height()
            )

            lbl.setZValue(35)

    def obtener_puntos_conexion(self):
        return [
            self.mapToScene(QPointF(p.x, p.y))
            for p in self.pines_logicos
        ]

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)

        modo_oscuro = (
            getattr(self.scene(), "modo_oscuro", False)
            if self.scene()
            else False
        )

        color_trazo = (
            QColor("#38bdf8")
            if modo_oscuro
            else QColor("#0f172a")
        )

        if getattr(self, "is_highlighted", False):
            color_trazo = QColor("#facc15")
            pen = QPen(color_trazo, 4)

        elif self.isSelected():
            color_trazo = QColor("#2563eb")
            pen = QPen(color_trazo, 2)

        else:
            pen = QPen(color_trazo, 2)

        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)

        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        rect = self.boundingRect()
        w = rect.width()
        h = rect.height()
        cy = h / 2

        if self.tipo == "Resistor":
            painter.drawLine(
                QPointF(0, cy),
                QPointF(20, cy),
            )
            painter.drawLine(
                QPointF(60, cy),
                QPointF(80, cy),
            )

            painter.setBrush(
                QColor("#1e293b")
                if modo_oscuro
                else QColor("#ffffff")
            )

            painter.drawRect(
                20,
                int(cy - 8),
                40,
                16,
            )

        elif self.tipo == "Capacitor":
            painter.drawLine(
                QPointF(0, cy),
                QPointF(35, cy),
            )
            painter.drawLine(
                QPointF(45, cy),
                QPointF(80, cy),
            )
            painter.drawLine(
                QPointF(35, cy - 12),
                QPointF(35, cy + 12),
            )
            painter.drawLine(
                QPointF(45, cy - 12),
                QPointF(45, cy + 12),
            )

        elif self.tipo == "Inductor / Bobina":
            painter.drawLine(
                QPointF(0, cy),
                QPointF(20, cy),
            )
            painter.drawLine(
                QPointF(60, cy),
                QPointF(80, cy),
            )

            path = QPainterPath()
            path.moveTo(20, cy)
            path.arcTo(20, cy - 10, 13.3, 20, 180, -180)
            path.arcTo(33.3, cy - 10, 13.3, 20, 180, -180)
            path.arcTo(46.6, cy - 10, 13.3, 20, 180, -180)

            painter.drawPath(path)

        elif self.tipo in ["Diodo", "Zener", "LED"]:
            painter.drawLine(
                QPointF(0, cy),
                QPointF(30, cy),
            )
            painter.drawLine(
                QPointF(50, cy),
                QPointF(80, cy),
            )

            path = QPainterPath()
            path.moveTo(30, cy - 12)
            path.lineTo(50, cy)
            path.lineTo(30, cy + 12)
            path.closeSubpath()

            painter.setBrush(QBrush(color_trazo))
            painter.drawPath(path)
            painter.setBrush(Qt.NoBrush)

            painter.drawLine(
                QPointF(50, cy - 12),
                QPointF(50, cy + 12),
            )

            if self.tipo == "Zener":
                painter.drawLine(
                    QPointF(50, cy - 12),
                    QPointF(55, cy - 12),
                )
                painter.drawLine(
                    QPointF(50, cy + 12),
                    QPointF(45, cy + 12),
                )

            elif self.tipo == "LED":
                painter.drawLine(
                    QPointF(40, cy - 15),
                    QPointF(50, cy - 25),
                )
                painter.drawLine(
                    QPointF(47, cy - 25),
                    QPointF(50, cy - 25),
                )
                painter.drawLine(
                    QPointF(50, cy - 22),
                    QPointF(50, cy - 25),
                )
                painter.drawLine(
                    QPointF(45, cy - 15),
                    QPointF(55, cy - 25),
                )
                painter.drawLine(
                    QPointF(52, cy - 25),
                    QPointF(55, cy - 25),
                )
                painter.drawLine(
                    QPointF(55, cy - 22),
                    QPointF(55, cy - 25),
                )

        elif self.tipo == "Transistor":
            painter.drawEllipse(
                10,
                5,
                50,
                50,
            )

            painter.drawLine(
                QPointF(0, cy),
                QPointF(25, cy),
            )

            painter.drawLine(
                QPointF(25, cy - 15),
                QPointF(25, cy + 15),
            )

            painter.drawLine(
                QPointF(25, cy - 5),
                QPointF(w, 10),
            )

            painter.drawLine(
                QPointF(25, cy + 5),
                QPointF(w, h - 10),
            )

            p_arrow = QPainterPath()
            p_arrow.moveTo(w - 2, h - 12)
            p_arrow.lineTo(w - 12, h - 10)
            p_arrow.lineTo(w - 8, h - 18)
            p_arrow.closeSubpath()

            painter.setBrush(QBrush(color_trazo))
            painter.drawPath(p_arrow)
            painter.setBrush(Qt.NoBrush)

        elif self.tipo == "Circuito Integrado":
            painter.setBrush(QColor("#1e293b"))
            painter.drawRect(
                10,
                0,
                int(w - 20),
                int(h),
            )

            painter.setBrush(QColor("#334155"))
            painter.drawArc(
                int(w / 2 - 6),
                -6,
                12,
                12,
                180 * 16,
                -180 * 16,
            )

            painter.setBrush(Qt.NoBrush)

            for y in [20, 40, 60]:
                painter.drawLine(
                    QPointF(0, y),
                    QPointF(10, y),
                )
                painter.drawLine(
                    QPointF(w - 10, y),
                    QPointF(w, y),
                )

        elif self.tipo == "Batería / Pila":
            painter.drawLine(
                QPointF(0, cy),
                QPointF(35, cy),
            )

            painter.drawLine(
                QPointF(45, cy),
                QPointF(80, cy),
            )

            painter.drawLine(
                QPointF(35, cy - 16),
                QPointF(35, cy + 16),
            )

            painter.setPen(
                QPen(color_trazo, 4)
            )

            painter.drawLine(
                QPointF(45, cy - 8),
                QPointF(45, cy + 8),
            )

            painter.setPen(pen)

        elif self.tipo == "Pulsador / Push Button":
            painter.drawLine(
                QPointF(0, cy),
                QPointF(25, cy),
            )

            painter.drawLine(
                QPointF(55, cy),
                QPointF(80, cy),
            )

            painter.drawEllipse(
                22,
                int(cy - 4),
                8,
                8,
            )

            painter.drawEllipse(
                50,
                int(cy - 4),
                8,
                8,
            )

            painter.drawLine(
                QPointF(25, cy - 12),
                QPointF(55, cy - 12),
            )

            painter.drawLine(
                QPointF(40, cy - 12),
                QPointF(40, cy - 18),
            )

        elif self.tipo == "Terminal Alimentación":
            path = QPainterPath()
            path.moveTo(w / 2, h)
            path.lineTo(w / 2, h / 2 + 5)
            path.lineTo(w / 2 - 10, h / 2 + 5)
            path.lineTo(w / 2, 0)
            path.lineTo(w / 2 + 10, h / 2 + 5)
            path.lineTo(w / 2, h / 2 + 5)

            painter.setBrush(color_trazo)
            painter.drawPath(path)
            painter.setBrush(Qt.NoBrush)

        elif self.tipo == "Agujero de Montaje":
            painter.setBrush(
                QColor("#cbd5e1")
                if modo_oscuro
                else QColor("#94a3b8")
            )
            painter.drawEllipse(
                5,
                5,
                30,
                30,
            )

            painter.setBrush(
                QColor("#0f172a")
                if modo_oscuro
                else QColor("#f8fafc")
            )

            painter.drawEllipse(
                12,
                12,
                16,
                16,
            )

            painter.setBrush(Qt.NoBrush)
            painter.setPen(
                QPen(color_trazo, 1, Qt.DashLine)
            )

            painter.drawLine(
                QPointF(20, -5),
                QPointF(20, 45),
            )

            painter.drawLine(
                QPointF(-5, 20),
                QPointF(45, 20),
            )

            painter.setPen(pen)

        elif self.tipo == "Display 7 Segmentos":
            painter.setBrush(
                QBrush(QColor("#18181b"))
            )

            painter.drawRect(
                0,
                0,
                int(w),
                int(h),
            )

            painter.setPen(
                QPen(
                    QColor("#ef4444"),
                    5,
                    Qt.SolidLine,
                    Qt.RoundCap,
                )
            )

            painter.drawLine(20, 20, 40, 20)
            painter.drawLine(40, 20, 40, 45)
            painter.drawLine(40, 45, 40, 70)
            painter.drawLine(20, 70, 40, 70)
            painter.drawLine(20, 45, 20, 70)
            painter.drawLine(20, 20, 20, 45)
            painter.drawLine(20, 45, 40, 45)
            painter.drawPoint(50, 70)

            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

        elif self.tipo == "Conector de Placa":
            painter.setBrush(
                QBrush(
                    QColor("#16a34a")
                    if modo_oscuro
                    else QColor("#22c55e")
                )
            )

            painter.setPen(
                QPen(QColor("#14532d"), 1.5)
            )

            painter.drawRoundedRect(
                0,
                0,
                int(w),
                int(h),
                5,
                5,
            )

            for p in self.pines_logicos:
                center = QPointF(p.x, p.y)

                painter.setPen(
                    QPen(QColor("#e2e8f0"), 1.5)
                )

                painter.setBrush(
                    QBrush(QColor("#f8fafc"))
                )

                painter.drawEllipse(
                    center,
                    7.0,
                    7.0,
                )

                painter.setPen(Qt.NoPen)
                painter.setBrush(
                    QBrush(QColor("#0f172a"))
                )

                painter.drawEllipse(
                    center,
                    3.2,
                    3.2,
                )

            painter.setBrush(Qt.NoBrush)
            painter.setPen(pen)

        else:
            painter.setBrush(
                QColor("#1e293b")
                if modo_oscuro
                else QColor("#ffffff")
            )

            painter.drawRect(
                0,
                0,
                int(w),
                int(h),
            )

            painter.drawLine(
                QPointF(0, cy),
                QPointF(10, cy),
            )

            painter.drawLine(
                QPointF(w - 10, cy),
                QPointF(w, cy),
            )

        if getattr(self, "is_highlighted", False):
            pin_color = QColor("#facc15")
        elif modo_oscuro:
            pin_color = QColor("#67e8f9")
        else:
            pin_color = QColor("#dc2626")

        pen_pin = QPen(pin_color, 1.8)
        brush_pin = QBrush(QColor("#f8fafc"))

        for p in self.pines_logicos:
            center = QPointF(p.x, p.y)

            painter.setPen(pen_pin)
            painter.setBrush(brush_pin)

            painter.drawEllipse(
                center,
                4.5,
                4.5,
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(
                QBrush(QColor("#0f172a"))
            )

            painter.drawEllipse(
                center,
                2.0,
                2.0,
            )

    def itemChange(self, change, value):
        if (
            change == QGraphicsItem.ItemPositionChange
            and self.scene()
        ):
            new_pos = snap_to_grid(value)
            self.scene().actualizar_indicadores_conexion()
            return new_pos

        return super().itemChange(change, value)

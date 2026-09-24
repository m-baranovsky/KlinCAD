import os
import sys

from PyQt5.QtWidgets import QApplication

from klincad.editor.window import EditorCircuito


def main():
    # En GNOME/Wayland forzamos el backend nativo de Qt.
    # En X11 y otros entornos no modificamos nada.
    if (
        sys.platform.startswith("linux")
        and os.environ.get("XDG_SESSION_TYPE") == "wayland"
    ):
        os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

    app = QApplication(sys.argv)
    ventana = EditorCircuito()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

import sys

from PyQt5.QtWidgets import QApplication

from klincad.editor.window import EditorCircuito


def main():
    app = QApplication(sys.argv)
    ventana = EditorCircuito()
    ventana.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

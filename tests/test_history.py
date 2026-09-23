from PyQt5.QtWidgets import QGraphicsScene

from klincad.editor.history import GestorHistorial


class EditorFalso(GestorHistorial):
    def __init__(self):
        self.scene = QGraphicsScene()
        self.panel_capas = None
        self.proyecto_activo = False
        self.marcas_limpiadas = False

        self.inicializar_historial()

    def limpiar_marcas_drc(self):
        self.marcas_limpiadas = True


def test_inicializar_historial():
    editor = EditorFalso()

    assert editor.historial_undo == []
    assert editor.historial_redo == []
    assert editor.estado_guardado is None
    assert editor._estado_accion_inicio is None


def test_guardar_estado_crea_entrada_de_undo():
    editor = EditorFalso()

    editor.guardar_estado()

    assert len(editor.historial_undo) == 1
    assert editor.historial_redo == []


def test_deshacer_y_rehacer():
    editor = EditorFalso()

    editor.guardar_estado()

    estado_inicial_undo = len(editor.historial_undo)

    editor.guardar_estado()

    assert len(editor.historial_undo) == estado_inicial_undo + 1

    editor.deshacer()

    assert len(editor.historial_redo) >= 1

    editor.rehacer()

    assert len(editor.historial_undo) >= 1

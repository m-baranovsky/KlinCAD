import json

from klincad.services.project_io import abrir_proyecto, guardar_proyecto


class EditorFalso:
    def __init__(self, datos=None):
        self.datos = datos or {"version": 1, "items": []}

    def serializar_escena(self):
        return json.dumps(self.datos)

    def cargar_estado(self, estado):
        self.datos = json.loads(estado)


def test_guardar_y_abrir_proyecto(tmp_path):
    archivo = tmp_path / "prueba.klincad"

    editor_original = EditorFalso({
        "version": 1,
        "items": [
            {
                "tipo": "Componente",
                "valor": "10k",
            }
        ],
    })

    assert guardar_proyecto(editor_original, str(archivo))
    assert archivo.exists()

    editor_nuevo = EditorFalso()

    assert abrir_proyecto(editor_nuevo, str(archivo))
    assert editor_nuevo.datos == editor_original.datos


def test_guardar_agrega_extension_klincad(tmp_path):
    archivo = tmp_path / "proyecto"

    editor = EditorFalso()

    assert guardar_proyecto(editor, str(archivo))

    assert (tmp_path / "proyecto.klincad").exists()

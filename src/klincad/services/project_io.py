# =============================================================================
# KlinCAD - Lectura y escritura de proyectos
# =============================================================================

import json
import os


PROJECT_EXTENSIONS = (
    ".klincad",
    ".json",
)


def guardar_proyecto(editor, path):
    """
    Guarda el estado actual del editor en formato JSON.

    El formato .klincad es JSON legible para facilitar
    depuración y colaboración.
    """
    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(path)
    )

    if not path.lower().endswith(
        PROJECT_EXTENSIONS
    ):
        path += ".klincad"

    try:
        data = json.loads(
            editor.serializar_escena()
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as archivo:
            json.dump(
                data,
                archivo,
                indent=4,
                ensure_ascii=False,
            )

        return True

    except Exception:
        return False


def abrir_proyecto(editor, path):
    """
    Lee un proyecto y reconstruye la escena mediante
    el cargador de estados del editor.
    """
    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(path)
    )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as archivo:
            data = json.load(archivo)

        editor.cargar_estado(
            json.dumps(
                data,
                ensure_ascii=False,
            )
        )

        return True

    except Exception:
        return False

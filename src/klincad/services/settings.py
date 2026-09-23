# =============================================================================
# KlinCAD - Preferencias persistentes
# =============================================================================

from PyQt5.QtCore import QSettings


ORGANIZATION_NAME = "KlinCAD"
APPLICATION_NAME = "KlinCAD"


def crear_configuracion():
    """
    Crea la instancia central de QSettings de KlinCAD.
    """
    return QSettings(
        ORGANIZATION_NAME,
        APPLICATION_NAME,
    )


def obtener_mostrar_guias_inicio(configuracion=None):
    """
    Obtiene la preferencia de mostrar la guía al iniciar.

    Por defecto la guía se muestra.
    """
    if configuracion is None:
        configuracion = crear_configuracion()

    return configuracion.value(
        "interfaz/mostrar_guias_inicio",
        True,
        type=bool,
    )


def guardar_mostrar_guias_inicio(
    mostrar,
    configuracion=None,
):
    """
    Guarda la preferencia de mostrar la guía al iniciar.
    """
    if configuracion is None:
        configuracion = crear_configuracion()

    configuracion.setValue(
        "interfaz/mostrar_guias_inicio",
        bool(mostrar),
    )

    configuracion.sync()


def obtener_idioma(configuracion=None):
    """
    Obtiene el idioma guardado.

    Si todavía no existe una preferencia,
    se utiliza español.
    """
    if configuracion is None:
        configuracion = crear_configuracion()

    return configuracion.value(
        "interfaz/idioma",
        "es",
    )


def guardar_idioma(
    idioma,
    configuracion=None,
):
    """
    Guarda el idioma seleccionado.
    """
    if configuracion is None:
        configuracion = crear_configuracion()

    if idioma not in ("es", "en"):
        idioma = "es"

    configuracion.setValue(
        "interfaz/idioma",
        idioma,
    )

    configuracion.sync()

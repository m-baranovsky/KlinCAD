# =============================================================================
# KlinCAD - Exportación PNG / PDF
# =============================================================================

import os
import math

from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import (
    QBrush,
    QImage,
    QPainter,
    QPageSize,
    QPdfWriter,
)

from klincad.items.markers import (
    FlechaError,
    IndicadorConexion,
)


def bbox_exportable(editor):
    """
    Obtiene el bounding box real del diseño visible.

    Se excluyen los indicadores visuales del DRC y de conexión
    para que no alteren el encuadre de la exportación.
    """
    rect = QRectF()
    inicializado = False

    excluidos = (
        FlechaError,
        IndicadorConexion,
    )

    for item in editor.scene.items():

        if isinstance(item, excluidos):
            continue

        if not item.isVisible():
            continue

        item_rect = item.sceneBoundingRect()

        if (
            not item_rect.isValid()
            or item_rect.isNull()
        ):
            continue

        if not inicializado:
            rect = item_rect
            inicializado = True
        else:
            rect = rect.united(
                item_rect
            )

    if not inicializado:
        return QRectF(
            -50,
            -50,
            100,
            100,
        )

    return rect


def ocultar_indicadores_exportacion(editor):
    """
    Oculta temporalmente las marcas DRC/conexión.
    """
    estados = []

    for item in editor.scene.items():
        if (
            isinstance(
                item,
                (
                    FlechaError,
                    IndicadorConexion,
                ),
            )
            and item.isVisible()
        ):
            estados.append(
                (item, True)
            )

            item.setVisible(False)

    return estados


def restaurar_indicadores_exportacion(
    editor,
    estados,
):
    """
    Restaura la visibilidad previa de los indicadores.
    """
    for item, visible in estados:

        if item.scene() is editor.scene:
            item.setVisible(
                visible
            )


def render_exportacion(
    editor,
    source_rect,
    scale=2.0,
):
    """
    Renderiza el diseño a QImage.

    Se utiliza un render intermedio para evitar problemas
    con coordenadas negativas de la escena.
    """
    width = max(
        1,
        int(
            math.ceil(
                source_rect.width()
                * scale
            )
        ),
    )

    height = max(
        1,
        int(
            math.ceil(
                source_rect.height()
                * scale
            )
        ),
    )

    image = QImage(
        width,
        height,
        QImage.Format_ARGB32_Premultiplied,
    )

    image.fill(
        Qt.transparent
    )

    original_bg = (
        editor.scene.backgroundBrush()
    )

    estados = (
        ocultar_indicadores_exportacion(
            editor
        )
    )

    seleccionados = list(
        editor.scene.selectedItems()
    )

    painter = QPainter(image)

    try:
        painter.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform,
            True,
        )

        editor.scene.clearSelection()

        editor.scene.setBackgroundBrush(
            QBrush(Qt.NoBrush)
        )

        editor.scene.render(
            painter,
            QRectF(
                0,
                0,
                width,
                height,
            ),
            source_rect,
        )

    finally:
        painter.end()

        editor.scene.setBackgroundBrush(
            original_bg
        )

        restaurar_indicadores_exportacion(
            editor,
            estados,
        )

        for item in seleccionados:

            if item.scene() is editor.scene:
                item.setSelected(True)

        editor.scene.update()

    return image


def exportar_png(
    editor,
    path,
):
    """
    Exporta el diseño completo a PNG.

    Devuelve True si el archivo fue creado correctamente.
    """
    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(path)
    )

    if not path.lower().endswith(
        ".png"
    ):
        path += ".png"

    rect = bbox_exportable(
        editor
    ).adjusted(
        -20,
        -20,
        20,
        20,
    )

    # Evita imágenes gigantes cuando el diseño ocupa
    # una gran extensión de la escena.
    max_dimension = 8000.0

    max_side = max(
        rect.width(),
        rect.height(),
        1.0,
    )

    scale = min(
        2.0,
        max_dimension / max_side,
    )

    scale = max(
        scale,
        0.5,
    )

    image = render_exportacion(
        editor,
        rect,
        scale=scale,
    )

    if image.isNull():
        return False

    guardado = image.save(
        path,
        "PNG",
    )

    existe = os.path.isfile(
        path
    )

    tiene_datos = (
        existe
        and os.path.getsize(path) > 0
    )

    return (
        guardado
        and tiene_datos
    )


def exportar_pdf(
    editor,
    path,
):
    """
    Exporta el diseño completo a una página A4.

    Devuelve True si el archivo PDF fue generado.
    """
    if not path:
        return False

    path = os.path.abspath(
        os.path.expanduser(path)
    )

    if not path.lower().endswith(
        ".pdf"
    ):
        path += ".pdf"

    rect = bbox_exportable(
        editor
    ).adjusted(
        -20,
        -20,
        20,
        20,
    )

    image = render_exportacion(
        editor,
        rect,
        scale=2.0,
    )

    if image.isNull():
        return False

    writer = QPdfWriter(
        path
    )

    writer.setPageSize(
        QPageSize(QPageSize.A4)
    )

    writer.setResolution(
        144
    )

    painter = QPainter(
        writer
    )

    try:
        painter.setRenderHint(
            QPainter.SmoothPixmapTransform,
            True,
        )

        page_w = float(
            writer.width()
        )

        page_h = float(
            writer.height()
        )

        margin = min(
            56.0,
            min(
                page_w,
                page_h,
            ) * 0.06,
        )

        target = QRectF(
            margin,
            margin,
            max(
                1.0,
                page_w - margin * 2,
            ),
            max(
                1.0,
                page_h - margin * 2,
            ),
        )

        factor = min(
            target.width()
            / max(
                1,
                image.width(),
            ),
            target.height()
            / max(
                1,
                image.height(),
            ),
        )

        draw_w = (
            image.width()
            * factor
        )

        draw_h = (
            image.height()
            * factor
        )

        draw_rect = QRectF(
            target.center().x()
            - draw_w / 2,

            target.center().y()
            - draw_h / 2,

            draw_w,
            draw_h,
        )

        painter.drawImage(
            draw_rect,
            image,
        )

    finally:
        painter.end()

    existe = os.path.isfile(
        path
    )

    tiene_datos = (
        existe
        and os.path.getsize(path) > 0
    )

    return tiene_datos

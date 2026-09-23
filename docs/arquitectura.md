# Arquitectura de KlinCAD

## 1. Objetivo

KlinCAD se organiza por módulos para evitar que toda la aplicación dependa de un único archivo.

La arquitectura separa:

- lógica del editor;
- elementos gráficos;
- interfaz;
- servicios;
- utilidades;
- pruebas.

Esto facilita el mantenimiento y la incorporación de nuevas funcionalidades.

---

## 2. Estructura

```text
src/
└── klincad/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── i18n.py
    │
    ├── editor/
    │   ├── __init__.py
    │   ├── window.py
    │   ├── scene.py
    │   ├── layers.py
    │   ├── history.py
    │   └── drc.py
    │
    ├── items/
    │   ├── __init__.py
    │   ├── component.py
    │   ├── track.py
    │   ├── node.py
    │   ├── mesh.py
    │   └── markers.py
    │
    ├── ui/
    │   ├── __init__.py
    │   ├── dialogs.py
    │   ├── splash.py
    │   ├── toolbars.py
    │   └── viewer3d.py
    │
    ├── services/
    │   ├── __init__.py
    │   ├── project_io.py
    │   ├── export.py
    │   └── settings.py
    │
    └── utils/
        ├── __init__.py
        └── geometry.py

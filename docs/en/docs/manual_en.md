# KlinCAD User Manual

## 1. Introduction

KlinCAD is a graphical editor for designing electronic circuits and organizing their connections on a working scene.

The interface allows users to place components, create tracks, use nodes and meshes, manage layers, check connection errors and export designs.

---

## 2. Creating a Project

When KlinCAD starts, a new project can be created from the initial screen.

It can also be created using:

**Project → New Project**

The central working area contains the scene where circuit elements are placed.

---

## 3. Selection Tool

The **Pointer** tool allows circuit elements to be selected and moved.

Components can be selected individually and repositioned inside the scene.

The editor uses a grid to help with alignment.

---

## 4. Components

The **Components** menu provides several electronic elements, including:

- Resistors.
- Capacitors.
- Inductors.
- Diodes.
- Zener diodes.
- Transistors.
- Integrated circuits.
- LEDs.
- Buzzers.
- Displays.
- Push buttons.
- Switches.
- Batteries.
- Terminals.
- Connectors.
- Mounting holes.

Components provide terminals that can be used as connection points.

---

## 5. Tracks

The **Track** tool creates connections between terminals.

Tracks can be moved and modified through their endpoints.

The grid is used to help with routing.

Tracks belong to different design layers.

---

## 6. Nodes

The **Node** tool adds explicit connection points.

Nodes can be moved and selected like other graphical elements.

---

## 7. Meshes

The **Mesh** tool creates a rectangular reference area on the scene.

Meshes are intended as visual and organizational elements.

---

## 8. Layers

The layer panel controls the visibility of the different circuit layers.

Available layers include:

- Top Copper.
- Bottom Copper.
- General / Jumpers.
- Power / Notes.

The panel allows layer visibility to be changed and controls the ordering of layers.

---

## 9. Rotation

Elements that support rotation use their own rotation origin.

The:

**R**

key rotates the selected element.

---

## 10. Undo and Redo

KlinCAD provides an action history.

Main shortcuts:

- **Ctrl + Z**: undo.
- **Ctrl + Y**: redo.

---

## 11. Copy, Cut and Paste

Available shortcuts:

- **Ctrl + C**: copy.
- **Ctrl + X**: cut.
- **Ctrl + V**: paste.

The following keys can be used to remove selected elements:

**Delete** or **Backspace**

---

## 12. Saving and Opening Projects

Projects use the:

`.klincad`

extension.

The **Project** menu provides options to:

- Create a new project.
- Open an existing project.
- Save the current project.

---

## 13. DRC Check

The **DRC** tool checks for connection problems.

When floating or disconnected pins are detected, KlinCAD can visually mark the problematic locations.

After fixing the issues, the markers can be removed.

---

## 14. Isometric Viewer

The **2.5D Isometric Viewer** provides an alternative visual representation of the design.

It displays components and tracks using an isometric perspective.

---

## 15. Export

The design can be exported to:

- PNG.
- PDF.

The export process attempts to use the area occupied by the design elements while excluding DRC visual markers.

---

## 16. Electronic Calculator

The **Utilities → Electronic Calculator** option opens the integrated calculator.

It is intended for quick electronics-related calculations.

---

## 17. Language

KlinCAD provides:

- Spanish.
- English.

The language can be changed from the corresponding menu.

---

## 18. Dark Mode

The interface includes an option to enable or disable dark mode.

---

## 19. Help

The **Help** menu provides guidance information and access to the project community.

---

## 20. Recommended Workflow

A basic workflow is:

1. Create a project.
2. Place the components.
3. Arrange components using the grid.
4. Draw tracks between terminals.
5. Add nodes when needed.
6. Check the layers.
7. Run DRC.
8. Fix the reported connections.
9. Save the project.
10. Export the design when required.

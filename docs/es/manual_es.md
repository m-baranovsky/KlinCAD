# Manual de usuario de KlinCAD

## 1. Introducción

KlinCAD es un editor gráfico para diseñar circuitos electrónicos y organizar sus conexiones sobre una escena de trabajo.

La interfaz permite colocar componentes, crear pistas, utilizar nodos y mallas, trabajar con capas, revisar errores de conexión y exportar el diseño.

---

## 2. Crear un proyecto

Al iniciar KlinCAD se puede comenzar un proyecto nuevo desde la pantalla inicial.

También se puede utilizar:

**Proyecto → Nuevo Proyecto**

El área central de trabajo contiene la escena donde se colocan los elementos del circuito.

---

## 3. Herramienta de selección

La herramienta **Puntero** permite seleccionar y mover los elementos del circuito.

Los componentes pueden seleccionarse individualmente y desplazarse dentro de la escena.

El editor utiliza una cuadrícula para facilitar la alineación.

---

## 4. Componentes

Desde el menú **Componentes** se pueden agregar diferentes elementos electrónicos.

Entre ellos se encuentran:

- Resistencias.
- Capacitores.
- Inductores.
- Diodos.
- Diodos Zener.
- Transistores.
- Circuitos integrados.
- LEDs.
- Buzzers.
- Displays.
- Pulsadores.
- Interruptores.
- Baterías.
- Terminales.
- Conectores.
- Agujeros de fijación.

Los componentes disponen de terminales que pueden utilizarse como puntos de conexión.

---

## 5. Pistas

La herramienta **Pista** permite crear conexiones entre terminales.

Las pistas pueden desplazarse y modificarse desde sus extremos.

El sistema utiliza la cuadrícula para facilitar el trazado.

Las pistas pertenecen a diferentes capas del diseño.

---

## 6. Nodos

La herramienta **Nodo** permite agregar puntos explícitos de conexión.

Los nodos pueden moverse y seleccionarse como otros elementos gráficos.

---

## 7. Mallas

La herramienta **Malla** permite crear un área rectangular de referencia sobre la escena.

Las mallas sirven como elemento visual y de organización del diseño.

---

## 8. Capas

El panel de capas permite controlar la visualización de las distintas capas del circuito.

Las capas disponibles incluyen:

- Top Copper.
- Bottom Copper.
- General / Jumpers.
- Power / Notes.

Desde el panel se puede cambiar la visibilidad de las pistas y modificar el orden de las capas.

---

## 9. Rotación

Los elementos compatibles con rotación utilizan un origen de rotación propio.

La tecla:

**R**

permite rotar el elemento seleccionado.

---

## 10. Deshacer y rehacer

KlinCAD incorpora historial de acciones.

Atajos principales:

- **Ctrl + Z**: deshacer.
- **Ctrl + Y**: rehacer.

---

## 11. Copiar, cortar y pegar

Atajos disponibles:

- **Ctrl + C**: copiar.
- **Ctrl + X**: cortar.
- **Ctrl + V**: pegar.

También se puede utilizar:

**Delete** o **Backspace**

para eliminar elementos seleccionados.

---

## 12. Guardar y abrir proyectos

Los proyectos utilizan la extensión:

`.klincad`

Desde el menú **Proyecto** se puede:

- Crear un proyecto nuevo.
- Abrir un proyecto existente.
- Guardar el proyecto actual.

---

## 13. Comprobación DRC

La herramienta **DRC** comprueba problemas de conexión.

Cuando se detectan pines flotantes o desconectados, KlinCAD puede marcar visualmente las posiciones problemáticas mediante indicadores.

Después de corregir los problemas, las marcas pueden eliminarse.

---

## 14. Visor isométrico

El **Visor 2.5D Isométrico** proporciona una representación visual alternativa del diseño.

Permite observar componentes y pistas desde una perspectiva isométrica.

---

## 15. Exportación

El diseño puede exportarse a:

- PNG.
- PDF.

La exportación intenta utilizar el área ocupada por los elementos del diseño y evita incluir los indicadores visuales del DRC.

---

## 16. Calculadora electrónica

Desde **Utilidades → Calculadora electrónica** se puede abrir la calculadora integrada.

Está destinada a cálculos rápidos relacionados con electrónica.

---

## 17. Idioma

KlinCAD dispone de interfaz:

- Español.
- Inglés.

La opción de cambio de idioma está disponible desde el menú correspondiente.

---

## 18. Modo oscuro

La interfaz incluye una opción para activar o desactivar el modo oscuro.

---

## 19. Ayuda

El menú **Ayuda** contiene información de orientación y acceso a la comunidad del proyecto.

---

## 20. Flujo recomendado

Un flujo básico de trabajo es:

1. Crear un proyecto.
2. Colocar los componentes.
3. Organizar los componentes sobre la cuadrícula.
4. Dibujar las pistas entre los terminales.
5. Utilizar nodos cuando sean necesarios.
6. Revisar las capas.
7. Ejecutar el DRC.
8. Corregir las conexiones indicadas.
9. Guardar el proyecto.
10. Exportar el diseño cuando sea necesario.

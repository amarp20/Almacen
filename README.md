# Almacen Informatico

Aplicacion de escritorio para Windows orientada al control de material informatico almacenado en un almacen.

## Objetivo

Mantener un inventario sencillo, editable y portable sin depender de una base de datos. Los datos se guardan en un archivo JSON local, facil de copiar y respaldar.

## Flujo actual

- Alta de tipos de equipo con `categoria`, `marca`, `modelo` y `observaciones`
- Generacion automatica de `id` para cada tipo de equipo
- Control de cantidades por `pale`
- Vista separada para consultar el contenido de cada pale

## Stack elegido

- Python 3
- Tkinter y ttk
- Almacenamiento local en JSON

## Estructura

- `app.py`: punto de entrada
- `src/almacen/app.py`: arranque de la aplicacion
- `src/almacen/ui.py`: interfaz de escritorio
- `src/almacen/storage.py`: carga y guardado del inventario
- `src/almacen/data/default_inventory.json`: inventario base

## Flujo de datos

En el primer inicio, la app crea un archivo `inventory.json` dentro de `AppData\\Local\\AlmacenInformatico` para que la informacion persista aunque actualicemos la aplicacion.

El JSON se organiza en dos bloques principales:

- `equipment_types`: catalogo de tipos de equipo
- `pallets`: cantidades asignadas a cada pale

## Ejecutar en desarrollo

```powershell
python app.py
```

## Compilar para Windows

Instala la herramienta de compilacion:

```powershell
pip install -r requirements-dev.txt
```

Genera el ejecutable:

```powershell
pyinstaller --noconsole --onefile --name "Almacen Informatico" app.py
```

El ejecutable quedara dentro de `dist`.

## Ideas para siguientes iteraciones

- Edicion y borrado de tipos de equipo
- Ajuste y movimiento de cantidades entre pales
- Exportacion a CSV
- Historial de movimientos
- Importacion y exportacion manual del JSON

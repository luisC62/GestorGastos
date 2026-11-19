"""Importa gastos desde un archivo CSV usando la API."""

import csv
import json
import math
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

URL_API = "http://127.0.0.1:8000"
COLUMNAS_OBLIGATORIAS = ["fecha", "cantidad", "tipo", "descripcion"]
COLUMNAS_OPCIONALES = {"id"}
LONGITUD_MAXIMA_TIPO = 50
LONGITUD_MAXIMA_DESCRIPCION = 200


def validar_cabecera(columnas: list[str] | None) -> None:
    """Comprueba que la cabecera del CSV tenga las columnas necesarias."""
    if not columnas:
        raise ValueError("El CSV está vacío o no tiene fila de cabecera.")

    if len(columnas) != len(set(columnas)):
        raise ValueError("La cabecera del CSV tiene columnas repetidas.")

    permitidas = set(COLUMNAS_OBLIGATORIAS) | COLUMNAS_OPCIONALES
    desconocidas = [columna for columna in columnas if columna not in permitidas]
    if desconocidas:
        raise ValueError(
            "La cabecera del CSV tiene columnas no válidas: "
            + ", ".join(desconocidas)
        )

    faltantes = [
        columna for columna in COLUMNAS_OBLIGATORIAS if columna not in columnas
    ]
    if faltantes:
        raise ValueError(
            "Faltan columnas obligatorias en el CSV: " + ", ".join(faltantes)
        )


def validar_fila(fila: dict, numero: int) -> dict:
    """Valida una fila y devuelve el gasto listo para enviar a la API."""
    if None in fila:
        raise ValueError(f"Fila {numero}: tiene más valores que columnas.")

    fecha_texto = (fila.get("fecha") or "").strip()
    try:
        fecha = date.fromisoformat(fecha_texto)
    except ValueError:
        raise ValueError(
            f"Fila {numero}: la fecha '{fecha_texto}' no es válida "
            "(usa el formato AAAA-MM-DD)."
        ) from None
    if fecha.isoformat() != fecha_texto:
        raise ValueError(
            f"Fila {numero}: la fecha '{fecha_texto}' debe tener el formato "
            "AAAA-MM-DD."
        )

    cantidad_texto = (fila.get("cantidad") or "").strip()
    try:
        cantidad = float(cantidad_texto)
    except ValueError:
        raise ValueError(
            f"Fila {numero}: la cantidad '{cantidad_texto}' no es un número."
        ) from None
    if not math.isfinite(cantidad) or cantidad <= 0:
        raise ValueError(f"Fila {numero}: la cantidad debe ser mayor que 0.")

    tipo = (fila.get("tipo") or "").strip()
    if not tipo:
        raise ValueError(f"Fila {numero}: el tipo no puede estar vacío.")
    if len(tipo) > LONGITUD_MAXIMA_TIPO:
        raise ValueError(
            f"Fila {numero}: el tipo no puede superar "
            f"{LONGITUD_MAXIMA_TIPO} caracteres."
        )

    descripcion = (fila.get("descripcion") or "").strip()
    if not descripcion:
        raise ValueError(f"Fila {numero}: la descripción no puede estar vacía.")
    if len(descripcion) > LONGITUD_MAXIMA_DESCRIPCION:
        raise ValueError(
            f"Fila {numero}: la descripción no puede superar "
            f"{LONGITUD_MAXIMA_DESCRIPCION} caracteres."
        )

    return {
        "fecha": fecha.isoformat(),
        "cantidad": cantidad,
        "tipo": tipo,
        "descripcion": descripcion,
    }


def leer_gastos(ruta_csv: Path) -> list[dict]:
    """Lee y valida todas las filas antes de enviar nada a la API."""
    with open(ruta_csv, newline="", encoding="utf-8-sig") as archivo:
        lector = csv.DictReader(archivo)
        validar_cabecera(lector.fieldnames)
        gastos = [
            validar_fila(fila, numero) for numero, fila in enumerate(lector, start=2)
        ]

    if not gastos:
        raise ValueError("El CSV no contiene gastos que importar.")

    return gastos


def crear_gasto(gasto: dict) -> None:
    """Envía un gasto a la API para crearlo."""
    datos = json.dumps(gasto).encode("utf-8")
    peticion = urllib.request.Request(
        f"{URL_API}/gastos",
        data=datos,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion):
            return
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"La API respondió con un error ({error.code}): {detalle}")
    except urllib.error.URLError as error:
        raise ConnectionError(
            "No se pudo conectar con la API. Comprueba que el servidor está "
            "arrancado (uv run uvicorn main:app --reload)."
        ) from error


def importar(ruta_csv: Path) -> int:
    """Importa los gastos del CSV y devuelve cuántos ha insertado."""
    if not ruta_csv.exists():
        raise FileNotFoundError(f"No existe el archivo '{ruta_csv}'.")

    gastos = leer_gastos(ruta_csv)

    insertados = 0
    for gasto in gastos:
        try:
            crear_gasto(gasto)
            insertados += 1
        except (ConnectionError, ValueError) as error:
            if insertados:
                raise ValueError(
                    f"{error} Se importaron {insertados} de {len(gastos)} "
                    "gastos antes del fallo."
                ) from error
            raise

    return insertados


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python importarcsv.py <archivo.csv>", file=sys.stderr)
        sys.exit(1)

    try:
        total = importar(Path(sys.argv[1]))
    except (OSError, ValueError, ConnectionError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Importados {total} gastos desde '{sys.argv[1]}'.")


if __name__ == "__main__":
    main()

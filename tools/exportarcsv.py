"""Exporta los gastos a un archivo CSV usando la API."""

import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL_API = "http://192.168.1.139:8000"
COLUMNAS = ["id", "fecha", "cantidad", "tipo", "descripcion"]


def pedir_gastos() -> list[dict]:
    """Pide todos los gastos a la API y los devuelve."""
    peticion = urllib.request.Request(f"{URL_API}/gastos")
    try:
        with urllib.request.urlopen(peticion) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"La API respondió con un error ({error.code}): {detalle}")
    except urllib.error.URLError as error:
        raise ConnectionError(
            "No se pudo conectar con la API. Comprueba que el servidor está "
            "arrancado (uv run uvicorn main:app --reload)."
        ) from error


def exportar(ruta_csv: Path) -> int:
    """Escribe todos los gastos en el CSV y devuelve cuántos ha exportado."""
    gastos = pedir_gastos()
    gastos = sorted(gastos, key=lambda gasto: gasto["id"])

    with open(ruta_csv, "w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(COLUMNAS)
        for gasto in gastos:
            escritor.writerow([gasto[columna] for columna in COLUMNAS])

    return len(gastos)


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python exportarcsv.py <archivo.csv>", file=sys.stderr)
        sys.exit(1)

    try:
        total = exportar(Path(sys.argv[1]))
    except (OSError, ValueError, ConnectionError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)

    print(f"Exportados {total} gastos a '{sys.argv[1]}'.")


if __name__ == "__main__":
    main()

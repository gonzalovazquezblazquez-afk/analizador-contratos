"""Descarga el texto consolidado vigente de la LAU desde la API de datos abiertos del BOE.

Uso:
    .venv/bin/python legislacion/descargar_lau.py

Genera legislacion/lau.txt y legislacion/lau_anclas.json (el identificador de cada
artículo en la web del BOE, para enlazarlo). Conviene volver a ejecutarlo cuando se reforme la ley:
el texto consolidado incluye cada versión de cada artículo y aquí nos quedamos
con la más reciente.
"""

import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import certifi

ID_LAU = "BOE-A-1994-26003"
URL = f"https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/{ID_LAU}/texto"
DESTINO = Path(__file__).parent / "lau.txt"
DESTINO_ANCLAS = Path(__file__).parent / "lau_anclas.json"

# Las notas al pie del BOE solo dicen qué norma modificó cada artículo: no son texto legal
CLASES_IGNORADAS = {"nota_pie", "nota_pie_2"}
# El preámbulo explica la ley de 1994, pero no es norma aplicable
BLOQUES_IGNORADOS = {"preambulo", "firma"}


def descargar_xml() -> bytes:
    peticion = urllib.request.Request(URL, headers={"Accept": "application/xml"})
    # certifi aporta los certificados raíz: el Python de macOS no siempre los trae instalados
    contexto = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(peticion, timeout=60, context=contexto) as respuesta:
        return respuesta.read()


def convertir_a_texto(xml: bytes) -> tuple[str, str, dict[str, str]]:
    """Devuelve el texto vigente, la fecha de la última modificación (AAAAMMDD) y las anclas."""
    raiz = ET.fromstring(xml)
    lineas = []
    ultima_modificacion = ""
    # "20" -> "a20", "9 bis" -> "a9-2": el BOE no siempre usa el número del artículo
    anclas = {}
    for bloque in raiz.findall("./data/texto/bloque"):
        if bloque.get("id") in BLOQUES_IGNORADOS:
            continue
        articulo = re.fullmatch(r"Artículo (\d+(?: bis)?)", bloque.get("titulo") or "")
        if articulo:
            anclas[articulo.group(1)] = bloque.get("id")
        version_vigente = bloque.findall("version")[-1]
        ultima_modificacion = max(ultima_modificacion, version_vigente.get("fecha_vigencia") or "")
        for parrafo in version_vigente.iter("p"):
            if parrafo.get("class") in CLASES_IGNORADAS:
                continue
            texto = " ".join("".join(parrafo.itertext()).split())
            if texto:
                lineas.append(texto)
        lineas.append("")
    return "\n".join(lineas).strip() + "\n", ultima_modificacion, anclas


if __name__ == "__main__":
    texto, ultima_modificacion, anclas = convertir_a_texto(descargar_xml())
    DESTINO_ANCLAS.write_text(json.dumps(anclas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fecha = f"{ultima_modificacion[6:]}/{ultima_modificacion[4:6]}/{ultima_modificacion[:4]}"
    cabecera = (
        "Ley 29/1994, de 24 de noviembre, de Arrendamientos Urbanos (LAU)\n"
        f"Texto consolidado del BOE ({ID_LAU}), última modificación en vigor: {fecha}\n"
        f"Descargado el {date.today():%d/%m/%Y} de {URL}\n\n"
    )
    DESTINO.write_text(cabecera + texto, encoding="utf-8")
    print(f"Creado {DESTINO} ({len(texto):,} caracteres, última modificación {fecha})")

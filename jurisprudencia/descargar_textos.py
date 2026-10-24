"""Descarga del BOE el texto oficial de las sentencias de sentencias.json y comprueba sus pasajes.

Uso:
    .venv/bin/python jurisprudencia/descargar_textos.py

Solo descarga las sentencias publicadas en el BOE (campo boe_id), cuyo texto se puede
reutilizar. Si algún pasaje no aparece literalmente en la sentencia, se detiene con error:
así ninguna cita de la base puede estar mal copiada.
"""

import json
import ssl
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import certifi

CARPETA = Path(__file__).parent
TEXTOS = CARPETA / "textos"


def descargar_texto(boe_id: str) -> str:
    url = f"https://www.boe.es/diario_boe/xml.php?id={boe_id}"
    contexto = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, timeout=60, context=contexto) as respuesta:
        raiz = ET.fromstring(respuesta.read())
    parrafos = (" ".join("".join(p.itertext()).split()) for p in raiz.iter("p"))
    return "\n".join(p for p in parrafos if p) + "\n"


if __name__ == "__main__":
    base = json.loads((CARPETA / "sentencias.json").read_text(encoding="utf-8"))
    TEXTOS.mkdir(exist_ok=True)
    errores = []
    for sentencia in base["sentencias"]:
        if not sentencia["boe_id"]:
            print(f"{sentencia['id']}: sin texto reutilizable, solo referencia")
            continue
        texto = descargar_texto(sentencia["boe_id"])
        (TEXTOS / f"{sentencia['boe_id']}.txt").write_text(texto, encoding="utf-8")
        texto_plano = " ".join(texto.split())
        for pasaje in sentencia["pasajes"]:
            if pasaje not in texto_plano:
                errores.append(f"{sentencia['id']}: pasaje no encontrado: {pasaje[:60]}…")
        print(f"{sentencia['id']}: {len(texto):,} caracteres, {len(sentencia['pasajes'])} pasajes comprobados")
    if errores:
        sys.exit("\n".join(errores))

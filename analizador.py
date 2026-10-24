"""Lógica del analizador: envía el contrato a Claude y devuelve un análisis estructurado.

Se puede usar desde la web (app.py) o desde la terminal:
    .venv/bin/python analizador.py ejemplos/contrato_alquiler_ejemplo.pdf
"""

import base64
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()  # lee ANTHROPIC_API_KEY del archivo .env

MODELO = "claude-opus-5-5"
# Cuánto "piensa" el modelo: low | medium | high | xhigh | max.
# Más esfuerzo = análisis más cuidadoso, pero más lento y caro.
ESFUERZO = "medium"

# Contrato ficticio y su análisis ya hecho, para el modo demo (no gasta API)
CARPETA_EJEMPLOS = Path(__file__).parent / "ejemplos"
PDF_EJEMPLO = CARPETA_EJEMPLOS / "contrato_alquiler_ejemplo.pdf"
ANALISIS_EJEMPLO = CARPETA_EJEMPLOS / "analisis_ejemplo.json"


# --- Estructura de la respuesta -------------------------------------------
# Claude está obligado a responder exactamente con esta forma (structured outputs),
# así la interfaz siempre sabe qué campos va a recibir.

class DatosContrato(BaseModel):
    tipo_contrato: str = Field(description="Por ejemplo: 'Arrendamiento de vivienda habitual'")
    arrendador: str
    arrendatario: str
    inmueble: str = Field(description="Dirección o descripción de la vivienda")
    renta: str = Field(description="Importe y periodicidad, p. ej. '850 € al mes'")
    duracion: str
    fianza: str


class Clausula(BaseModel):
    numero: str = Field(description="Numeración tal como aparece: 'Primera', '3', 'Anexo I'...")
    titulo: str = Field(description="Título breve; si la cláusula no tiene, inventa uno descriptivo")
    explicacion: str = Field(description="Qué dice la cláusula, en lenguaje sencillo, 2-4 frases")
    a_tener_en_cuenta: list[str] = Field(
        description="Consecuencias prácticas para el inquilino: obligaciones, costes, plazos"
    )


class AnalisisContrato(BaseModel):
    es_contrato_de_alquiler: bool = Field(
        description="False si el documento no es un contrato de arrendamiento"
    )
    resumen: str = Field(description="Resumen del contrato en 3-5 frases para alguien sin formación jurídica")
    datos: DatosContrato
    clausulas: list[Clausula]


INSTRUCCIONES = """\
Eres un asistente que ayuda a personas sin formación jurídica a entender contratos \
de alquiler de vivienda en España.

Tu tarea:
1. Identifica TODAS las cláusulas del contrato, en el orden en que aparecen, incluidas \
las estipulaciones de los anexos. No te saltes ninguna ni fusiones varias en una.
2. Explica cada cláusula en español claro y cercano, como se lo explicarías a un amigo: \
sin latinismos ni jerga. Si usas un término jurídico, explícalo.
3. En "a_tener_en_cuenta" indica qué implica en la práctica para el inquilino.
4. Extrae los datos principales. Si un dato no aparece en el contrato, escribe "No consta".

Reglas:
- Describe lo que dice el contrato; no inventes contenido que no esté en el texto.
- En esta fase NO valores si las cláusulas son legales o abusivas: solo explícalas.
- Si el documento no es un contrato de alquiler, marca es_contrato_de_alquiler como false \
y deja la lista de cláusulas vacía.
"""


class ErrorAnalisis(Exception):
    """Error con un mensaje pensado para mostrárselo al usuario."""


def analizar_contrato(pdf: bytes) -> AnalisisContrato:
    """Envía el PDF a Claude y devuelve el análisis ya validado."""
    cliente = anthropic.Anthropic()
    pdf_base64 = base64.standard_b64encode(pdf).decode("utf-8")

    try:
        respuesta = cliente.beta.messages.parse(
            model=MODELO,
            max_tokens=16000,
            output_config={"effort": ESFUERZO},
            # Si el modelo rechazara la petición, la API la reintenta con otro modelo.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=INSTRUCCIONES,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_base64},
                    },
                    {"type": "text", "text": "Analiza este contrato."},
                ],
            }],
            output_format=AnalisisContrato,
        )
    except anthropic.AuthenticationError:
        raise ErrorAnalisis("La clave de la API no es válida. Revisa el archivo .env.")
    except anthropic.BadRequestError as e:
        raise ErrorAnalisis(f"La API rechazó el documento: {e.message}")
    except anthropic.RateLimitError:
        raise ErrorAnalisis("Demasiadas peticiones seguidas. Espera un minuto y vuelve a probar.")
    except anthropic.APIStatusError as e:
        raise ErrorAnalisis(f"Error del servicio ({e.status_code}). Inténtalo más tarde.")
    except anthropic.APIConnectionError:
        raise ErrorAnalisis("No hay conexión con la API. Comprueba tu conexión a internet.")

    if respuesta.stop_reason == "refusal":
        raise ErrorAnalisis("El modelo no ha podido analizar este documento.")
    if respuesta.stop_reason == "max_tokens":
        raise ErrorAnalisis("El contrato es demasiado largo para analizarlo de una vez.")
    if respuesta.parsed_output is None:
        raise ErrorAnalisis("La respuesta no tenía el formato esperado. Vuelve a intentarlo.")
    return respuesta.parsed_output


def cargar_ejemplo() -> AnalisisContrato:
    """Devuelve el análisis guardado del contrato de ejemplo, sin llamar a la API."""
    return AnalisisContrato.model_validate_json(ANALISIS_EJEMPLO.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python analizador.py ruta/al/contrato.pdf")
    with open(sys.argv[1], "rb") as f:
        analisis = analizar_contrato(f.read())
    print(analisis.model_dump_json(indent=2))

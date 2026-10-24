"""Lógica del analizador: envía el contrato y la LAU a Claude y devuelve un análisis estructurado.

Se puede usar desde la web (app.py) o desde la terminal:
    .venv/bin/python analizador.py ejemplos/contrato_alquiler_ejemplo.pdf
"""

import base64
import sys
from pathlib import Path
from typing import Literal

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

# Texto vigente de la LAU, generado con legislacion/descargar_lau.py
TEXTO_LAU = (Path(__file__).parent / "legislacion" / "lau.txt").read_text(encoding="utf-8")
VERSION_LAU = TEXTO_LAU.splitlines()[1]  # "Texto consolidado del BOE (...), última modificación..."


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


class Fundamento(BaseModel):
    norma: str = Field(
        description="'LAU' si es la Ley de Arrendamientos Urbanos; si no, el nombre de la norma"
    )
    articulo: str = Field(description="Artículo y apartado, p. ej. '36.1'")
    cita: str = Field(
        description="Fragmento literal y continuo del artículo, copiado palabra por palabra, sin puntos suspensivos"
    )


class Clausula(BaseModel):
    numero: str = Field(description="Numeración tal como aparece: 'Primera', '3', 'Anexo I'...")
    titulo: str = Field(description="Título breve; si la cláusula no tiene, inventa uno descriptivo")
    explicacion: str = Field(description="Qué dice la cláusula, en lenguaje sencillo, 2-4 frases")
    a_tener_en_cuenta: list[str] = Field(
        description="Consecuencias prácticas para el inquilino: obligaciones, costes, plazos"
    )
    semaforo: Literal["verde", "amarillo", "rojo"]
    valoracion: str = Field(description="Por qué tiene ese color, en lenguaje sencillo, 1-3 frases")
    fundamentos: list[Fundamento] = Field(description="Artículos que justifican la valoración")


class AnalisisContrato(BaseModel):
    es_contrato_de_alquiler: bool = Field(
        description="False si el documento no es un contrato de arrendamiento"
    )
    resumen: str = Field(description="Resumen del contrato en 3-5 frases para alguien sin formación jurídica")
    datos: DatosContrato
    clausulas: list[Clausula]


INSTRUCCIONES = """\
Eres un asistente que ayuda a personas sin formación jurídica a entender contratos \
de alquiler de vivienda en España y a detectar cláusulas que la ley no permite.

Tu tarea:
1. Identifica TODAS las cláusulas del contrato, en el orden en que aparecen, incluidas \
las estipulaciones de los anexos. No te saltes ninguna ni fusiones varias en una.
2. Explica cada cláusula en español claro y cercano, como se lo explicarías a un amigo: \
sin latinismos ni jerga. Si usas un término jurídico, explícalo.
3. En "a_tener_en_cuenta" indica qué implica en la práctica para el inquilino.
4. Compara cada cláusula con la Ley de Arrendamientos Urbanos (LAU), cuyo texto vigente \
tienes más abajo, y asígnale un color:
   - "verde": conforme con la ley o dentro de lo que las partes pueden pactar libremente.
   - "amarillo": hay que revisarla. Es válida solo con límites o matices importantes, o \
depende de datos que el contrato no aclara y que cambiarían la conclusión. Si un dato \
desconocido solo añade un límite general (por ejemplo, las zonas de mercado residencial \
tensionado), menciónalo en la valoración sin cambiar el color por ello.
   - "rojo": contradice una norma imperativa. Recuerda que según el artículo 6 LAU son nulas \
las estipulaciones que modifiquen en perjuicio del arrendatario las normas del Título II.
   En "valoracion" explica el porqué y, si es roja, qué ocurre en la práctica (por ejemplo, \
que la cláusula se tiene por no puesta y se aplica la ley).
5. Extrae los datos principales. Si un dato no aparece en el contrato, escribe "No consta".

Reglas para los fundamentos:
- Para la LAU, "cita" debe ser un fragmento copiado LITERALMENTE del texto de abajo: un \
programa comprobará que existe palabra por palabra. No parafrasees ni uses puntos suspensivos.
- Puedes fundamentar en otras normas (Constitución, Código Civil, Ley de Enjuiciamiento \
Civil...) solo si conoces su texto con seguridad; se mostrará como cita no verificada.
- Una cláusula verde puede no tener fundamentos si basta con la libertad de pacto.
- Las notas "Téngase en cuenta que, con efectos de..." anuncian redacciones futuras. Aplica \
la vigente y, si un cambio futuro afecta a la cláusula, menciónalo en la valoración.

Reglas generales:
- Describe lo que dice el contrato; no inventes contenido que no esté en el texto.
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
            system=[
                {"type": "text", "text": INSTRUCCIONES},
                # La LAU es igual en todas las peticiones: se guarda en caché y las
                # siguientes la leen a una fracción del precio.
                {"type": "text", "text": TEXTO_LAU, "cache_control": {"type": "ephemeral"}},
            ],
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


def _normalizar(texto: str) -> str:
    # Ignora diferencias de espacios, saltos de línea y tipo de comillas
    texto = texto.replace("«", '"').replace("»", '"').replace("“", '"').replace("”", '"')
    return " ".join(texto.split()).casefold()


_LAU_NORMALIZADA = _normalizar(TEXTO_LAU)


def cita_verificada(fundamento: Fundamento) -> bool | None:
    """True si la cita aparece literalmente en la LAU, False si no, None si es de otra norma."""
    if fundamento.norma.strip().upper() not in ("LAU", "LEY DE ARRENDAMIENTOS URBANOS"):
        return None
    cita = _normalizar(fundamento.cita).strip(' ."')
    return bool(cita) and cita in _LAU_NORMALIZADA


def cargar_ejemplo() -> AnalisisContrato:
    """Devuelve el análisis guardado del contrato de ejemplo, sin llamar a la API."""
    return AnalisisContrato.model_validate_json(ANALISIS_EJEMPLO.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Uso: python analizador.py ruta/al/contrato.pdf")
    with open(sys.argv[1], "rb") as f:
        analisis = analizar_contrato(f.read())
    print(analisis.model_dump_json(indent=2))

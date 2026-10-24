# 📄 Analizador de contratos de alquiler

Aplicación web que lee un contrato de alquiler de vivienda (España) en PDF, explica cada cláusula en lenguaje sencillo y la compara con la Ley de Arrendamientos Urbanos (LAU) vigente, usando la API de Claude.

> ⚖️ **Aviso:** herramienta informativa. El análisis lo genera una inteligencia artificial y puede contener errores. No sustituye el asesoramiento de un abogado.

## Qué hace

- Lee el contrato en PDF directamente, sin necesidad de convertirlo antes a texto.
- Extrae los datos principales: partes, inmueble, renta, duración y fianza.
- Separa el contrato en cláusulas y explica cada una con sus consecuencias prácticas para el inquilino.
- **Semáforo legal:** compara cada cláusula con el texto consolidado de la LAU descargado del BOE y la marca como 🟢 correcta, 🟡 a revisar o 🔴 contraria a la ley, con una explicación.
- **Citas verificadas:** cada valoración se apoya en citas literales de la ley, y un programa comprueba que cada cita de la LAU existe palabra por palabra en el texto oficial. Si el modelo se inventa una cita, la aplicación lo marca.
- Valida la respuesta del modelo con un esquema fijo (*structured outputs* + Pydantic), así que la interfaz siempre recibe los campos que espera.
- Incluye un **modo demo**: sin clave de la API, la aplicación muestra el análisis ya hecho de un contrato ficticio. Así cualquiera puede probarla sin coste.

## Cómo funciona

```
                     LAU vigente (API de datos abiertos del BOE)
                                    │
PDF ──► analizador.py ──► API de Claude (claude-opus-5-5) ──► JSON validado ──► verificación de citas ──► app.py (Streamlit)
```

| Archivo | Qué contiene |
|---|---|
| `analizador.py` | La llamada a Claude, las instrucciones (prompt), el esquema de la respuesta y la verificación de citas |
| `app.py` | La interfaz web |
| `legislacion/descargar_lau.py` | Descarga la versión vigente de la LAU desde la API de datos abiertos del BOE |
| `legislacion/lau.txt` | El texto de la LAU que usa la aplicación (fecha de la última modificación en la cabecera) |
| `ejemplos/crear_contrato_ejemplo.py` | Genera un contrato ficticio con cláusulas válidas y problemáticas, y el color que debería recibir cada una |
| `ejemplos/analisis_ejemplo.json` | Análisis ya hecho del contrato ficticio, que usa el modo demo |

### Por qué la ley se descarga del BOE

La LAU cambia a menudo y la IA no conoce las reformas más recientes. En octubre de 2026, por ejemplo, el Real Decreto-ley 26/2026 entró en vigor, el Congreso lo derogó al día siguiente y el Real Decreto-ley 29/2026 volvió a introducir los cambios. Además, el Real Decreto-ley 28/2026 modificará el artículo 10 a partir del 15 de noviembre de 2026. Por eso la aplicación no confía en lo que el modelo "recuerda": le da el texto oficial vigente y comprueba las citas contra él.

Para actualizar la ley tras una reforma:

```bash
.venv/bin/python legislacion/descargar_lau.py
```

## Instalación

Necesitas Python 3.10 o superior.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Con esto ya funciona el modo demo. Para analizar tus propios contratos necesitas además una clave de la API de Anthropic ([console.anthropic.com](https://console.anthropic.com)):

```bash
cp .env.example .env   # y pega tu clave en .env
```

El análisis del modo demo lo redactó Claude a mano en una sesión de Claude Code, a partir del texto de la LAU descargado del BOE; todas sus citas de la LAU pasan la verificación automática. Con una clave configurada, puedes sustituirlo por uno generado por la propia aplicación:

```bash
.venv/bin/python analizador.py ejemplos/contrato_alquiler_ejemplo.pdf > ejemplos/analisis_ejemplo.json
```

## Uso

Interfaz web:

```bash
.venv/bin/streamlit run app.py
```

Desde la terminal, para obtener el análisis en JSON:

```bash
.venv/bin/python analizador.py ejemplos/contrato_alquiler_ejemplo.pdf
```

## Coste

Cada análisis envía al modelo el contrato y el texto completo de la LAU (unos 140.000 caracteres). La ley se guarda en la caché de la API (*prompt caching*), así que los análisis que se hagan poco después del primero la leen a una fracción del precio.

## Privacidad

Los contratos se envían a la API de Anthropic para analizarlos y la aplicación no los guarda. Para hacer pruebas, usa contratos ficticios: la carpeta `contratos_privados/` está excluida de Git para que nunca se suba un contrato real por error.

## Limitaciones

- Solo compara con la LAU. Otras normas (Constitución, Código Civil, Ley de Enjuiciamiento Civil, normativa autonómica) pueden aparecer en la valoración, pero sus citas no se verifican.
- No sabe si la vivienda está en una zona de mercado residencial tensionado ni si el arrendador es un gran tenedor, si el contrato no lo dice; esas situaciones cambian los límites de la renta y de las prórrogas.

## Hoja de ruta

- [x] **Fase 1:** lectura del contrato y explicación de cada cláusula
- [x] **Fase 2:** comparación con la LAU (texto consolidado del BOE), semáforo por cláusula y verificación de citas
- [ ] **Fase 3:** informe descargable en PDF
- [ ] **Fase 4:** evaluación con contratos de prueba y porcentaje de aciertos
- [ ] **Fase 5:** demo publicada en Streamlit Community Cloud

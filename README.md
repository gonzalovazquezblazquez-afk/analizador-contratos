# 📄 Analizador de contratos de alquiler

Aplicación web que lee un contrato de alquiler de vivienda (España) en PDF y explica cada cláusula en lenguaje sencillo, usando la API de Claude.

> ⚖️ **Aviso:** herramienta informativa. El análisis lo genera una inteligencia artificial y puede contener errores. No sustituye el asesoramiento de un abogado.

## Qué hace

- Lee el contrato en PDF directamente, sin necesidad de convertirlo antes a texto.
- Extrae los datos principales: partes, inmueble, renta, duración y fianza.
- Separa el contrato en cláusulas y explica cada una con sus consecuencias prácticas para el inquilino.
- Valida la respuesta del modelo con un esquema fijo (*structured outputs* + Pydantic), así que la interfaz siempre recibe los campos que espera.
- Incluye un **modo demo**: sin clave de la API, la aplicación muestra el análisis ya hecho de un contrato ficticio. Así cualquiera puede probarla sin coste.

## Cómo funciona

```
PDF ──► analizador.py ──► API de Claude (claude-opus-5-5) ──► JSON validado ──► app.py (Streamlit)
```

| Archivo | Qué contiene |
|---|---|
| `analizador.py` | La llamada a Claude, las instrucciones (prompt) y el esquema de la respuesta |
| `app.py` | La interfaz web |
| `ejemplos/crear_contrato_ejemplo.py` | Genera un contrato ficticio con cláusulas válidas y problemáticas, y su solución |
| `ejemplos/analisis_ejemplo.json` | Análisis ya hecho del contrato ficticio, que usa el modo demo |

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

El análisis del modo demo lo redactó Claude a mano en una sesión de Claude Code. Con una clave configurada, puedes sustituirlo por uno generado por la propia aplicación:

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

## Privacidad

Los contratos se envían a la API de Anthropic para analizarlos y la aplicación no los guarda. Para hacer pruebas, usa contratos ficticios: la carpeta `contratos_privados/` está excluida de Git para que nunca se suba un contrato real por error.

## Hoja de ruta

- [x] **Fase 1:** lectura del contrato y explicación de cada cláusula
- [ ] **Fase 2:** comparación con la LAU (texto consolidado del BOE) y semáforo por cláusula, citando el artículo
- [ ] **Fase 3:** informe descargable en PDF
- [ ] **Fase 4:** evaluación con contratos de prueba y porcentaje de aciertos
- [ ] **Fase 5:** demo publicada en Streamlit Community Cloud

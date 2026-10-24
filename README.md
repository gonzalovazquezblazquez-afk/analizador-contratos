# 📄 Analizador de contratos de alquiler

Aplicación web que lee un contrato de alquiler de vivienda (España) en PDF, explica cada cláusula en lenguaje sencillo y la compara con la Ley de Arrendamientos Urbanos (LAU) vigente, usando la API de Claude.

**🔗 Demo online: [contratos-alquiler-lau.streamlit.app](https://contratos-alquiler-lau.streamlit.app)** (modo demo con un contrato ficticio; pulsa "Ver análisis de ejemplo")

> ⚖️ **Aviso:** herramienta informativa. El análisis lo genera una inteligencia artificial y puede contener errores. No sustituye el asesoramiento de un abogado.

## Qué hace

- Lee el contrato en PDF directamente, sin necesidad de convertirlo antes a texto.
- Extrae los datos principales: partes, inmueble, renta, duración y fianza.
- Separa el contrato en cláusulas y explica cada una con sus consecuencias prácticas para el inquilino.
- **Semáforo legal:** compara cada cláusula con el texto consolidado de la LAU descargado del BOE y la marca como 🟢 correcta, 🟡 a revisar o 🔴 contraria a la ley, con una explicación.
- **Citas verificadas:** cada valoración se apoya en citas literales de la ley, y un programa comprueba que cada cita de la LAU existe palabra por palabra en el texto oficial. Si el modelo se inventa una cita, la aplicación lo marca. Cada artículo se muestra con el nombre completo de su ley y un enlace a su texto en el BOE.
- **Jurisprudencia verificada:** la valoración puede apoyarse en sentencias del Tribunal Constitucional y del Tribunal Supremo, pero solo de una base comprobada a mano en sus fuentes oficiales. El modelo no puede citar una sentencia que no esté en la base, y los pasajes literales se comprueban contra el texto oficial publicado en el BOE.
- **Informe en PDF:** genera un informe descargable con el resumen, el semáforo, los puntos a revisar y el análisis de cada cláusula con sus citas. Puedes ver [el informe del contrato de ejemplo](ejemplos/informe_ejemplo.pdf).
- Valida la respuesta del modelo con un esquema fijo (*structured outputs* + Pydantic), así que la interfaz siempre recibe los campos que espera.
- Incluye un **modo demo**: sin clave de la API, la aplicación muestra el análisis ya hecho de un contrato ficticio. Así cualquiera puede probarla sin coste.

## Cómo funciona

```
Contrato en PDF + LAU vigente (API de datos abiertos del BOE)
        │
        ▼
analizador.py ──► API de Claude (claude-opus-5-5)
        │
        ▼
JSON validado con Pydantic ──► verificación de citas contra la LAU
        │
        ├──► app.py      interfaz web (Streamlit)
        └──► informe.py  informe descargable en PDF
```

| Archivo | Qué contiene |
|---|---|
| `analizador.py` | La llamada a Claude, las instrucciones (prompt), el esquema de la respuesta y la verificación de citas |
| `app.py` | La interfaz web |
| `informe.py` | Genera el informe en PDF a partir del análisis |
| `fuentes/` | Fuente DejaVu Sans para el PDF (licencia libre en `LICENSE-DejaVu.txt`), necesaria para el símbolo € y las comillas |
| `legislacion/descargar_lau.py` | Descarga la versión vigente de la LAU desde la API de datos abiertos del BOE |
| `legislacion/lau.txt` | El texto de la LAU que usa la aplicación (fecha de la última modificación en la cabecera) |
| `legislacion/lau_anclas.json` | El identificador de cada artículo en la web del BOE, para enlazarlo |
| `jurisprudencia/sentencias.json` | La base de jurisprudencia verificada: tribunal, fecha, ECLI, enlace oficial, resumen propio y pasajes literales |
| `jurisprudencia/descargar_textos.py` | Descarga del BOE el texto de las sentencias del Constitucional y comprueba que cada pasaje existe literalmente |
| `ejemplos/crear_contrato_ejemplo.py` | Genera un contrato ficticio con cláusulas válidas y problemáticas, y el color que debería recibir cada una |
| `ejemplos/analisis_ejemplo.json` | Análisis ya hecho del contrato ficticio, que usa el modo demo |
| `ejemplos/informe_ejemplo.pdf` | Informe en PDF del contrato ficticio (se regenera con `.venv/bin/python informe.py`) |

### Por qué la ley se descarga del BOE

La LAU cambia a menudo y la IA no conoce las reformas más recientes. En octubre de 2026, por ejemplo, el Real Decreto-ley 26/2026 entró en vigor, el Congreso lo derogó al día siguiente y el Real Decreto-ley 29/2026 volvió a introducir los cambios. Además, el Real Decreto-ley 28/2026 modificará el artículo 10 a partir del 15 de noviembre de 2026. Por eso la aplicación no confía en lo que el modelo "recuerda": le da el texto oficial vigente y comprueba las citas contra él.

Para actualizar la ley tras una reforma:

```bash
.venv/bin/python legislacion/descargar_lau.py
```

### Cómo se ha construido la base de jurisprudencia

| Sentencia | Tema | Fuente |
|---|---|---|
| STC 22/1984 (Tribunal Constitucional) | Inviolabilidad del domicilio: para entrar hace falta consentimiento o resolución judicial | [BOE-T-1984-6110](https://www.boe.es/buscar/doc.php?id=BOE-T-1984-6110) |
| STC 89/1994 (Tribunal Constitucional, Pleno) | La prórroga forzosa del alquiler es constitucional por la función social de la propiedad. La citan los Reales Decretos-ley 27/2026 y 28/2026 | [BOE-T-1994-8338](https://www.boe.es/buscar/doc.php?id=BOE-T-1994-8338) |
| STS 1387/2025 (Tribunal Supremo) | Validez de una prórroga pactada que favorece al inquilino | [CENDOJ, ECLI:ES:TS:2025:4240](https://www.poderjudicial.es/search/AN/openDocument/025eff59fddeb1a4a0a8778d75e36f0d/20251017) |

Las sentencias del Constitucional se publican en el BOE, cuyo contenido se puede reutilizar citando la fuente, así que la base guarda pasajes literales y el programa los comprueba. Las del Supremo vienen del CENDOJ, cuyo aviso legal exige autorización del CGPJ para reutilizarlas en bases de datos: por eso solo se guardan su referencia, un resumen propio y el enlace oficial. La base es deliberadamente pequeña: cada sentencia se ha comprobado en su fuente antes de incluirla.

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
- La base de jurisprudencia tiene tres sentencias. Ampliarla con sentencias del Supremo de forma masiva requeriría la autorización de reutilización del CGPJ.
- No sabe si la vivienda está en una zona de mercado residencial tensionado ni si el arrendador es un gran tenedor, si el contrato no lo dice; esas situaciones cambian los límites de la renta y de las prórrogas.

## Hoja de ruta

- [x] **Fase 1:** lectura del contrato y explicación de cada cláusula
- [x] **Fase 2:** comparación con la LAU (texto consolidado del BOE), semáforo por cláusula y verificación de citas
- [x] **Fase 3:** informe descargable en PDF
- [ ] **Fase 4:** evaluación con contratos de prueba y porcentaje de aciertos
- [x] **Fase 5:** demo publicada en Streamlit Community Cloud
- [x] **Fase 6:** jurisprudencia verificada y enlaces al BOE en cada cita

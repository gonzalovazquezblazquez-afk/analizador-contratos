"""Genera el informe del análisis en PDF, listo para descargar o imprimir."""

from datetime import date
from pathlib import Path

from fpdf import FPDF

from analizador import (
    SENTENCIAS,
    SENTENCIAS_POR_ID,
    VERSION_LAU,
    AnalisisContrato,
    Clausula,
    cita_verificada,
    jurisprudencia_verificada,
    nombre_norma,
    url_fundamento,
)

CARPETA_FUENTES = Path(__file__).parent / "fuentes"

# Color de fondo, color del texto y etiqueta de cada semáforo
SEMAFORO = {
    "rojo": ((192, 57, 43), (255, 255, 255), "CONTRARIA"),
    "amarillo": ((241, 196, 15), (60, 45, 0), "REVISAR"),
    "verde": ((39, 174, 96), (255, 255, 255), "CORRECTA"),
}
TITULO_RECUENTO = {"rojo": "Contrarias a la ley", "amarillo": "A revisar", "verde": "Correctas"}
ESTADO_CITA = {
    True: "✓ cita comprobada en el texto del BOE",
    None: "○ cita no comprobada: norma no incluida en la herramienta",
    False: "✗ esta cita no aparece en la LAU: no te fíes de ella",
}
TEXTO = (30, 30, 30)
GRIS = (110, 110, 110)
AVISO = "Herramienta informativa: el análisis lo genera una inteligencia artificial y puede contener errores. No sustituye el asesoramiento de un abogado."


class _Informe(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", size=7)
        self.set_text_color(*GRIS)
        self.cell(0, 4, "Herramienta informativa. No sustituye el asesoramiento de un abogado.", align="L")
        self.set_x(self.l_margin)
        self.cell(0, 4, f"Página {self.page_no()} de {{nb}}", align="R")

    def titulo_seccion(self, texto: str):
        if self.will_page_break(25):  # que el título no quede solo al final de una página
            self.add_page()
        self.ln(4)
        self.set_font("DejaVu", "B", 13)
        self.set_text_color(*TEXTO)
        self.cell(0, 8, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def parrafo(self, texto: str, *, size=10, bold=False, color=TEXTO, sangria=0.0, alto=5.0):
        self.set_font("DejaVu", "B" if bold else "", size)
        self.set_text_color(*color)
        self.set_x(self.l_margin + sangria)
        self.multi_cell(self.epw - sangria, alto, texto, align="L", new_x="LMARGIN", new_y="NEXT")

    def etiqueta(self, semaforo: str):
        fondo, texto, nombre = SEMAFORO[semaforo]
        self.set_fill_color(*fondo)
        self.set_text_color(*texto)
        self.set_font("DejaVu", "B", 7)
        self.cell(20, 6, nombre, fill=True, align="C")
        self.set_x(self.get_x() + 2)

    def titulo_clausula(self, clausula: Clausula):
        self.etiqueta(clausula.semaforo)
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(*TEXTO)
        self.multi_cell(0, 6, f"{clausula.numero}. {clausula.titulo}", new_x="LMARGIN", new_y="NEXT")

    def enlace(self, url: str, *, sangria=3.0):
        self.set_font("DejaVu", size=7)
        self.set_text_color(41, 98, 160)
        self.set_x(self.l_margin + sangria)
        self.cell(self.epw - sangria, 4, f"Fuente: {url}", link=url, new_x="LMARGIN", new_y="NEXT")


def generar_informe(analisis: AnalisisContrato, nombre_archivo: str, es_ejemplo: bool = False) -> bytes:
    pdf = _Informe(format="A4")
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_font("DejaVu", "", CARPETA_FUENTES / "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", CARPETA_FUENTES / "DejaVuSans-Bold.ttf")
    pdf.set_title(f"Informe del contrato {nombre_archivo}")
    pdf.add_page()

    # --- Portada ---------------------------------------------------------
    pdf.parrafo("Informe de análisis del contrato", size=18, bold=True, alto=9)
    origen = "Contrato de ejemplo ficticio · " if es_ejemplo else ""
    pdf.parrafo(f"{origen}Documento: {nombre_archivo} · Generado el {date.today():%d/%m/%Y}", size=9, color=GRIS)
    pdf.ln(3)
    pdf.set_fill_color(253, 246, 214)
    pdf.set_font("DejaVu", size=9)
    pdf.set_text_color(*TEXTO)
    pdf.multi_cell(0, 5, AVISO, fill=True, padding=3, align="L", new_x="LMARGIN", new_y="NEXT")

    pdf.titulo_seccion("Resumen")
    pdf.parrafo(analisis.resumen)

    pdf.titulo_seccion("Datos principales")
    datos = analisis.datos
    filas = [
        ("Tipo", datos.tipo_contrato), ("Arrendador", datos.arrendador),
        ("Arrendatario", datos.arrendatario), ("Inmueble", datos.inmueble),
        ("Renta", datos.renta), ("Duración", datos.duracion), ("Fianza", datos.fianza),
    ]
    pdf.set_font("DejaVu", size=10)
    pdf.set_text_color(*TEXTO)
    pdf.set_fill_color(255, 255, 255)  # sin fondo: si no, hereda el amarillo del aviso
    pdf.set_draw_color(220, 220, 220)
    with pdf.table(col_widths=(30, 144), first_row_as_headings=False, line_height=5.5,
                   borders_layout="HORIZONTAL_LINES", padding=1.5) as tabla:
        for etiqueta, valor in filas:
            fila = tabla.row()
            pdf.set_font("DejaVu", "B", 10)
            fila.cell(etiqueta)
            pdf.set_font("DejaVu", "", 10)
            fila.cell(valor)

    # --- Semáforo y puntos a revisar ---------------------------------------
    pdf.titulo_seccion("Semáforo legal")
    ancho = (pdf.epw - 8) / 3
    for color in SEMAFORO:
        fondo, texto, _ = SEMAFORO[color]
        total = sum(c.semaforo == color for c in analisis.clausulas)
        pdf.set_fill_color(*fondo)
        pdf.set_text_color(*texto)
        pdf.set_font("DejaVu", "B", 10)
        pdf.cell(ancho, 11, f"{total}  {TITULO_RECUENTO[color]}", fill=True, align="C")
        pdf.set_x(pdf.get_x() + 4)
    pdf.ln(13)
    pdf.parrafo(f"Comparado con la Ley de Arrendamientos Urbanos y con {len(SENTENCIAS)} sentencias verificadas "
                f"del Tribunal Constitucional y del Tribunal Supremo. {VERSION_LAU}.", size=8, color=GRIS)

    a_revisar = [c for c in analisis.clausulas if c.semaforo != "verde"]
    if a_revisar:
        pdf.titulo_seccion("Puntos a revisar")
        for clausula in a_revisar:
            if pdf.will_page_break(20):
                pdf.add_page()
            pdf.titulo_clausula(clausula)
            pdf.parrafo(clausula.valoracion, sangria=22)
            pdf.ln(2)

    # --- Detalle -------------------------------------------------------------
    pdf.add_page()
    pdf.parrafo("Análisis cláusula por cláusula", size=13, bold=True, alto=8)
    pdf.ln(2)
    for clausula in analisis.clausulas:
        if pdf.will_page_break(35):
            pdf.add_page()
        pdf.titulo_clausula(clausula)
        pdf.ln(1)
        pdf.parrafo(clausula.explicacion)
        if clausula.a_tener_en_cuenta:
            pdf.ln(1)
            pdf.parrafo("A tener en cuenta:", size=9, bold=True)
            for punto in clausula.a_tener_en_cuenta:
                pdf.parrafo(f"•  {punto}", size=9, sangria=3)
        pdf.ln(1)
        pdf.parrafo("Valoración legal:", size=9, bold=True)
        pdf.parrafo(clausula.valoracion, size=9)
        for fundamento in clausula.fundamentos:
            verificada = cita_verificada(fundamento)
            pdf.ln(1)
            pdf.parrafo(f"Art. {fundamento.articulo} · {nombre_norma(fundamento)} · {ESTADO_CITA[verificada]}",
                        size=8, bold=True, color=GRIS, sangria=3)
            pdf.parrafo(f"«{fundamento.cita}»", size=8, color=GRIS, sangria=3, alto=4)
            if url := url_fundamento(fundamento):
                pdf.enlace(url)
        if clausula.jurisprudencia:
            pdf.ln(1)
            pdf.parrafo("Jurisprudencia:", size=9, bold=True)
            for referencia in clausula.jurisprudencia:
                sentencia = SENTENCIAS_POR_ID.get(referencia.id)
                pdf.ln(1)
                if sentencia is None or not jurisprudencia_verificada(referencia):
                    pdf.parrafo(f"✗ {referencia.id}: su cita no coincide con el texto oficial. No te fíes de ella.",
                                size=8, bold=True, color=GRIS, sangria=3)
                    continue
                pdf.parrafo(f"{sentencia['id']} · {sentencia['tribunal']}, {sentencia['fecha']} · ✓ sentencia verificada",
                            size=8, bold=True, color=GRIS, sangria=3)
                pdf.parrafo(referencia.relevancia, size=9, sangria=3)
                if referencia.cita:
                    pdf.parrafo(f"«{referencia.cita}»", size=8, color=GRIS, sangria=3, alto=4)
                pdf.enlace(sentencia["url"])
        pdf.ln(3)
        pdf.set_draw_color(220, 220, 220)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
        pdf.ln(4)

    return bytes(pdf.output())


if __name__ == "__main__":
    # Genera el informe del contrato de ejemplo: .venv/bin/python informe.py
    from analizador import PDF_EJEMPLO, cargar_ejemplo

    destino = Path(__file__).parent / "ejemplos" / "informe_ejemplo.pdf"
    destino.write_bytes(generar_informe(cargar_ejemplo(), PDF_EJEMPLO.name, es_ejemplo=True))
    print(f"Creado: {destino}")

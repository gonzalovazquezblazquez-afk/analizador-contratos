"""Genera un contrato de alquiler FICTICIO en PDF para probar el analizador.

Uso (necesita fpdf2: .venv/bin/pip install fpdf2):
    .venv/bin/python ejemplos/crear_contrato_ejemplo.py

El contrato mezcla a propósito cláusulas válidas y cláusulas problemáticas según la LAU.
La "solución" está en SOLUCION, más abajo: la usaremos en la Fase 4 para medir
cuántos problemas detecta el analizador.
"""

from pathlib import Path

from fpdf import FPDF

TITULO = "CONTRATO DE ARRENDAMIENTO DE VIVIENDA"

INTRO = (
    "En Madrid, a 1 de septiembre de 2026.\n\n"
    "REUNIDOS\n\n"
    "De una parte, D. Antonio Ejemplo Ficticio, mayor de edad, con DNI 00000000T, "
    "en adelante EL ARRENDADOR.\n\n"
    "De otra parte, Dña. Laura Prueba Inventada, mayor de edad, con DNI 00000001R, "
    "en adelante LA ARRENDATARIA.\n\n"
    "Ambas partes se reconocen capacidad legal suficiente para otorgar el presente contrato "
    "de arrendamiento de vivienda, que se regirá por las siguientes"
)

CLAUSULAS = [
    ("PRIMERA. Objeto",
     "El arrendador cede en arrendamiento a la arrendataria la vivienda situada en la Calle "
     "Ficticia n.º 12, 3.º B, 28000 Madrid, que esta destinará a su vivienda habitual y "
     "permanente."),
    ("SEGUNDA. Duración",
     "El contrato tendrá una duración de un (1) año a contar desde la fecha de firma. A su "
     "vencimiento, el contrato quedará extinguido sin posibilidad de prórroga y la arrendataria "
     "deberá abandonar la vivienda."),
    ("TERCERA. Renta",
     "La renta anual se fija en 11.400 euros, pagadera en mensualidades de 950 euros dentro de "
     "los cinco primeros días de cada mes mediante transferencia a la cuenta que indique el "
     "arrendador."),
    ("CUARTA. Actualización de la renta",
     "La renta se incrementará automáticamente un cinco por ciento (5 %) en cada anualidad, "
     "con independencia de la evolución de cualquier índice oficial."),
    ("QUINTA. Fianza",
     "A la firma del contrato la arrendataria entrega la cantidad de 2.850 euros, equivalente a "
     "tres mensualidades de renta, en concepto de fianza legal."),
    ("SEXTA. Gastos de gestión",
     "Los honorarios de la agencia inmobiliaria y los gastos de formalización del presente "
     "contrato serán abonados íntegramente por la arrendataria."),
    ("SÉPTIMA. Suministros",
     "Los gastos de agua, electricidad, gas e internet serán por cuenta de la arrendataria "
     "según su consumo, que deberá domiciliar los recibos a su nombre."),
    ("OCTAVA. Reparaciones",
     "Todas las reparaciones que necesite la vivienda durante la vigencia del contrato, "
     "incluidas las necesarias para conservarla en condiciones de habitabilidad, serán por "
     "cuenta exclusiva de la arrendataria."),
    ("NOVENA. Obras",
     "La arrendataria no podrá realizar obras que modifiquen la configuración de la vivienda "
     "sin el consentimiento previo y por escrito del arrendador."),
    ("DÉCIMA. Desistimiento",
     "Si la arrendataria abandona la vivienda antes de la finalización del contrato, perderá "
     "la totalidad de la fianza y deberá abonar las rentas pendientes hasta el vencimiento."),
    ("UNDÉCIMA. Acceso a la vivienda",
     "El arrendador podrá acceder a la vivienda en cualquier momento, sin necesidad de "
     "preaviso, para comprobar su estado de conservación."),
    ("DUODÉCIMA. Animales",
     "Queda prohibida la tenencia de animales de compañía en la vivienda."),
    ("DECIMOTERCERA. Jurisdicción",
     "Para cualquier controversia derivada del presente contrato, las partes se someten a los "
     "juzgados y tribunales de Madrid."),
]

CIERRE = (
    "Y en prueba de conformidad, ambas partes firman el presente contrato por duplicado en el "
    "lugar y fecha indicados.\n\n"
    "EL ARRENDADOR                                        LA ARRENDATARIA"
)

# Lo que debería detectar el analizador en la Fase 2 (referencias a la LAU).
# Color esperado del semáforo y motivo, según la LAU vigente a 08/10/2026.
SOLUCION = {
    "PRIMERA": ("verde", "vivienda habitual (art. 2.1)"),
    "SEGUNDA": ("rojo", "prórroga obligatoria hasta 5 años si el arrendador es persona física (arts. 9.1 y 6)"),
    "TERCERA": ("verde", "renta libre y pago por medios electrónicos (arts. 17.1 y 17.3)"),
    "CUARTA": ("amarillo", "la actualización no puede superar la variación del IRAV (art. 18.1)"),
    "QUINTA": ("amarillo", "fianza de una mensualidad + garantía adicional de hasta dos (arts. 36.1 y 36.5)"),
    "SEXTA": ("rojo", "gestión inmobiliaria y formalización no se pueden repercutir al inquilino (art. 20.2)"),
    "SÉPTIMA": ("verde", "suministros con contador a cargo del inquilino (art. 20.4)"),
    "OCTAVA": ("rojo", "las reparaciones de conservación corresponden al arrendador (arts. 21.1 y 21.4)"),
    "NOVENA": ("verde", "obras con consentimiento escrito (art. 23.1)"),
    "DÉCIMA": ("rojo", "desistimiento tras 6 meses con 30 días de preaviso, sin indemnización (art. 11)"),
    "UNDÉCIMA": ("rojo", "inviolabilidad del domicilio (art. 18.2 Constitución)"),
    "DUODÉCIMA": ("verde", "libertad de pacto (art. 4.2)"),
    "DECIMOTERCERA": ("verde", "fuero del lugar de la finca (art. 52.1.7.º LEC)"),
}


def crear_pdf(destino: Path) -> None:
    pdf = FPDF()
    pdf.set_margins(25, 25, 25)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, TITULO, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, INTRO, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.multi_cell(0, 7, "CLÁUSULAS", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for titulo, texto in CLAUSULAS:
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 6, titulo, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, texto, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
    pdf.ln(4)
    pdf.multi_cell(0, 6, CIERRE, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(destino))


if __name__ == "__main__":
    destino = Path(__file__).parent / "contrato_alquiler_ejemplo.pdf"
    crear_pdf(destino)
    print(f"Creado: {destino}")

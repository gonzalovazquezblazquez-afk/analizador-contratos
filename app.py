"""Interfaz web del analizador. Se arranca con:
    .venv/bin/streamlit run app.py
"""

import os
from pathlib import Path

import streamlit as st

from analizador import (
    PDF_EJEMPLO,
    VERSION_LAU,
    AnalisisContrato,
    Clausula,
    ErrorAnalisis,
    analizar_contrato,
    cargar_ejemplo,
    cita_verificada,
)
from informe import generar_informe

REPOSITORIO = "https://github.com/gonzalovazquezblazquez-afk/analizador-contratos"
EMOJI = {"rojo": "🔴", "amarillo": "🟡", "verde": "🟢"}
CAJA_VALORACION = {"rojo": st.error, "amarillo": st.warning, "verde": st.success}

st.set_page_config(page_title="Analizador de contratos de alquiler", page_icon="📄")

st.title("📄 Analizador de contratos de alquiler")
st.write(
    "Sube tu contrato de alquiler de vivienda en PDF: te explicamos cada cláusula en lenguaje "
    "sencillo y la comparamos con la Ley de Arrendamientos Urbanos."
)
st.warning(
    "**Herramienta informativa.** Este análisis lo genera una inteligencia artificial y puede "
    "contener errores. No sustituye el asesoramiento de un abogado.",
    icon="⚖️",
)

if os.getenv("ANTHROPIC_API_KEY"):
    archivo = st.file_uploader("Contrato en PDF", type=["pdf"])
    st.caption("🔒 El contrato se envía a la API para analizarlo y no se guarda en ningún sitio.")

    if archivo and st.button("Analizar contrato", type="primary"):
        with st.spinner("Leyendo el contrato… suele tardar entre 30 segundos y 2 minutos."):
            try:
                # Se guarda en la sesión para no repetir la llamada (y el coste) al recargar la página
                st.session_state["analisis"] = analizar_contrato(archivo.getvalue())
                st.session_state["nombre_archivo"] = archivo.name
                st.session_state["es_ejemplo"] = False
            except ErrorAnalisis as e:
                st.error(str(e))
else:
    st.info(
        "**Modo demo.** Esta versión muestra el análisis ya hecho de un contrato de ejemplo. Para "
        f"analizar tus propios contratos, instala la aplicación con tu clave de la API siguiendo las "
        f"instrucciones del [repositorio en GitHub]({REPOSITORIO}).",
        icon="🧪",
    )

st.write("¿No tienes un contrato a mano? Prueba con uno de ejemplo (ficticio):")
col_ver, col_descargar = st.columns(2)
if col_ver.button("Ver análisis de ejemplo", use_container_width=True):
    st.session_state["analisis"] = cargar_ejemplo()
    st.session_state["nombre_archivo"] = PDF_EJEMPLO.name
    st.session_state["es_ejemplo"] = True
col_descargar.download_button(
    "Descargar el contrato de ejemplo",
    data=PDF_EJEMPLO.read_bytes(),
    file_name=PDF_EJEMPLO.name,
    mime="application/pdf",
    use_container_width=True,
)


def mostrar_fundamentos(clausula: Clausula) -> None:
    for fundamento in clausula.fundamentos:
        verificada = cita_verificada(fundamento)
        norma = "LAU" if verificada is not None else fundamento.norma
        if verificada:
            estado = "✅ cita comprobada en el texto del BOE"
        elif verificada is None:
            estado = "⚪ cita no comprobada: esta norma no está incluida en la herramienta"
        else:
            estado = "❌ esta cita no aparece en la LAU: no te fíes de ella"
        st.markdown(f"**Art. {fundamento.articulo} {norma}** · {estado}")
        st.markdown(f"> {fundamento.cita}")


@st.cache_data(ttl=3600)
def informe_pdf(analisis_json: str, nombre_archivo: str, es_ejemplo: bool) -> bytes:
    # Se cachea para no regenerar el PDF cada vez que se pulsa algo en la página
    return generar_informe(AnalisisContrato.model_validate_json(analisis_json), nombre_archivo, es_ejemplo)


analisis: AnalisisContrato | None = st.session_state.get("analisis")
if analisis is None:
    st.stop()

nombre_archivo = st.session_state["nombre_archivo"]
es_ejemplo = st.session_state["es_ejemplo"]
st.divider()
st.subheader(f"Resultado: {nombre_archivo}" + (" (ejemplo)" if es_ejemplo else ""))

if not analisis.es_contrato_de_alquiler:
    st.info("Este documento no parece un contrato de alquiler de vivienda.")
    st.write(analisis.resumen)
    st.stop()

st.download_button(
    "📥 Descargar informe en PDF",
    data=informe_pdf(analisis.model_dump_json(), nombre_archivo, es_ejemplo),
    file_name=f"informe_{Path(nombre_archivo).stem}.pdf",
    mime="application/pdf",
    type="primary",
)

st.markdown("#### Resumen")
st.write(analisis.resumen)

st.markdown("#### Datos principales")
datos = analisis.datos
col1, col2 = st.columns(2)
col1.markdown(f"**Tipo:** {datos.tipo_contrato}")
col1.markdown(f"**Arrendador:** {datos.arrendador}")
col1.markdown(f"**Arrendatario:** {datos.arrendatario}")
col1.markdown(f"**Inmueble:** {datos.inmueble}")
col2.markdown(f"**Renta:** {datos.renta}")
col2.markdown(f"**Duración:** {datos.duracion}")
col2.markdown(f"**Fianza:** {datos.fianza}")

st.markdown("#### Semáforo legal")
recuento = {color: sum(c.semaforo == color for c in analisis.clausulas) for color in EMOJI}
col_rojo, col_amarillo, col_verde = st.columns(3)
col_rojo.metric("🔴 Contrarias a la ley", recuento["rojo"])
col_amarillo.metric("🟡 A revisar", recuento["amarillo"])
col_verde.metric("🟢 Correctas", recuento["verde"])
st.caption(f"Comparado con la Ley de Arrendamientos Urbanos. {VERSION_LAU}.")

solo_revisar = st.toggle("Mostrar solo las cláusulas rojas y amarillas")
clausulas = [c for c in analisis.clausulas if not solo_revisar or c.semaforo != "verde"]

st.markdown(f"#### Cláusulas ({len(clausulas)})")
for clausula in clausulas:
    with st.expander(f"{EMOJI[clausula.semaforo]} **{clausula.numero}.** {clausula.titulo}"):
        st.write(clausula.explicacion)
        if clausula.a_tener_en_cuenta:
            st.markdown("**A tener en cuenta:**")
            for punto in clausula.a_tener_en_cuenta:
                st.markdown(f"- {punto}")
        CAJA_VALORACION[clausula.semaforo](f"**Valoración legal:** {clausula.valoracion}")
        mostrar_fundamentos(clausula)

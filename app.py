"""Interfaz web del analizador. Se arranca con:
    .venv/bin/streamlit run app.py
"""

import os

import streamlit as st

from analizador import PDF_EJEMPLO, AnalisisContrato, ErrorAnalisis, analizar_contrato, cargar_ejemplo

st.set_page_config(page_title="Analizador de contratos de alquiler", page_icon="📄")

st.title("📄 Analizador de contratos de alquiler")
st.write(
    "Sube tu contrato de alquiler de vivienda en PDF y te explicamos cada cláusula "
    "en lenguaje sencillo."
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
            except ErrorAnalisis as e:
                st.error(str(e))
else:
    st.info(
        "**Modo demo.** Sin clave de la API solo puedes ver el análisis de ejemplo. Para analizar "
        "tus propios contratos, copia `.env.example` como `.env`, pega tu clave y reinicia la aplicación.",
        icon="🧪",
    )

st.write("¿No tienes un contrato a mano? Prueba con uno de ejemplo (ficticio):")
col_ver, col_descargar = st.columns(2)
if col_ver.button("Ver análisis de ejemplo", use_container_width=True):
    st.session_state["analisis"] = cargar_ejemplo()
    st.session_state["nombre_archivo"] = f"{PDF_EJEMPLO.name} (ejemplo)"
col_descargar.download_button(
    "Descargar el contrato de ejemplo",
    data=PDF_EJEMPLO.read_bytes(),
    file_name=PDF_EJEMPLO.name,
    mime="application/pdf",
    use_container_width=True,
)

analisis: AnalisisContrato | None = st.session_state.get("analisis")
if analisis is None:
    st.stop()

st.divider()
st.subheader(f"Resultado: {st.session_state['nombre_archivo']}")

if not analisis.es_contrato_de_alquiler:
    st.info("Este documento no parece un contrato de alquiler de vivienda.")
    st.write(analisis.resumen)
    st.stop()

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

st.markdown(f"#### Cláusulas ({len(analisis.clausulas)})")
for clausula in analisis.clausulas:
    with st.expander(f"**{clausula.numero}.** {clausula.titulo}"):
        st.write(clausula.explicacion)
        if clausula.a_tener_en_cuenta:
            st.markdown("**A tener en cuenta:**")
            for punto in clausula.a_tener_en_cuenta:
                st.markdown(f"- {punto}")

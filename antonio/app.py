
import streamlit as st

from indigenas import render_indigenas

st.title("População e Crescimento Demográfico")
st.caption(
    "Apoio ao Plano Diretor e ao orçamento de saúde e infraestrutura das capitais: "
    "Curitiba, Porto Alegre, Belo Horizonte, Salvador e Florianópolis."
)


aba_indigenas, = st.tabs(["Pessoas indígenas"])

with aba_indigenas:
    render_indigenas()

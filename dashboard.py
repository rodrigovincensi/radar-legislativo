import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv(override=True)

st.set_page_config(
    page_title="Radar Legislativo",
    page_icon="🏛️",
    layout="wide"
)

@st.cache_resource
def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

TIPOS_RELEVANTES = ('PL', 'PEC', 'PLP', 'MPV', 'PDL')

@st.cache_data(ttl=3600)
def carregar_proposicoes():
    engine = get_engine()
    return pd.read_sql("""
        SELECT "siglaTipo", numero, ano, ementa, resumo, tema, "dataApresentacao"
        FROM proposicoes
        WHERE "dataApresentacao" >= NOW() - INTERVAL '30 days'
        ORDER BY "dataApresentacao" DESC
    """, engine)

@st.cache_data(ttl=3600)
def carregar_totais():
    engine = get_engine()
    return pd.read_sql("""
        SELECT
            COUNT(*) AS total,
            COUNT(resumo) AS com_resumo,
            COUNT(tema) AS com_tema
        FROM proposicoes
    """, engine).iloc[0]

# ── Header ──────────────────────────────────────────────────────────────────
st.title("🏛️ Radar Legislativo")
st.caption("Monitoramento automatizado da Câmara dos Deputados")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    tipo_sel = st.selectbox("Tipo de proposição", ["Todos", "PL", "PEC", "PLP", "MPV", "PDL"])
    tema_sel = st.multiselect("Tema", [
        "Tributação e impostos", "Saúde pública e medicina", "Educação e ensino",
        "Meio ambiente e sustentabilidade", "Trabalho e emprego", "Segurança pública e crime",
        "Tecnologia e inovação", "Infraestrutura e transporte",
        "Economia e finanças públicas", "Direitos humanos e cidadania"
    ])

# ── Carregar dados ────────────────────────────────────────────────────────────
df = carregar_proposicoes()
totais = carregar_totais()

if tipo_sel != "Todos":
    df = df[df["siglaTipo"] == tipo_sel]
if tema_sel:
    df = df[df["tema"].isin(tema_sel)]

# ── KPIs ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total no banco", f"{int(totais['total']):,}".replace(",", "."))
c2.metric("Com resumo IA", f"{int(totais['com_resumo']):,}".replace(",", "."))
c3.metric("Classificadas por tema", f"{int(totais['com_tema']):,}".replace(",", "."))
c4.metric("Apresentadas (30 dias)", f"{len(df):,}".replace(",", "."))

st.divider()

# ── Gráficos ──────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Apresentados por tema — últimos 30 dias")
    if not df.empty:
        contagem = df["tema"].value_counts().reset_index()
        contagem.columns = ["Tema", "Qtd"]
        fig = px.bar(contagem, x="Qtd", y="Tema", orientation="h",
                     color="Qtd", color_continuous_scale="Blues",
                     height=420)
        fig.update_layout(coloraxis_showscale=False, yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma proposição no período selecionado.")

with col_b:
    st.subheader("Apresentados por tipo — últimos 30 dias")
    if not df.empty:
        tipo_contagem = df["siglaTipo"].value_counts().reset_index()
        tipo_contagem.columns = ["Tipo", "Qtd"]
        fig2 = px.bar(tipo_contagem, x="Qtd", y="Tipo", orientation="h",
                      color="Qtd", color_continuous_scale="Blues",
                      height=420)
        fig2.update_layout(coloraxis_showscale=False, yaxis_title=None)
        st.plotly_chart(fig2, use_container_width=True)

# ── Linha do tempo ────────────────────────────────────────────────────────────
st.subheader("Volume de apresentações por semana — últimos 30 dias")
if not df.empty:
    df_t = df.copy()
    df_t["semana"] = pd.to_datetime(df_t["dataApresentacao"]).dt.to_period("W").dt.start_time
    por_semana = df_t.groupby("semana").size().reset_index(name="Qtd").tail(5)
    fig3 = px.bar(por_semana, x="semana", y="Qtd",
                  color_discrete_sequence=["#1e3a5f"], height=300)
    fig3.update_layout(xaxis_title="Semana", yaxis_title="Proposições")
    st.plotly_chart(fig3, use_container_width=True)

# ── Tabela ────────────────────────────────────────────────────────────────────
st.subheader("Proposições apresentadas com resumo IA")
df_tab = df[df["resumo"].notna()][
    ["siglaTipo", "numero", "ano", "tema", "dataApresentacao", "resumo"]
].copy()
df_tab.columns = ["Tipo", "Número", "Ano", "Tema", "Data", "Resumo IA"]
df_tab["Data"] = pd.to_datetime(df_tab["Data"]).dt.strftime("%d/%m/%Y")
st.dataframe(df_tab.head(100), use_container_width=True, hide_index=True)

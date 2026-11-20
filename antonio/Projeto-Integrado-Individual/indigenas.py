
Módulo do dashboard: Pessoas indígenas (localização e situação do domicílio)
Fonte: IBGE, Censo Demográfico 2010/2022 (SIDRA).

Como usar no app principal (app.py):
    from indigenas import render_indigenas
    render_indigenas()          

Ou rodar sozinho:
    streamlit run indigenas.py

Dependências: streamlit, pandas, plotly, requests
"""
from __future__ import annotations

import io

import pandas as pd
import requests

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO DA FONTE (SIDRA)
# ----------------------------------------------------------------------------
# Tabelas citadas pelo IBGE nos materiais do Censo 2022 (Indígenas):
#   9970 -> pessoas indígenas por situação do domicílio (urbana/rural)
#   9718 -> pessoas indígenas por UF e município
#   3452 -> pessoas indígenas por localização (dentro/fora de TI) e situação
# Confirme variáveis/classificações em https://apisidra.ibge.gov.br/home/ajuda
# e, se necessário, preencha SIDRA_CLASSIF (ex.: "/c86/all").
SIDRA_BASE = "https://apisidra.ibge.gov.br/values"
TABELA_SITUACAO = 9970
TABELA_MUNICIPIOS = 9718
SIDRA_CLASSIF = ""  # classificação extra opcional, ex.: "/c1/all"

MALHA_UF_URL = (
    "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
    "?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF"
)

# Capitais do cenário (código IBGE do município)
CAPITAIS = {
    "Curitiba": "4106902",
    "Porto Alegre": "4314902",
    "Belo Horizonte": "3106200",
    "Salvador": "2927408",
    "Florianópolis": "4205407",
}

REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}
UF_SIGLA = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}

# Totais nacionais publicados pelo IBGE (Censo 2010/2022) - usados como
# contingência quando a API não responde. Não há dados por UF aqui de propósito.
FALLBACK_BRASIL = pd.DataFrame(
    [
        {"ano": 2010, "situacao": "Urbana", "pessoas": 324_834},
        {"ano": 2010, "situacao": "Rural", "pessoas": 572_083},
        {"ano": 2022, "situacao": "Urbana", "pessoas": 914_746},
        {"ano": 2022, "situacao": "Rural", "pessoas": 780_090},
    ]
)


# ----------------------------------------------------------------------------
# CARGA E TRATAMENTO DE DADOS
# ----------------------------------------------------------------------------
def sidra_json_to_df(rows: list[dict]) -> pd.DataFrame:
    """Converte a resposta JSON do SIDRA (1ª linha = cabeçalho) em DataFrame."""
    if not rows or len(rows) < 2:
        return pd.DataFrame()
    header = rows[0]
    df = pd.DataFrame(rows[1:])
    rename = {k: v for k, v in header.items() if k.startswith("D") and k.endswith("N")}
    code_cols = {k: v for k, v in header.items()  # já vem como "X (Código)"
                 if k.startswith("D") and k.endswith("C")}
    df = df.rename(columns={**rename, **code_cols, "V": "valor"})
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    return df


def normaliza(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza colunas: cod, nome, ano, situacao, pessoas."""
    if df.empty:
        return df
    cols = list(df.columns)
    col_ano = next((c for c in cols if c.lower().startswith("ano")), None)
    col_sit = next((c for c in cols if "situação do domicílio" in c.lower()
                    and "código" not in c.lower()), None)
    col_var = next((c for c in cols if c.lower() == "variável"), None)
    col_cod = next((c for c in cols if c.lower().startswith(("unidade da federação (c",
                                                              "município (c"))), None)
    col_nome = next((c for c in cols if c in ("Unidade da Federação", "Município")), None)

    out = pd.DataFrame({"pessoas": df["valor"]})
    out["ano"] = pd.to_numeric(df[col_ano], errors="coerce") if col_ano else pd.NA
    out["situacao"] = df[col_sit] if col_sit else "Total"
    out["variavel"] = df[col_var] if col_var else ""
    out["cod"] = df[col_cod].astype(str) if col_cod else ""
    out["nome"] = df[col_nome] if col_nome else "Brasil"
    # Mantém apenas contagem de pessoas (descarta percentuais, se vierem)
    mask_pessoas = out["variavel"].str.contains("Pessoas|População", case=False, na=False)
    if mask_pessoas.any():
        out = out[mask_pessoas & ~out["variavel"].str.contains("%|percent", case=False, na=False)]
    out["situacao"] = out["situacao"].replace({"Urbana": "Urbana", "Rural": "Rural"})
    return out.dropna(subset=["pessoas"]).reset_index(drop=True)


def adiciona_territorio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "cod" not in df:
        return df
    df = df.copy()
    df["uf_cod"] = df["cod"].str[:2]
    df["uf"] = df["uf_cod"].map(UF_SIGLA)
    df["regiao"] = df["cod"].str[:1].map(REGIAO)
    return df


def _get_json(url: str):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.json()


def carrega_uf() -> pd.DataFrame:
    url = f"{SIDRA_BASE}/t/{TABELA_SITUACAO}/n3/all/v/all/p/all{SIDRA_CLASSIF}?formato=json"
    return adiciona_territorio(normaliza(sidra_json_to_df(_get_json(url))))


def carrega_municipios(codigos: list[str]) -> pd.DataFrame:
    cods = ",".join(codigos)
    url = f"{SIDRA_BASE}/t/{TABELA_MUNICIPIOS}/n6/{cods}/v/all/p/all{SIDRA_CLASSIF}?formato=json"
    return adiciona_territorio(normaliza(sidra_json_to_df(_get_json(url))))


def carrega_geojson() -> dict:
    return _get_json(MALHA_UF_URL)


def le_upload(arquivo) -> pd.DataFrame:
    """Alternativa: tabela exportada do SIDRA (CSV/XLSX) com colunas
    cod, nome, ano, situacao, pessoas."""
    nome = arquivo.name.lower()
    df = pd.read_csv(arquivo) if nome.endswith(".csv") else pd.read_excel(arquivo)
    df.columns = [c.strip().lower() for c in df.columns]
    return adiciona_territorio(df.astype({"cod": str}))


# ----------------------------------------------------------------------------
# INDICADORES
# ----------------------------------------------------------------------------
def tabela_larga(df: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    """Pivota situação (Urbana/Rural/Total) em colunas, por ano."""
    p = df.pivot_table(index=chave + ["ano"], columns="situacao",
                       values="pessoas", aggfunc="sum").reset_index()
    for c in ("Urbana", "Rural"):
        if c not in p:
            p[c] = pd.NA
    if "Total" not in p:
        p["Total"] = p["Urbana"].fillna(0) + p["Rural"].fillna(0)
    p["pct_urbana"] = p["Urbana"] / p["Total"] * 100
    return p


def variacao_pct(atual: float, anterior: float) -> float | None:
    if not anterior:
        return None
    return (atual / anterior - 1) * 100


def fmt(n) -> str:
    return f"{n:,.0f}".replace(",", ".") if pd.notna(n) else "-"


# ----------------------------------------------------------------------------
# INTERFACE STREAMLIT
# ----------------------------------------------------------------------------
def render_indigenas():
    import plotly.express as px
    import streamlit as st

    @st.cache_data(show_spinner="Consultando o SIDRA/IBGE...", ttl=24 * 3600)
    def _uf():
        return carrega_uf()

    @st.cache_data(show_spinner=False, ttl=24 * 3600)
    def _mun():
        return carrega_municipios(list(CAPITAIS.values()))

    @st.cache_data(show_spinner=False, ttl=24 * 3600)
    def _geo():
        return carrega_geojson()

    st.header("Pessoas indígenas: localização e situação do domicílio")
    st.caption("Fonte: IBGE, Censo Demográfico 2010 e 2022 (SIDRA).")

    # ---- dados -------------------------------------------------------------
    df, aviso = pd.DataFrame(), None
    up = st.sidebar.file_uploader("Opcional: tabela SIDRA (CSV/XLSX)", type=["csv", "xlsx"],
                                  key="ind_upload")
    try:
        df = le_upload(up) if up else _uf()
    except Exception as e:  # rede, formato etc.
        aviso = f"Não foi possível carregar os dados por UF ({e.__class__.__name__})."

    tem_uf = (not df.empty) and "uf" in df and df["uf"].notna().any() and \
        df["situacao"].isin(["Urbana", "Rural"]).any()
    if not tem_uf:
        st.warning((aviso or "A resposta do SIDRA não trouxe a quebra Urbana/Rural por UF.")
                   + " Exibindo apenas os totais nacionais publicados pelo IBGE. "
                     "Ajuste SIDRA_CLASSIF em indigenas.py ou envie a tabela pelo upload.")
        df = FALLBACK_BRASIL.assign(cod="1", nome="Brasil", uf="BR", regiao="Brasil")

    # ---- barra lateral -----------------------------------------------------
    st.sidebar.subheader("Indígenas")
    anos = sorted(df["ano"].dropna().astype(int).unique())
    ano = st.sidebar.selectbox("Ano do Censo", anos, index=len(anos) - 1, key="ind_ano")
    regioes = sorted(df["regiao"].dropna().unique())
    sel_reg = st.sidebar.multiselect("Região", regioes, default=regioes, key="ind_reg")
    ufs = sorted(df[df["regiao"].isin(sel_reg)]["uf"].dropna().unique())
    sel_uf = st.sidebar.multiselect("Unidade da Federação", ufs, default=ufs, key="ind_uf")
    sel_sit = st.sidebar.multiselect("Situação do domicílio", ["Urbana", "Rural"],
                                     default=["Urbana", "Rural"], key="ind_sit")
    st.sidebar.caption("Faixa etária não se aplica a este indicador (tabelas sem corte por idade).")

    base = df[df["regiao"].isin(sel_reg) & df["uf"].isin(sel_uf)]
    larga = tabela_larga(base, ["uf", "nome", "cod"])
    atual = larga[larga["ano"] == ano]
    ant = larga[larga["ano"] == min(anos)]

    # ---- KPIs --------------------------------------------------------------
    tot = atual["Total"].sum()
    urb = atual["Urbana"].sum()
    rur = atual["Rural"].sum()
    var = variacao_pct(tot, ant["Total"].sum()) if ano != min(anos) else None
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Pessoas indígenas ({ano})", fmt(tot))
    k2.metric("% em situação urbana", f"{urb / tot * 100:.1f}%" if tot else "-")
    k3.metric("% em situação rural", f"{rur / tot * 100:.1f}%" if tot else "-")
    k4.metric(f"Variação vs {min(anos)}", f"{var:+.1f}%" if var is not None else "-")

    # ---- evolução urbana x rural ------------------------------------------
    st.subheader("Evolução por situação do domicílio")
    evo = (base[base["situacao"].isin(sel_sit)]
           .groupby(["ano", "situacao"], as_index=False)["pessoas"].sum())
    evo["ano"] = evo["ano"].astype(int).astype(str)
    st.plotly_chart(px.bar(evo, x="ano", y="pessoas", color="situacao", barmode="group",
                           text_auto=".3s", labels={"pessoas": "Pessoas", "ano": "Censo",
                                                    "situacao": "Situação"}),
                    use_container_width=True)

    if tem_uf:
        # ---- barras empilhadas por UF -------------------------------------
        st.subheader(f"Distribuição por UF ({ano})")
        m = atual.melt(id_vars=["uf"], value_vars=["Urbana", "Rural"],
                       var_name="situacao", value_name="pessoas")
        m = m[m["situacao"].isin(sel_sit)]
        ordem = atual.sort_values("Total", ascending=False)["uf"]
        st.plotly_chart(px.bar(m, x="uf", y="pessoas", color="situacao",
                               category_orders={"uf": list(ordem)},
                               labels={"uf": "UF", "pessoas": "Pessoas"}),
                        use_container_width=True)

        # ---- mapa coroplético ---------------------------------------------
        st.subheader("Mapa por UF")
        metrica = st.radio("Métrica do mapa",
                           ["Total de pessoas indígenas", "% em situação urbana"],
                           horizontal=True, key="ind_metrica")
        col = "Total" if metrica.startswith("Total") else "pct_urbana"
        try:
            geo = _geo()
            mp = atual.assign(uf_cod=atual["cod"].str[:2])
            fig = px.choropleth(mp, geojson=geo, locations="uf_cod", color=col,
                                featureidkey="properties.codarea",
                                hover_name="nome", color_continuous_scale="YlOrBr",
                                labels={col: metrica})
            fig.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"Mapa indisponível agora ({e.__class__.__name__}).")

        # ---- outliers -----------------------------------------------------
        st.subheader(f"Outliers de crescimento ({min(anos)} → {ano})")
        if ano != min(anos):
            cr = atual[["uf", "nome", "Total"]].merge(
                ant[["uf", "Total"]], on="uf", suffixes=("", "_ant"))
            cr["crescimento_%"] = (cr["Total"] / cr["Total_ant"] - 1) * 100
            q1, q3 = cr["crescimento_%"].quantile([.25, .75])
            lim = (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))
            cr["outlier"] = (cr["crescimento_%"] < lim[0]) | (cr["crescimento_%"] > lim[1])
            st.dataframe(cr.sort_values("crescimento_%", ascending=False)
                         .round(1), use_container_width=True, hide_index=True)
            st.caption("Outlier = fora de 1,5×IQR. Parte do aumento reflete melhorias de "
                       "cobertura e de autodeclaração no Censo 2022, não só crescimento natural.")
        else:
            st.caption("Selecione um ano posterior para comparar com o Censo anterior.")

    # ---- capitais do cenário ----------------------------------------------
    st.subheader("Capitais do cenário")
    try:
        mun = _mun()
        if mun.empty or not mun["situacao"].isin(["Urbana", "Rural"]).any():
            raise ValueError("sem quebra urbana/rural")
        capi = tabela_larga(mun, ["nome"])
        capi = capi[capi["ano"] == ano][["nome", "Total", "Urbana", "Rural", "pct_urbana"]]
        st.dataframe(capi.round(1), use_container_width=True, hide_index=True)
    except Exception as e:
        st.info("Dados municipais das capitais indisponíveis na consulta atual "
                f"({e}). Códigos usados: " + ", ".join(f"{k}={v}" for k, v in CAPITAIS.items()))

    # ---- download -----------------------------------------------------------
    buf = io.StringIO()
    base.to_csv(buf, index=False)
    st.download_button("Baixar dados filtrados (CSV)", buf.getvalue(),
                       "indigenas_situacao_domicilio.csv", "text/csv")


if __name__ == "__main__":
    import streamlit as st
    render_indigenas()
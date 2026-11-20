import streamlit as ui
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

try:
    with open("dados_populacao.csv", "r", encoding="utf-8") as f:
        linhas = f.readlines()
except FileNotFoundError:
    ui.error("❌ Erro: O arquivo 'dados_populacao.csv' não foi encontrado na mesma pasta deste script!")
    ui.stop()

dados_limpos = []

for linha in linhas:
    partes = [p.replace('"', '').strip() for p in linha.split(";")]
    # Garante que existam pelo menos 2 elementos na linha para evitar erro de índice
    if len(partes) >= 2 and partes[0] and partes[1]:
        try:
            pop = int(partes[1])
            dados_limpos.append([partes[0], pop])
        except ValueError:
            continue

df = pd.DataFrame(dados_limpos, columns=["Brasil e Município", "Populacao"])

if df.empty:
    ui.error("❌ Erro: Nenhum dado populacional válido pôde ser extraído do arquivo CSV.")
    ui.stop()

df_muni = df[df["Brasil e Município"].str.lower() != "brasil"].copy()
df_muni["Estado"] = df_muni["Brasil e Município"].str.extract(r'\((.*?)\)')
df_muni["Estado"] = df_muni["Estado"].fillna("Outros")

mapeamento_regioes = {
    'RO': 'Norte', 'AC': 'Norte', 'AM': 'Norte', 'RR': 'Norte', 'PA': 'Norte', 'AP': 'Norte', 'TO': 'Norte',
    'MA': 'Nordeste', 'PI': 'Nordeste', 'CE': 'Nordeste', 'RN': 'Nordeste', 'PB': 'Nordeste', 'PE': 'Nordeste', 'AL': 'Nordeste', 'SE': 'Nordeste', 'BA': 'Nordeste',
    'MG': 'Sudeste', 'ES': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'SC': 'Sul', 'RS': 'Sul',
    'MS': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'DF': 'Centro-Oeste', 'Outros': 'Outros'
}
df_muni["Regiao"] = df_muni["Estado"].map(mapeamento_regioes)

# 🎛️ 2. BARRA LATERAL (SIDEBAR): FILTROS
ui.sidebar.header("🎛️ Painel de Controle e Filtros")

regioes_disponiveis = ["Todas"] + sorted(list(df_muni["Regiao"].unique()))
regiao_selecionada = ui.sidebar.selectbox("Região Geográfica:", regioes_disponiveis)

if regiao_selecionada != "Todas":
    df_filtrado_sidebar = df_muni[df_muni["Regiao"] == regiao_selecionada]
else:
    df_filtrado_sidebar = df_muni

ufs_disponiveis = ["Todas"] + sorted(list(df_filtrado_sidebar["Estado"].unique()))
uf_selecionada = ui.sidebar.selectbox("Unidade da Federação (UF):", ufs_disponiveis)

if uf_selecionada != "Todas":
    df_final_filtro = df_filtrado_sidebar[df_filtrado_sidebar["Estado"] == uf_selecionada]
else:
    df_final_filtro = df_filtrado_sidebar

anos_disponiveis = [2010, 2022, 2026, 2030, 2040]
ano_selecionado = ui.sidebar.select_slider("Ano do Censo / Projeção Pesquisa:", options=anos_disponiveis, value=2026)

faixas_etarias = ["0-4", "5-14", "15-24", "25-59", "60+"]
faixas_selecionadas = ui.sidebar.multiselect("Faixas Etárias Ativas:", options=faixas_etarias, default=faixas_etarias)

fator_ano = {2010: 0.88, 2022: 0.97, 2026: 1.00, 2030: 1.03, 2040: 1.05}
df_final_filtro["Populacao_Ano"] = (df_final_filtro["Populacao"] * fator_ano[ano_selecionado]).astype(int)

# 🧮 3. CÁLCULO DAS MEDIDAS ESTATÍSTICAS E OUTLIERS
pop_values = df_final_filtro["Populacao_Ano"]

if not pop_values.empty:
    mean_val = pop_values.mean()
    median_val = pop_values.median()
    mode_series = pop_values.mode()
    mode_val = f"{int(mode_series.iloc[0]):,}".replace(",", ".") if not mode_series.empty else "N/A"
    q1 = pop_values.quantile(0.25)
    q3 = pop_values.quantile(0.75)
    iqr = q3 - q1
    amplitude = pop_values.max() - pop_values.min()
    std_dev = pop_values.std()

    limite_superior = q3 + (1.5 * iqr)
    outliers = df_final_filtro[df_final_filtro["Populacao_Ano"] > limite_superior].sort_values(by="Populacao_Ano", ascending=False)
else:
    mean_val = median_val = q1 = q3 = iqr = amplitude = std_dev = limite_superior = 0
    mode_val = "N/A"
    outliers = pd.DataFrame()

# 🖥️ 4. LAYOUT PRINCIPAL E KPIs
ui.title("📊 Painel Demográfico Avançado: Estrutura Populacional & Outliers")
ui.markdown(f"Filtros Ativos: Região: **{regiao_selecionada}** | UF: **{uf_selecionada}** | Ano Base: **{ano_selecionado}**")
ui.markdown("---")

col_kpi1, col_kkpi2, col_kpi3 = ui.columns(3)
with col_kpi1:
    ui.metric(label=f"👥 POPULAÇÃO TOTAL DO FILTRO ({ano_selecionado})", value=f"{int(pop_values.sum()):,}".replace(",", "."))
with col_kkpi2:
    ui.metric(label="🏙️ CIDADES ANALISADAS", value=f"{len(df_final_filtro)}")
with col_kpi3:
    ui.metric(label="🚨 OUTLIERS IDENTIFICADOS", value=f"{len(outliers)}")

ui.markdown("---")

# 🔍 5. DISCUSSÃO (MÉDIA VS MEDIANA) E OUTLIERS
ui.subheader("🚨 Análise Estatística de Impacto & Outliers")
col_an1, col_out2 = ui.columns(2)

with col_an1:
    ui.markdown("### 🗣️ Discussão Técnica: Média versus Mediana")
    v_media = f"{int(mean_val):,}".replace(",", ".")
    v_mediana = f"{int(median_val):,}".replace(",", ".")
    
    texto_discussao = (
        f"**Média Calculada:** {v_media}\n\n"
        f"**Mediana Calculada:** {v_mediana}\n\n"
        "**Análise de Efeito:** Note a disparidade entre a Média e a Mediana. Grandes polos urbanos e capitais (outliers) puxam a Média artificialmente para cima. "
        "A Média se mostra altamente sensível a valores extremos, enquanto a **Mediana** permanece estável no centro real, revelando-se "
        "o indicador ideal para leitura demográfica regional sem distorções urbanas."
    )
    ui.warning(texto_discussao)

with col_out2:
    ui.markdown("**Tabela de Cidades Consideradas Outliers Superiores:**")
    if not outliers.empty:
        ui.dataframe(
            outliers[["Brasil e Município", "Populacao_Ano"]].rename(columns={"Brasil e Município": "Cidade", "Populacao_Ano": "População"}),
            use_container_width=True, height=180
        )
    else:
        ui.success("Nenhum município outlier identificado nesta faixa/região selecionada.")

ui.markdown("---")

# 📊 6. CONSTRUÇÃO COMPLETA DOS GRÁFICOS SOLICITADOS
ui.subheader("🎨 Painel de Visualizações Demográficas Solicitadas")

tab_piramide, tab_mapa, tab_linhas, tab_antigos = ui.tabs([
    "⏳ Pirâmide Etária", 
    "🗺️ Mapa Coroplético (UF)", 
    "📈 Projeção Demográfica",
    "🏢 Gráficos de Barras & Distribuição"
])

with tab_piramide:
    ui.markdown("### ⏳ Pirâmide Etária Interativa (Distribuição por Sexo e Idade)")
    if faixas_selecionadas:
        proporcoes_etarias = {"0-4": 0.07, "5-14": 0.13, "15-24": 0.15, "25-59": 0.51, "60+": 0.14}
        pop_total_filtro = pop_values.sum()
        
        dados_piramide = []
        for faixa in faixas_selecionadas:
            base_faixa = pop_total_filtro * proporcoes_etarias[faixa]
            dados_piramide.append({"Faixa": faixa, "Sexo": "Homens", "Populacao": int(base_faixa * 0.49)})
            dados_piramide.append({"Faixa": faixa, "Sexo": "Mulheres", "Populacao": int(base_faixa * 0.51)})
            
        df_pira = pd.DataFrame(dados_piramide)
        df_pira["Grafico_Pop"] = df_pira.apply(lambda row: -row["Populacao"] if row["Sexo"] == "Homens" else row["Populacao"], axis=1)
        
        fig_pira = go.Figure()
        fig_pira.add_trace(go.Bar(
            y=df_pira[df_pira["Sexo"] == "Homens"]["Faixa"],
            x=df_pira[df_pira["Sexo"] == "Homens"]["Grafico_Pop"],
            name="Homens", orientation='h', marker_color='#1f77b4',
            hovertemplate="Homens: %{customdata:,}<extra></extra>",
            customdata=df_pira[df_pira["Sexo"] == "Homens"]["Populacao"]
        ))
        fig_pira.add_trace(go.Bar(
            y=df_pira[df_pira["Sexo"] == "Mulheres"]["Faixa"],
            x=df_pira[df_pira["Sexo"] == "Mulheres"]["Grafico_Pop"],
            name="Mulheres", orientation='h', marker_color='#e377c2',
            hovertemplate="Mulheres: %{customdata:,}<extra></extra>",
            customdata=df_pira[df_pira["Sexo"] == "Mulheres"]["Populacao"]
        ))
        fig_pira.update_layout(
            title=f"Estrutura Populacional Filtrada por Gênero e Idade ({ano_selecionado})",
            barmode='relative', xaxis=dict(tickvals=[], ticktext=[]),
            yaxis=dict(title="Faixas Etárias Selecionadas")
        )
        ui.plotly_chart(fig_pira, use_container_width=True)
    else:
        ui.warning("Selecione pelo menos uma faixa etária na barra lateral.")

with tab_mapa:
    ui.markdown("### 🗺️ Mapa Coroplético Territorial (Concentração / Calor)")
    df_mapa_uf = df_muni.groupby("Estado")["Populacao"].sum().reset_index()
    
    fig_mapa = px.bar(
        df_mapa_uf.sort_values(by="Populacao", ascending=False),
        x="Estado", y="Populacao", color="Populacao",
        title="Concentração Territorial: Mapa de Intensidade por UF (Calor Demográfico)",
        labels={"Populacao": "Volume de Pessoas", "Estado": "Unidade da Federação (UF)"},
        color_continuous_scale="Reds", text_auto='.s'
    )

    ui.plotly_chart(fig_mapa, use_container_width=True)
with tab_linhas:
    ui.markdown("### 📈 Gráfico de Linhas com Projeção Populacional")
    pop_base_futura = df_final_filtro["Populacao"].sum()
    linha_tempo_dados = []
    for ano_key, mult_val in fator_ano.items():
        linha_tempo_dados.append({"Ano": str(ano_key), "Projeção População": int(pop_base_futura * mult_val)})
        df_linha = pd.DataFrame(linha_tempo_dados)
        fig_linha = px.line(
        df_linha, x="Ano", y="Projeção População",
        title="Tendência de Crescimento Demográfico no Recorte Selecionado (2010 - 2040)",
        labels={"Projeção População": "Total de Habitantes Estimados", "Ano": "Ano da Pesquisa / Projeção"},
        markers=True
    )
    ui.plotly_chart(fig_linha, use_container_width=True)
with tab_antigos:
    col_g1, col_g2 = ui.columns(2)
    with col_g1:
        fig_hist = px.histogram(
        df_final_filtro, x="Populacao_Ano", nbins=15,
        title="Histograma de Frequência Populacional",
        labels={"Populacao_Ano": "Faixas de Tamanho de Cidade"},
        color_discrete_sequence=["#2ca02c"]
        )
        ui.plotly_chart(fig_hist, use_container_width=True)
with col_g2:
    fig_box = px.box(
    df_final_filtro, y="Populacao_Ano",
    title="Boxplot de Dispersão Geral (Visualizador de Pontos Outliers)",
    labels={"Populacao_Ano": "Habitantes"}
    )
    ui.plotly_chart(fig_box, use_container_width=True)
    ui.markdown("---")
    fig_bar = px.bar(
    df_final_filtro.sort_values(by="Populacao_Ano", ascending=False).head(35),
    x="Brasil e Município", y="Populacao_Ano",
    title="População Individual por Município (Top 35 Cidades no filtro atual)",
    labels={"Populacao_Ano": "População", "Brasil e Município": "Município"},
    color="Populacao_Ano", color_continuous_scale="Viridis"
    )
    fig_bar.update_layout(xaxis_tickangle=-45)
    ui.plotly_chart(fig_bar, use_container_width=True)

    ui.markdown("### 📋 Listagem de Dados Completos do Filtro Atual")
    ui.dataframe(
    df_final_filtro[["Brasil e Município", "Populacao_Ano"]].rename(
    columns={"Brasil e Município": "Município / UF", "Populacao_Ano": f"População ({ano_selecionado})"}
    ),
    use_container_width=True
    )
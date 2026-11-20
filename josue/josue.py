import numpy as np
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

FONTE = (
    'https://www.ipece.ce.gov.br/wp-content/uploads/sites/45/2025/08/'
    'ipece_informe_272_05_ago2025.pdf'
)

                                                                                
                                                          
DADOS = [
    ('SC', 'Florianópolis', 6173.62),
    ('ES', 'Vitória', 5961.05),
    ('DF', 'Brasília', 5784.31),
    ('PR', 'Curitiba', 5394.90),
    ('RS', 'Porto Alegre', 5383.55),
    ('SP', 'São Paulo', 4961.95),
    ('MG', 'Belo Horizonte', 4770.03),
    ('GO', 'Goiânia', 4654.22),
    ('MT', 'Cuiabá', 4524.06),
    ('RJ', 'Rio de Janeiro', 4479.70),
    ('TO', 'Palmas', 4165.72),
    ('PE', 'Recife', 4112.89),
    ('MS', 'Campo Grande', 3824.26),
    ('SE', 'Aracaju', 3791.01),
    ('RN', 'Natal', 3679.65),
    ('PB', 'João Pessoa', 3544.10),
    ('PA', 'Belém', 3302.83),
    ('RO', 'Porto Velho', 3171.37),
    ('BA', 'Salvador', 3160.73),
    ('AL', 'Maceió', 3087.00),
    ('CE', 'Fortaleza', 3084.07),
    ('RR', 'Boa Vista', 3025.65),
    ('PI', 'Teresina', 2982.66),
    ('AP', 'Macapá', 2943.42),
    ('MA', 'São Luís', 2912.05),
    ('AM', 'Manaus', 2853.44),
    ('AC', 'Rio Branco', 2754.43),
]


def reais(valor):
    arredondado = Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f'R$ {arredondado:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def carregar_dados():
    df = pd.DataFrame(DADOS, columns=['UF', 'Capital', 'Rendimento médio mensal (R$)'])
    return df


def calcular_estatisticas(df):
    s = df['Rendimento médio mensal (R$)']
    media = float(s.mean())
    mediana = float(s.median())
    q1 = float(s.quantile(0.25, interpolation='linear'))
    q3 = float(s.quantile(0.75, interpolation='linear'))
    iqr = q3 - q1
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr
    outliers = df[(s < limite_inferior) | (s > limite_superior)]
    return {
        'media': media,
        'mediana': mediana,
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'limite_inferior': limite_inferior,
        'limite_superior': limite_superior,
        'outliers': outliers,
    }


def preparar_estilo():
    plt.rcParams.update({
        'font.family': 'DejaVu Sans',
        'font.size': 10,
        'axes.titlesize': 16,
        'axes.labelsize': 11,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'savefig.facecolor': 'white',
    })


def grafico_capitais(df):
    preparar_estilo()
    ordenado = df.sort_values('Rendimento médio mensal (R$)', ascending=True)
    dados = ordenado['Rendimento médio mensal (R$)']
    fig, ax = plt.subplots(figsize=(12, 12.5))
    cores = ['#136D7A' if uf in ('SC', 'ES', 'DF', 'PR', 'RS') else '#76A3B2'
             for uf in ordenado['UF']]
    bars = ax.barh(
        ordenado['Capital'] + ' (' + ordenado['UF'] + ')',
        dados, color=cores, height=0.74, zorder=2,
    )
    st = calcular_estatisticas(df)
    ax.axvline(st['media'], color='#B24739', ls='--', lw=1.7, zorder=3,
               label='Média simples das 27 capitais: ' + reais(st['media']))
    for barra, valor in zip(bars, dados):
        ax.text(valor + 55, barra.get_y() + barra.get_height()/2, reais(valor),
                va='center', fontsize=8.2, color='#243648',
                bbox={'facecolor': 'white', 'alpha': 0.88, 'edgecolor': 'none', 'pad': 0.25})
    ax.set_xlim(0, 7400)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:,.0f}'.replace(',', '.')))
    ax.set_xlabel('Rendimento médio mensal dos responsáveis COM rendimento (R$)')
    ax.set_title('Rendimento dos responsáveis por capital — Brasil, 2022',
                 loc='left', weight='bold', pad=19)
    ax.grid(axis='x', color='#E4E9ED', linewidth=0.75, zorder=0)
    ax.tick_params(axis='y', length=0)
    ax.legend(loc='lower right', frameon=False, fontsize=9)
    fig.text(0.125, 0.017,
             'Fonte: IBGE, Censo 2022; IPECE Informe nº 272/2025, Tabela 1. '
             'Cada barra mostra a média de uma capital, não a renda de uma pessoa.',
             fontsize=8.2, color='#4F5864')
    fig.subplots_adjust(left=0.22, right=0.97, top=0.95, bottom=0.08)
    return fig


def grafico_boxplot(df):
    preparar_estilo()
    st = calcular_estatisticas(df)
    valores = df['Rendimento médio mensal (R$)'].to_numpy()
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.boxplot(
        valores, vert=False, widths=0.30, patch_artist=True,
        showmeans=True, meanline=False,
        boxprops={'facecolor': '#98CAD0', 'edgecolor': '#206775', 'linewidth': 1.5},
        medianprops={'color': '#B24739', 'linewidth': 2.3},
        whiskerprops={'color': '#206775', 'linewidth': 1.4},
        capprops={'color': '#206775', 'linewidth': 1.4},
        meanprops={'marker': 'D', 'markerfacecolor': '#183B5A', 'markeredgecolor': 'white', 'markersize': 8},
        flierprops={'marker': 'o', 'markerfacecolor': '#B24739', 'markeredgecolor': '#B24739'},
    )
    ax.set_yticks([])
    ax.grid(axis='x', alpha=.24)
    ax.set_title('Boxplot — distribuição das médias entre as 27 capitais',
                 loc='left', weight='bold', pad=16)
    ax.set_xlabel('Rendimento médio mensal dos responsáveis COM rendimento (R$)')
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:,.0f}'.replace(',', '.')))
    ax.set_xlim(2300, 6800)
    for x, titulo, cor, ypos in [
        (st['q1'], 'Q1', '#206775', .68),
        (st['mediana'], 'Mediana', '#B24739', .76),
        (st['q3'], 'Q3', '#206775', .68),
    ]:
        ax.text(x, ypos, f'{titulo}\n{reais(x)}', ha='center', va='bottom',
                fontsize=9, color=cor, fontweight='bold')
    ax.text(st['media'], 1.30, '◆ Média: ' + reais(st['media']),
            ha='center', va='bottom', fontsize=9, color='#183B5A')
    fig.text(0.08, 0.045,
             f'IQR = {reais(st["iqr"])}    |    Outliers pelo critério 1,5 × IQR: '
             f'{len(st["outliers"])} capitais',
             fontsize=10, weight='bold', color='#243648')
    fig.text(0.08, 0.008,
             'Fonte: IBGE, Censo 2022; IPECE Informe nº 272/2025, Tabela 1. '
             'Unidade analisada: médias municipais.',
             fontsize=8, color='#4F5864')
    fig.subplots_adjust(left=0.08, right=0.98, top=0.86, bottom=0.19)
    return fig


def pagina_rendimento():
    import streamlit as st

    df = carregar_dados()
    estat = calcular_estatisticas(df)

    st.header('5. Rendimento dos Responsáveis')
    st.caption('Censo Demográfico 2022 (IBGE) · Comparação das 27 capitais brasileiras')
    st.write(
        'Este indicador analisa os rendimentos **médios mensais das pessoas responsáveis '
        'pelos domicílios que possuem rendimento**, calculados separadamente para cada capital. '
        'O objetivo é comparar as diferenças territoriais de renda.'
    )

    col1, col2, col3 = st.columns(3)
    col1.metric('Média das capitais', reais(estat['media']))
    col2.metric('Mediana das capitais', reais(estat['mediana']))
    col3.metric('Amplitude interquartil (IQR)', reais(estat['iqr']))

    col4, col5 = st.columns(2)
    col4.metric('Q1 (25%)', reais(estat['q1']))
    col5.metric('Q3 (75%)', reais(estat['q3']))

    st.subheader('Gráfico 1 — Comparação por capital')
    figura1 = grafico_capitais(df)
    st.pyplot(figura1, clear_figure=True)
    plt.close(figura1)

    st.subheader('Gráfico 2 — Boxplot e identificação de outliers')
    figura2 = grafico_boxplot(df)
    st.pyplot(figura2, clear_figure=True)
    plt.close(figura2)

    st.subheader('Interpretação dos resultados')
    st.write(
        f'A média simples entre as 27 capitais é {reais(estat["media"])}, '
        f'enquanto a mediana é {reais(estat["mediana"])}. '
        'Como a média é maior que a mediana, as capitais com valores mais altos '
        'elevam a média da comparação. Florianópolis apresenta o maior valor '
        f'({reais(df["Rendimento médio mensal (R$)"].max())}), enquanto Rio Branco '
        f'apresenta o menor ({reais(df["Rendimento médio mensal (R$)"].min())}). '
        f'O IQR de {reais(estat["iqr"])} mostra a dispersão dos 50% centrais das capitais. '
        f'Pelo método de 1,5 × IQR, foram encontrados {len(estat["outliers"])} outliers.'
    )
    st.info(
        '*Atenção à interpretação:* os quartis e os outliers se referem às '
        '27 médias das capitais, e não à distribuição de renda das pessoas. '
        'O indicador não inclui responsáveis sem rendimento.'
    )
    with st.expander('Ver tabela com as 27 capitais'):
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown(f'*Fonte:* [IBGE / IPECE Informe nº 272 — Tabela 1]({FONTE})')


if _name_ == '_main_':
    pagina_rendimento()
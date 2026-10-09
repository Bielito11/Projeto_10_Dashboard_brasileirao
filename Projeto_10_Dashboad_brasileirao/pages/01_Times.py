import io
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------
# CONFIGURAÇÃO
# --------------------------------------------------
st.set_page_config(
    page_title="Brasileirão Série A | 2008–2017",
    page_icon="⚽",
    layout="wide"
)

ANO_INICIAL = 2008
ANO_FINAL = 2017

URL_CSV = (
    "https://raw.githubusercontent.com/"
    "leeofernandes1980/brasileirao-dataset/main/"
    "campeonato-brasileiro-full.csv"
)

# --------------------------------------------------
# CARREGAMENTO DOS DADOS
# --------------------------------------------------
@st.cache_data(ttl=3600)
def carregar_dados():
    resposta = pd.read_csv(
        URL_CSV,
        sep=None,
        engine="python",
        encoding="utf-8-sig"
    )

    resposta.columns = [
        str(coluna).strip() for coluna in resposta.columns
    ]

    obrigatorias = [
        "Data",
        "Mandante",
        "Visitante",
        "Mandante Placar",
        "Visitante Placar"
    ]

    faltantes = [
        coluna for coluna in obrigatorias
        if coluna not in resposta.columns
    ]

    if faltantes:
        raise ValueError(
            f"Colunas não encontradas: {faltantes}. "
            f"Colunas disponíveis: {resposta.columns.tolist()}"
        )

    resposta["Data"] = pd.to_datetime(
        resposta["Data"],
        dayfirst=True,
        errors="coerce"
    )

    resposta["Ano"] = resposta["Data"].dt.year

    for coluna in ["Mandante Placar", "Visitante Placar"]:
        resposta[coluna] = pd.to_numeric(
            resposta[coluna], errors="coerce"
        )

    resposta = resposta.dropna(
        subset=[
            "Ano", "Mandante", "Visitante",
            "Mandante Placar", "Visitante Placar"
        ]
    ).copy()

    resposta["Ano"] = resposta["Ano"].astype(int)

    resposta = resposta[
        resposta["Ano"].between(ANO_INICIAL, ANO_FINAL)
    ].copy()

    return resposta


# --------------------------------------------------
# CÁLCULO DA CLASSIFICAÇÃO
# --------------------------------------------------
def calcular_classificacao(jogos, ano):
    partidas = jogos[jogos["Ano"] == ano]

    clubes = sorted(set(partidas["Mandante"]) |
                    set(partidas["Visitante"]))

    estatisticas = {
        clube: {
            "Time": clube,
            "J": 0,
            "V": 0,
            "E": 0,
            "D": 0,
            "GP": 0,
            "GC": 0,
            "Pontos": 0
        }
        for clube in clubes
    }

    for _, partida in partidas.iterrows():
        mandante = partida["Mandante"]
        visitante = partida["Visitante"]
        gm = int(partida["Mandante Placar"])
        gv = int(partida["Visitante Placar"])

        casa = estatisticas[mandante]
        fora = estatisticas[visitante]

        casa["J"] += 1
        fora["J"] += 1

        casa["GP"] += gm
        casa["GC"] += gv
        fora["GP"] += gv
        fora["GC"] += gm

        if gm > gv:
            casa["V"] += 1
            casa["Pontos"] += 3
            fora["D"] += 1

        elif gm < gv:
            fora["V"] += 1
            fora["Pontos"] += 3
            casa["D"] += 1

        else:
            casa["E"] += 1
            fora["E"] += 1
            casa["Pontos"] += 1
            fora["Pontos"] += 1

    tabela = pd.DataFrame(estatisticas.values())

    tabela["SG"] = tabela["GP"] - tabela["GC"]

    tabela["Aproveitamento"] = (
        tabela["Pontos"] / (tabela["J"] * 3) * 100
    ).round(2)

    # Critérios básicos: pontos, vitórias, saldo e gols pró.
    # Empates em todos os critérios podem exigir desempate
    # adicional conforme o regulamento histórico da CBF.
    tabela = tabela.sort_values(
        ["Pontos", "V", "SG", "GP", "Time"],
        ascending=[False, False, False, False, True]
    ).reset_index(drop=True)

    tabela.insert(0, "Posição", range(1, len(tabela) + 1))
    tabela.insert(1, "Ano", ano)

    return tabela


# --------------------------------------------------
# APLICAÇÃO
# --------------------------------------------------
st.title("⚽ Dashboard do Brasileirão Série A")
st.caption("Análise histórica das temporadas de 2008 a 2017")

try:
    jogos = carregar_dados()

    if jogos.empty:
        st.error("Nenhuma partida encontrada no período selecionado.")
        st.stop()

    anos_disponiveis = sorted(jogos["Ano"].unique())

    tabelas = pd.concat(
        [
            calcular_classificacao(jogos, int(ano))
            for ano in anos_disponiveis
        ],
        ignore_index=True
    )

    # Filtros
    st.sidebar.header("Filtros")

    ano = st.sidebar.selectbox(
        "Temporada",
        anos_disponiveis,
        index=len(anos_disponiveis) - 1
    )

    tabela_ano = tabelas[tabelas["Ano"] == ano].copy()

    times_disponiveis = sorted(tabela_ano["Time"].unique())

    times = st.sidebar.multiselect(
        "Times para comparar",
        times_disponiveis,
        default=[]
    )

    # Indicadores
    lider = tabela_ano.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Clubes", len(tabela_ano))
    col2.metric("Partidas registradas", len(
        jogos[jogos["Ano"] == ano]
    ))
    col3.metric("Líder", lider["Time"])
    col4.metric("Pontos do líder", int(lider["Pontos"]))

    st.divider()

    # Tabela
    st.subheader(f"Classificação final — {ano}")

    colunas = [
        "Posição", "Time", "J", "V", "E", "D",
        "GP", "GC", "SG", "Pontos", "Aproveitamento"
    ]

    st.dataframe(
        tabela_ano[colunas],
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Baixar classificação CSV",
        data=tabela_ano[colunas].to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"classificacao_brasileirao_{ano}.csv",
        mime="text/csv"
    )

    # Gráfico 1: pontos por clube
    st.subheader("Pontuação por clube")

    dados_grafico = tabela_ano.copy()

    if times:
        dados_grafico = dados_grafico[
            dados_grafico["Time"].isin(times)
        ]

    fig_pontos = px.bar(
        dados_grafico.sort_values("Pontos"),
        x="Pontos",
        y="Time",
        orientation="h",
        color="Pontos",
        color_continuous_scale="Blues",
        title=f"Pontos conquistados em {ano}",
        labels={"Pontos": "Pontos", "Time": "Clube"}
    )

    fig_pontos.update_layout(
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False
    )

    st.plotly_chart(fig_pontos, use_container_width=True)

    # Gráfico 2: gols pró x gols contra
    st.subheader("Ataque e defesa")

    fig_gols = px.scatter(
        dados_grafico,
        x="GP",
        y="GC",
        size="Pontos",
        color="Time",
        hover_name="Time",
        hover_data=["V", "E", "D", "SG"],
        labels={
            "GP": "Gols pró",
            "GC": "Gols contra"
        },
        title="Gols marcados versus gols sofridos"
    )

    st.plotly_chart(fig_gols, use_container_width=True)

    # Gráfico 3: evolução histórica
    st.subheader("Evolução histórica dos clubes")

    historico = tabelas.copy()

    if times:
        historico = historico[historico["Time"].isin(times)]

    if historico.empty:
        st.info("Selecione ao menos um clube para visualizar.")
    else:
        fig_evolucao = px.line(
            historico,
            x="Ano",
            y="Pontos",
            color="Time",
            markers=True,
            hover_data=["Posição", "V", "SG"],
            title="Pontos por temporada",
            labels={
                "Ano": "Temporada",
                "Pontos": "Pontos conquistados",
                "Time": "Clube"
            }
        )

        fig_evolucao.update_xaxes(
            tickmode="linear",
            dtick=1
        )

        st.plotly_chart(
            fig_evolucao,
            use_container_width=True
        )

    # Exportação histórica
    st.subheader("Exportar todas as temporadas")

    st.download_button(
        "⬇️ Baixar histórico completo CSV",
        data=tabelas[colunas].to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="brasileirao_2008_2017.csv",
        mime="text/csv"
    )

    st.caption(
        "Fonte: repositório público de resultados históricos. "
        "A classificação é recalculada a partir dos placares "
        "disponíveis; confira a integridade da base e os "
        "critérios oficiais de desempate antes de uso acadêmico."
    )

except Exception as erro:
    st.error("Não foi possível carregar ou processar os dados.")
    st.exception(erro)
    st.info(
        "Verifique sua conexão com a internet, o endereço da "
        "base CSV e os nomes das colunas."
    )
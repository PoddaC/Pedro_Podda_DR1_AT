import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import seaborn as sns

st.set_page_config(page_title="Europa vs América do Sul", layout="wide")

# --- IDs confirmados ---
Torneios = {
    "Copa América 2024": {"competition_id": 223, "season_id": 282, "continente":"América do Sul"},
    "UEFA Euro 2024": {"competition_id": 55, "season_id": 282, "continente":"Europa"},
}

# ---Carregamento com Cache ---
@st.cache_data(show_spinner=False)
def carregar_partidas(cid,sid):
    return sb.matches(competition_id=cid, season_id=sid)

@st.cache_data(show_spinner=False)
def carregar_eventos(match_id):
    return sb.events(match_id=match_id)

def por_partida(t, chave):
    return t[chave] / t["partidas"] if t["partidas"] else 0

@st.cache_data
def carregar_agregados():
    torneios = pd.read_csv("dados_torneios.csv").set_index("torneio")
    jogadores = pd.read_csv("dados_jogadores.csv")
    chutes = pd.read_csv("dados_chutes.csv")
    jogadores = consolidar_jogadores(jogadores)   # <-- junta os fragmentos
    return torneios, jogadores, chutes

def consolidar_jogadores(df):
    df = df.copy()
    df["acoes"] = df["passes"] + df["chutes"] + df["faltas"]
    # posição principal = aquela em que o jogador foi mais ativo
    idx = df.groupby(["jogador", "time", "continente"])["acoes"].idxmax()
    pos = df.loc[idx, ["jogador", "time", "continente", "posicao"]]
    # soma as estatísticas numéricas em uma linha por jogador
    num = df.groupby(["jogador", "time", "continente"], as_index=False)[
        ["gols", "chutes", "passes", "passes_certos", "faltas", "defesas", "gols_sofridos"]
    ].sum()
    out = num.merge(pos, on=["jogador", "time", "continente"], how="left")
    out["precisao_passe"] = (100 * out["passes_certos"] / out["passes"]).round(1)
    out["taxa_defesa"] = (100 * out["defesas"] / (out["defesas"] + out["gols_sofridos"])).round(1)
    out["taxa_defesa"] = out["taxa_defesa"].fillna(0)
    out["categoria"] = out["posicao"].apply(categoria_posicao)
    return out

def mapa_de_passes(eventos, jogador=None):
    """Mapa de passes de uma partida. Se jogador for informado, filtra só os dele."""
    passes = eventos[eventos["type"] == "Pass"].copy()
    if jogador and jogador != "Todos":
        passes = passes[passes["player"] == jogador]

    pitch = Pitch(pitch_type="statsbomb", line_color="black", pitch_color="white")
    fig, ax = pitch.draw(figsize=(8, 5))

    for _, p in passes.iterrows():
        inicio, fim = p["location"], p["pass_end_location"]
        if not (isinstance(inicio, list) and isinstance(fim, list)):
            continue
        completo = pd.isna(p.get("pass_outcome"))
        cor = "blue" if completo else "red"
        pitch.arrows(inicio[0], inicio[1], fim[0], fim[1],
                     ax=ax, color=cor, width=2, headwidth=4, alpha=0.6)
    return fig

def categoria_posicao(pos):
    pos = str(pos)
    if "Goalkeeper" in pos:
        return "Goleiro"
    if "Back" in pos or "Center Back" in pos:
        return "Defesa"
    if "Midfield" in pos:
        return "Meio"
    if "Forward" in pos or "Wing" in pos or "Striker" in pos:
        return "Ataque"
    return "Outro"

# =====INTERFACE=====
st.title("Futebol: Europa vs América do Sul")
st.caption("Comparativo entre torneios de seleções da Europa e América do Sul em 2024 (Dados StatsBomb)")

df_torneios, df_jogadores, df_chutes = carregar_agregados()

nomes = list(Torneios.keys()) # [Copa America, Euro]

aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs(
    ["Visao geral", "Estilo de jogo", "Intensidade fisica", "Finalizacao",
     "Partida individual", "Ranking", "Comparar jogadores"]
)

# Visão geral
with aba1:
    st.subheader("Media por partida")
    for nome in nomes:
        t = df_torneios.loc[nome]
        st.markdown(f"### {nome} — {Torneios[nome]['continente']}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gols/jogo", f"{por_partida(t, 'gols'):.2f}")
        c2.metric("Chutes/jogo", f"{por_partida(t, 'chutes'):.1f}")
        c3.metric("Passes/jogo", f"{por_partida(t, 'passes'):.0f}")
        c4.metric("Faltas/jogo", f"{por_partida(t, 'faltas'):.1f}")

# Estilo de jogo
with aba2:
    st.subheader("Volume e precisão de passes")
    tabela = []
    for nome in nomes:
        t = df_torneios.loc[nome]
        precisao = 100 * t["passes_certos"] / t["passes"] if t["passes"] else 0
        tabela.append({
            "Torneio": nome,
            "Passes/jogo": round(por_partida(t, "passes")),
            "Precisão (%)": round(precisao, 1),
        })
    df_estilo = pd.DataFrame(tabela).set_index("Torneio")
    st.dataframe(df_estilo)
    st.bar_chart(df_estilo["Passes/jogo"])

#Intensidade física
with aba3:
    st.subheader("Faltas e cartões")
    tabela = []
    for nome in nomes:
        t = df_torneios.loc[nome]
        tabela.append({
            "Torneio": nome,
            "Faltas/jogo": round(por_partida(t, "faltas"), 1),
            "Amarelos/jogo": round(por_partida(t, "amarelos"), 2),
            "Vermelhos (total)": int(t["vermelhos"]),
        })
    df_intensidade = pd.DataFrame(tabela).set_index("Torneio")
    st.dataframe(df_intensidade)

# Finalização
with aba4:
    st.subheader("Mapa de chutes agregado")
    col_a, col_b = st.columns(2)
    for coluna, nome in zip([col_a, col_b], nomes):
        with coluna:
            st.markdown(f"**{nome}**")
            chutes = df_chutes[df_chutes["torneio"] == nome]
            pitch = Pitch(pitch_type="statsbomb", half=True, line_color="black")
            fig, ax = pitch.draw(figsize=(6, 4))
            if not chutes.empty:
                gols = chutes[chutes["gol"]]
                nao = chutes[~chutes["gol"]]
                pitch.scatter(nao["x"], nao["y"], ax=ax, color="gray", s=15, alpha=0.4)
                pitch.scatter(gols["x"], gols["y"], ax=ax, color="red", s=40)
            st.pyplot(fig)
            conv = 100 * len(chutes[chutes["gol"]]) / len(chutes) if len(chutes) else 0
            st.metric("Conversão de chutes (%)", f"{conv:.1f}")

# Partida individual
with aba5:
    st.subheader("Análise de uma partida")

    torneio_ind = st.selectbox("Torneio", nomes, key="torneio_ind")
    t = Torneios[torneio_ind]
    partidas_ind = carregar_partidas(t["competition_id"], t["season_id"])
    partidas_ind["rotulo"] = partidas_ind["home_team"] + " x " + partidas_ind["away_team"]

    rotulo = st.selectbox("Partida", partidas_ind["rotulo"], key="partida_ind")
    match_id = int(partidas_ind[partidas_ind["rotulo"] == rotulo]["match_id"].iloc[0])

    with st.spinner("Carregando eventos da partida..."):
        ev = carregar_eventos(match_id)

    jogadores = ["Todos"] + sorted(ev["player"].dropna().unique().tolist())
    jogador = st.selectbox("Jogador", jogadores, key="jogador_ind")

    st.markdown("#### Mapa de passes")
    st.caption("Azul = passe completo · Vermelho = passe perdido")
    fig = mapa_de_passes(ev, jogador)
    st.pyplot(fig)

    # eventos filtrados + download CSV
    eventos_mostrar = ev if jogador == "Todos" else ev[ev["player"] == jogador]
    colunas = ["minute", "second", "type", "team", "player"]
    tabela_ev = eventos_mostrar[colunas]

    st.markdown("#### Eventos")
    st.dataframe(tabela_ev, use_container_width=True)

    csv = tabela_ev.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar eventos em CSV",
        data=csv,
        file_name=f"eventos_{rotulo}.csv",
        mime="text/csv",
    )

# Ranking de jogadores
with aba6:
    st.subheader("Ranking de jogadores")
    st.caption("Somatório de cada jogador nos dois torneios")

    metrica = st.selectbox("Ordenar por", ["gols", "passes", "chutes", "faltas", "precisao_passe", "defesas", "gols_sofridos", "taxa_defesa"], key="metrica_rank")
    top_n = st.slider("Quantos mostrar", 5, 30, 10, key="top_rank")

    categorias = ["Todas", "Goleiro", "Defesa", "Meio", "Ataque"]
    cat_escolhida = st.selectbox("Posição", categorias, key="cat_rank")

    base = df_jogadores if cat_escolhida == "Todas" else df_jogadores[df_jogadores["categoria"] == cat_escolhida]
    ranking = base.sort_values(metrica, ascending=False).head(top_n)

    st.dataframe(
        ranking[["jogador", "time", "continente", "categoria", metrica]],
        use_container_width=True,
    )

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=df_jogadores,
        x="chutes", y="gols",
        hue="continente",
        alpha=0.6, ax=ax,
    )
    ax.set_xlabel("Chutes no torneio")
    ax.set_ylabel("Gols no torneio")
    st.pyplot(fig)

# Comparar dois jogadores
with aba7:
    st.subheader("Comparar dois jogadores")

    categorias = ["Todas", "Goleiro", "Defesa", "Meio", "Ataque"]
    cat_comp = st.selectbox("Filtrar por posição", categorias, key="cat_comp")

    base = df_jogadores if cat_comp == "Todas" else df_jogadores[df_jogadores["categoria"] == cat_comp]
    lista = sorted(base["jogador"].unique())

    if len(lista) < 2:
        st.warning("Poucos jogadores nessa posição para comparar.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            j1 = st.selectbox("Jogador 1", lista, key="j1")
        with col2:
            j2 = st.selectbox("Jogador 2", lista, index=1, key="j2")

        d1 = base[base["jogador"] == j1].iloc[0]
        d2 = base[base["jogador"] == j2].iloc[0]

        st.markdown(f"**{j1}** ({d1['continente']} · {d1['categoria']}) × **{j2}** ({d2['continente']} · {d2['categoria']})")

        metricas = ["gols", "chutes", "passes", "faltas", "precisao_passe"]
        if d1["categoria"] == "Goleiro" and d2["categoria"] == "Goleiro":
            metricas = ["defesas", "gols_sofridos", "taxa_defesa", "passes", "precisao_passe"]
        for met in metricas:            
            c1, c2 = st.columns(2)
            c1.metric(f"{j1} — {met}", d1[met])
            c2.metric(f"{j2} — {met}", d2[met])
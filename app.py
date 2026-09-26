import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from statsbombpy import sb

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

@st.cache_data(show_spinner=False)
#Percorrer todas as partidas do torneio e soma as estatiscas
def agregar_torneio(cid,sid):
    partidas = carregar_partidas(cid,sid)
    match_ids = partidas['match_id'].tolist()

    tot={"gols": 0, "chutes": 0, "passes": 0, "passes_certos": 0,
        "faltas": 0, "amarelos": 0, "vermelhos": 0}

    for mid in match_ids:
        ev = carregar_eventos(mid)

        shots = ev[ev['type'] == 'Shot']
        passes = ev[ev['type'] == 'Pass']

        tot["chutes"] += len(shots)
        tot["gols"] += int((shots['shot_outcome'] == 'Goal').sum()) if 'shot_outcome' in ev.columns else 0
        tot["passes"] += len(passes)
        tot["passes_certos"] += int(passes["pass_outcome"].isna().sum()) if "pass_outcome" in ev.columns else len(passes)
        tot["faltas"] += int((ev["type"] == "Foul Committed").sum())

        if "foul_committed_card" in ev.columns:
            tot["amarelos"]  += int((ev["foul_committed_card"] == "Yellow Card").sum())
            tot["vermelhos"] += int(ev["foul_committed_card"].isin(["Red Card", "Second Yellow"]).sum())
    tot["partidas"] = len(match_ids)
    return tot

@st.cache_data(show_spinner=False)
def coletar_chutes(cid,sid):
    partidas = carregar_partidas(cid,sid)
    linhas = []
    for mid in partidas['match_id'].tolist():
        ev = carregar_eventos(mid)
        chutes = ev[ev['type'] == 'Shot']
        if "location" not in chutes.columns:
            continue
        for _, r in chutes.iterrows():
            loc = r["location"]
            if isinstance(loc, list) and len(loc) == 2:
                linhas.append({
                    "x":loc[0],
                    "y":loc[1],
                    "gol":r.get("shot_outcome") == "Goal",
                    })
    return pd.DataFrame(linhas)

def por_partida(tot, chave):
    return tot[chave] / tot["partidas"] if tot["partidas"] else 0

# =====INTERFACE=====
st.title("Futebol: Europa vs América do Sul")
st.caption("Comparativo entre torneios de seleções da Europa e América do Sul em 2024 (Dados StatsBomb)")

#Carregar os agregados de ambos torneios
with st.spinner("Carregando dados da Euro 2024 (Primeira vez mais demorada)..."):
    dados = {
        nome: agregar_torneio(t["competition_id"], t["season_id"])
        for nome, t in Torneios.items()
    }

nomes = list(Torneios.keys()) # [Copa America, Euro]

aba1, aba2, aba3, aba4 = st.tabs(
    ["Visao geral", "Estilo de jogo", "Intensidade fisica", "Finalizacao"]
)

# Visão geral
with aba1:
    st.subheader("Media por partida")
    for nome in nomes:
        t = dados[nome]
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
        t = dados[nome]
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
        t = dados[nome]
        tabela.append({
            "Torneio": nome,
            "Faltas/jogo": round(por_partida(t, "faltas"), 1),
            "Amarelos/jogo": round(por_partida(t, "amarelos"), 2),
            "Vermelhos (total)": t["vermelhos"],
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
            chutes = coletar_chutes(
                Torneios[nome]["competition_id"], Torneios[nome]["season_id"]
            )
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

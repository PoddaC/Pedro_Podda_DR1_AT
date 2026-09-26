"""Roda UMA vez, localmente, para gerar os CSVs que o app vai ler.
Não faz parte do app — é só pré-processamento."""
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from statsbombpy import sb

TORNEIOS = {
    "Copa América 2024": {"competition_id": 223, "season_id": 282, "continente": "América do Sul"},
    "UEFA Euro 2024":    {"competition_id": 55,  "season_id": 282, "continente": "Europa"},
}


def eventos_partida(mid):
    return sb.events(match_id=mid)


# 1) Agregados por torneio
linhas_torneio = []
# 2) Estatísticas por jogador
linhas_jogador = []
# 3) Coordenadas dos chutes (para os mapas)
linhas_chute = []

for nome, t in TORNEIOS.items():
    print(f"Processando {nome}...")
    partidas = sb.matches(competition_id=t["competition_id"], season_id=t["season_id"])
    match_ids = partidas["match_id"].tolist()

    tot = {"gols": 0, "chutes": 0, "passes": 0, "passes_certos": 0, "faltas": 0, "amarelos": 0, "vermelhos": 0}
    for i, mid in enumerate(match_ids, 1):
        print(f"  partida {i}/{len(match_ids)}")
        ev = eventos_partida(mid)

        shots = ev[ev["type"] == "Shot"]
        passes = ev[ev["type"] == "Pass"]

        tot["chutes"] += len(shots)
        tot["gols"] += int((shots["shot_outcome"] == "Goal").sum()) if "shot_outcome" in ev.columns else 0
        tot["passes"] += len(passes)
        tot["passes_certos"] += int(passes["pass_outcome"].isna().sum()) if "pass_outcome" in ev.columns else len(passes)
        tot["faltas"] += int((ev["type"] == "Foul Committed").sum())
        if "foul_committed_card" in ev.columns:
            tot["amarelos"] += int((ev["foul_committed_card"] == "Yellow Card").sum())
            tot["vermelhos"] += int(ev["foul_committed_card"].isin(["Red Card", "Second Yellow"]).sum())
            
        # chutes com coordenada
        for _, r in shots.iterrows():
            loc = r["location"]
            if isinstance(loc, list) and len(loc) == 2:
                linhas_chute.append({
                    "torneio": nome, "continente": t["continente"],
                    "x": loc[0], "y": loc[1],
                    "gol": r.get("shot_outcome") == "Goal",
                })

        # por jogador
        evj = ev[ev["player"].notna()]
        for jogador, g in evj.groupby("player"):
            s = g[g["type"] == "Shot"]
            p = g[g["type"] == "Pass"]
            linhas_jogador.append({
                "jogador": jogador, "time": g["team"].iloc[0],
                "continente": t["continente"],
                "gols": int((s["shot_outcome"] == "Goal").sum()) if "shot_outcome" in g.columns else 0,
                "chutes": len(s), "passes": len(p),
                "passes_certos": int(p["pass_outcome"].isna().sum()) if "pass_outcome" in g.columns else len(p),
                "faltas": int((g["type"] == "Foul Committed").sum()),
            })

    tot["torneio"] = nome
    tot["continente"] = t["continente"]
    tot["partidas"] = len(match_ids)
    linhas_torneio.append(tot)

# --- salva os CSVs ---
pd.DataFrame(linhas_torneio).to_csv("dados_torneios.csv", index=False)

df_j = pd.DataFrame(linhas_jogador)
df_j = df_j.groupby(["jogador", "time", "continente"], as_index=False).sum()
df_j["precisao_passe"] = (100 * df_j["passes_certos"] / df_j["passes"]).round(1)
df_j.to_csv("dados_jogadores.csv", index=False)

pd.DataFrame(linhas_chute).to_csv("dados_chutes.csv", index=False)

print("Pronto! CSVs gerados: dados_torneios.csv, dados_jogadores.csv, dados_chutes.csv")
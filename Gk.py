import warnings
warnings.filterwarnings("ignore")
from statsbombpy import sb

partidas = sb.matches(competition_id=55, season_id=282)
ev = sb.events(match_id=partidas["match_id"].iloc[0])

gk = ev[ev["type"] == "Goal Keeper"]
print("Colunas de goleiro:", [c for c in ev.columns if "goalkeeper" in c])
print("\ngoalkeeper_type (valores):")
print(gk["goalkeeper_type"].value_counts())
print("\ngoalkeeper_outcome (valores):")
if "goalkeeper_outcome" in gk.columns:
    print(gk["goalkeeper_outcome"].value_counts())
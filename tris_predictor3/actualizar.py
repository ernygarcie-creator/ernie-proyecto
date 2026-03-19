"""
actualizar.py — Recalcula tris_data.json desde el Excel histórico
Uso: python actualizar.py
"""

import pandas as pd
import numpy as np
import json
import warnings
from collections import Counter, defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")

# ── CONFIGURACIÓN ──────────────────────────────────────────────────
EXCEL_PATH  = "Tris_para_analizar.xlsx"   # ← cambia si tu archivo tiene otro nombre
OUTPUT_PATH = "data/tris_data.json"
FECHA_CAMBIO = pd.Timestamp("2007-09-03")
# ──────────────────────────────────────────────────────────────────

def sp(p): return sum(int(c) for c in str(p))

def calcular_stats(seq, fechas_seq, digitos):
    """Calcula estadísticas para una secuencia de resultados."""
    n = len(seq)
    if n == 0: return {}
    conteo = Counter(seq)

    def rezago(p):
        for i in range(len(seq)-1, -1, -1):
            if seq[i] == p: return len(seq)-1-i
        return n

    def intervalos(p):
        pos = [i for i,x in enumerate(seq) if x==p]
        if len(pos) < 2: return None, None, None
        intv = [pos[k]-pos[k-1] for k in range(1, len(pos))]
        return round(np.mean(intv), 1), min(intv), max(intv)

    result = {}
    if digitos <= 2:
        combos = [str(i) for i in range(10)] if digitos==1 else \
                 [f"{a}{b}" for a in range(10) for b in range(10)]
        for p in combos:
            veces = conteo.get(p, 0)
            rez   = rezago(p)
            ip, imin, imax = intervalos(p)
            pos_p = [i for i,x in enumerate(seq) if x==p]
            uf    = fechas_seq[pos_p[-1]].strftime("%Y-%m-%d") if pos_p else "Nunca"
            u100  = seq[-100:].count(p)  if n >= 100  else seq.count(p)
            u200  = seq[-200:].count(p)  if n >= 200  else seq.count(p)
            u300  = seq[-300:].count(p)  if n >= 300  else seq.count(p)
            u500  = seq[-500:].count(p)  if n >= 500  else seq.count(p)
            u1000 = seq[-1000:].count(p) if n >= 1000 else seq.count(p)
            result[p] = {
                "par": p, "suma": sp(p), "zona": (5 <= sp(p) <= 13) if digitos==2 else None,
                "veces_total": veces, "por_100": round(veces/n*100, 3),
                "rezago_real": rez, "ultima_fecha": uf,
                "ult100": u100, "ult200": u200, "ult300": u300,
                "ult500": u500, "ult1000": u1000,
                "intervalo_prom": ip, "intervalo_min": imin, "intervalo_max": imax,
            }
    else:
        for p, veces in conteo.items():
            rez = rezago(p)
            ip, imin, imax = intervalos(p)
            pos_p = [i for i,x in enumerate(seq) if x==p]
            uf = fechas_seq[pos_p[-1]].strftime("%Y-%m-%d") if pos_p else "Nunca"
            result[p] = {
                "par": p, "suma": sp(p), "veces_total": veces,
                "por_n": round(veces/n*100, 4), "rezago_real": rez, "ultima_fecha": uf,
                "ult100": seq[-100:].count(p) if n>=100 else seq.count(p),
                "intervalo_prom": ip, "intervalo_min": imin, "intervalo_max": imax,
            }
    return result

def calcular_contexto(sumas_seq, seq, n):
    """Calcula el contexto de sumas para el analizador de par_final."""
    ctx2  = tuple(sumas_seq[-2:])
    ctx5  = tuple(sumas_seq[-5:])
    ctx10 = tuple(sumas_seq[-10:])
    ctx15 = tuple(sumas_seq[-15:])

    def matches_aprox(k, ctx, strict_last=2):
        prom_actual = np.mean(ctx)
        ctx_tail    = ctx[-strict_last:]
        matches     = []
        for i in range(k, n):
            tail = tuple(sumas_seq[i-strict_last:i])
            if tail == ctx_tail:
                prom_hist = np.mean(sumas_seq[i-k:i])
                if abs(prom_hist - prom_actual) <= 1.5:
                    matches.append(i)
        return matches

    matches = {
        "2":  [i for i in range(2,n) if tuple(sumas_seq[i-2:i])==ctx2],
        "5":  matches_aprox(5,  ctx5),
        "10": matches_aprox(10, ctx10),
        "15": matches_aprox(15, ctx15),
    }

    def build_gc(m):
        if not m: return {"n":0,"top_pares":[],"top_sumas":[],"pct_zona":0}
        sig = [seq[i] for i in m if i<n]
        cnt = Counter(sig)
        scnt = Counter(sp(p) for p in sig)
        pz  = sum(c for p,c in cnt.items() if 5<=sp(p)<=13) / len(sig) * 100 if sig else 0
        return {"n":len(sig),"top_pares":cnt.most_common(10),
                "top_sumas":scnt.most_common(9),"pct_zona":round(pz,1)}

    global_ctx = {k: build_gc(m) for k,m in matches.items()}
    global_ctx.update({
        "ctx2_sumas":  list(ctx2),  "ctx5_sumas":  list(ctx5),
        "ctx10_sumas": list(ctx10), "ctx15_sumas": list(ctx15),
    })

    par_ctx = {}
    todos = [f"{a}{b}" for a in range(10) for b in range(10)]
    for p in todos:
        par_ctx[p] = {}
        pos_p = [i for i,x in enumerate(seq) if x==p]
        for k_str, m in matches.items():
            k = int(k_str)
            if not m:
                par_ctx[p][k_str] = {"n_ctx":0,"n_p_siguiente":0,"n_p_prox5":0,"pct":0,"sig_cuando_p":[]}
                continue
            exactos = [pos for pos in pos_p if pos>=k and
                       tuple(sumas_seq[pos-k:pos])==(ctx2 if k==2 else ctx5 if k==5 else ctx10 if k==10 else ctx15)]
            n_sig   = sum(1 for i in m if i<n and seq[i]==p)
            n_prox5 = sum(1 for i in m if i<n and p in seq[i:min(i+5,n)])
            sig_sp  = Counter(seq[pos+1] for pos in exactos if pos+1<n)
            par_ctx[p][k_str] = {
                "n_ctx": len(m), "n_p_siguiente": n_sig, "n_p_prox5": n_prox5,
                "pct": round(n_sig/len(m)*100,1) if m else 0,
                "sig_cuando_p": sig_sp.most_common(5),
            }
    return par_ctx, global_ctx

def main():
    print(f"Cargando {EXCEL_PATH}...")
    df = pd.read_excel(EXCEL_PATH)
    for c in df.columns:
        if "fecha" in c.lower(): df.rename(columns={c:"fecha"}, inplace=True); break
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)
    df["era"] = df["fecha"].apply(lambda d: "5c" if d >= FECHA_CAMBIO else "4c")
    for c in ["R1","R2","R3","R4","R5"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Extraer modalidades
    mods = {k: [] for k in ["num_final","num_inicial","par_final","par_inicial","dir3","dir4","dir5"]}
    fechas_all = []
    for _, row in df.iterrows():
        try:
            era = row["era"]
            if era == "5c":
                r = [int(row[f"R{i}"]) for i in range(1,6)]
                mods["num_inicial"].append(str(r[0]))
                mods["num_final"].append(str(r[4]))
                mods["par_inicial"].append(f"{r[0]}{r[1]}")
                mods["par_final"].append(f"{r[3]}{r[4]}")
                mods["dir3"].append(f"{r[2]}{r[3]}{r[4]}")
                mods["dir4"].append(f"{r[1]}{r[2]}{r[3]}{r[4]}")
                mods["dir5"].append(f"{r[0]}{r[1]}{r[2]}{r[3]}{r[4]}")
            else:
                r = [int(row[f"R{i}"]) for i in range(1,5)]
                mods["num_inicial"].append(str(r[0]))
                mods["num_final"].append(str(r[3]))
                mods["par_inicial"].append(f"{r[0]}{r[1]}")
                mods["par_final"].append(f"{r[2]}{r[3]}")
                mods["dir3"].append(f"{r[1]}{r[2]}{r[3]}")
                mods["dir4"].append(f"{r[0]}{r[1]}{r[2]}{r[3]}")
                mods["dir5"].append(None)
            fechas_all.append(row["fecha"])
        except: continue

    n_total = len(fechas_all)
    ultima_fecha = fechas_all[-1].strftime("%Y-%m-%d")
    print(f"✓ {n_total} sorteos cargados. Último: {ultima_fecha}")

    output = {"num_final":{},"num_inicial":{},"par_final":{},"par_inicial":{},"dir3":{},"dir4":{},"dir5":{}}

    for mod_key in mods:
        dig = {"num_final":1,"num_inicial":1,"par_final":2,"par_inicial":2,"dir3":3,"dir4":4,"dir5":5}[mod_key]
        seq_raw = mods[mod_key]
        seq     = [x for x in seq_raw if x is not None]
        fechas  = [fechas_all[i] for i,x in enumerate(seq_raw) if x is not None]
        n_k     = len(seq)

        print(f"  Calculando {mod_key} ({n_k} sorteos, {dig} dígitos)...", end=" ")

        stats = calcular_stats(seq, fechas, dig)
        frec_suma = {}
        if dig <= 2:
            sc = Counter(sp(p) for p in seq)
            frec_suma = {str(s): round(sc.get(s,0)/n_k*100,3) for s in range(19)}

        suma_dist = {}
        sc_all = Counter(sp(p) for p in seq)
        for s,c in sc_all.items():
            suma_dist[str(s)] = {"cnt":c,"pct":round(c/n_k*100,3)}

        obj = {
            "n": n_k, "digitos": dig,
            "ultimo": seq[-1] if seq else None,
            "ultimos_10": seq[-10:],
            "suma_dist": suma_dist,
        }

        if dig <= 2:
            obj["par_data"] = stats
            obj["frec_suma_pct"] = frec_suma
            obj["suma_movil"] = sum(int(p) for p in seq[-100:]) if n_k>=100 else None
            zona = [p for p,d in stats.items() if d.get("zona")]
            obj["top_retraso"] = sorted(zona, key=lambda p:-stats[p].get("rezago_real",0))[:30]
            obj["top_rec100"]  = sorted(zona, key=lambda p:-stats[p].get("ult100",0))[:30]
            obj["top_rec500"]  = sorted(zona, key=lambda p:-stats[p].get("ult500",0))[:30]
            obj["ult100_cnt"]  = dict(Counter(seq[-100:]))
        elif dig == 3:
            obj["par_data"] = stats
            obj["ult100_cnt"] = dict(Counter(seq[-100:]))
            obj["top_retraso"] = sorted(stats.keys(), key=lambda p:-stats[p].get("rezago_real",0))[:30]
            obj["top_rec100"]  = sorted(stats.keys(), key=lambda p:-stats[p].get("ult100",0))[:30]
        else:
            # dir4/dir5: índice compacto [suma, veces, rezago, ultima_fecha]
            obj["idx"] = {p: [d["suma"],d["veces_total"],d["rezago_real"],d["ultima_fecha"]]
                          for p,d in stats.items()}

        if mod_key == "par_final":
            print("calculando contexto...", end=" ")
            sumas_seq = [sp(p) for p in seq]
            par_ctx, global_ctx = calcular_contexto(sumas_seq, seq, n_k)
            obj["par_ctx"]    = par_ctx
            obj["global_ctx"] = global_ctx

        output[mod_key] = obj
        print("✓")

    # Guardar
    Path("data").mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(',',':'))
    size = Path(OUTPUT_PATH).stat().st_size
    print(f"\n✓ {OUTPUT_PATH} guardado ({size//1024} KB)")
    print(f"  Última fecha: {ultima_fecha}")
    print(f"  Total sorteos: {n_total}")

if __name__ == "__main__":
    main()

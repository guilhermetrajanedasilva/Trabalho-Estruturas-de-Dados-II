import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

COLUNAS_FEATURES = ["z_robusto", "aumento_pct", "jitter_relativo", "perda_pct",
                    "timeout_atual", "n5_timeout", "n5_aumento80", "n5_risco"]
# Dicionário v0.2 — colunas que a árvore NÃO pode ler
COLUNAS_PROIBIDAS = ["fluxo_id", "pais", "ip / dst_addr", "rota_id", "timestamp",
                     "rtt_ms (RTT absoluto)", "jitter_ms (absoluto)", "regra_disparada",
                     "criterio_risco_atual", "split", "classe (é o alvo, não entrada)"]
COLS_FICHA = ["mediana", "mad", "iqr", "jitter_tipico", "perda_tipica", "prop_resposta"]


# --------------------------------------------------------------------------- #
# Infra
# --------------------------------------------------------------------------- #
def pastas_do_projeto(base: Path) -> dict:
    p = {"base": base, "config": base / "config", "raw": base / "data" / "raw",
         "raw_json": base / "data" / "raw" / "json", "interim": base / "data" / "interim",
         "processed": base / "data" / "processed", "reports": base / "reports"}
    for k in ("interim", "processed", "reports"):
        p[k].mkdir(parents=True, exist_ok=True)
    return p


def ler_json(caminho: Path) -> dict:
    if not caminho.exists():
        sys.exit(f"Arquivo não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding="utf-8"))


def epoch(iso_utc: str) -> int:
    return int(pd.Timestamp(iso_utc).timestamp())


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# 1. Inspeção do bruto (ainda sem rótulo)
# --------------------------------------------------------------------------- #
def inspecionar(pastas, cfg_col) -> tuple:
    csv = pastas["raw"] / "ping_bruto.csv"
    if not csv.exists():
        sys.exit(f"Bruto da Tarefa 1 não encontrado: {csv}\nRode antes: python coleta_bruta.py")
    df = pd.read_csv(csv, dtype={"fluxo_id": str, "dst_addr": str})
    obrig = {"timestamp", "timestamp_epoch", "measurement_id", "probe_id", "dst_addr", "fluxo_id",
             "rtt_avg_ms", "enviados", "recebidos", "perda_pct", "jitter_ms", "timeout_atual"}
    faltam = obrig - set(df.columns)
    if faltam:
        sys.exit(f"Colunas ausentes no bruto: {sorted(faltam)}")

    a0, a1 = epoch(cfg_col["periodo_a"]["inicio_utc"]), epoch(cfg_col["periodo_a"]["fim_utc"])
    b0, b1 = epoch(cfg_col["periodo_b"]["inicio_utc"]), epoch(cfg_col["periodo_b"]["fim_utc"])
    assert a1 <= b0, "Períodos A e B se sobrepõem"

    ins = {"n_bruto": int(len(df)), "n_fluxos": int(df["fluxo_id"].nunique())}
    chave = ["measurement_id", "probe_id", "timestamp_epoch"]
    ins["duplicatas"] = int(df.duplicated(chave).sum())
    ins["rtt_vazio"] = int(df["rtt_avg_ms"].isna().sum())
    ins["rtt_gravado_como_zero_ou_negativo"] = int((df["rtt_avg_ms"] <= 0).sum())  # tem de ser 0
    ins["jitter_zero_com_menos_de_2_respostas"] = int(((df["jitter_ms"] == 0) & (df["recebidos"] < 2)).sum())
    ins["timeouts"] = int(df["timeout_atual"].sum())

    df = df.drop_duplicates(chave)
    # o período é recalculado pelo timestamp (não se confia só na coluna da Tarefa 1)
    df["periodo"] = np.select([df["timestamp_epoch"].between(a0, a1 - 1), df["timestamp_epoch"].between(b0, b1 - 1)],
                              ["A", "B"], default="fora")
    ins["linhas_fora_de_A_e_B"] = int((df["periodo"] == "fora").sum())
    df = df[df["periodo"] != "fora"]
    comp = df.groupby(["fluxo_id", "periodo"])["timestamp_epoch"].apply(set).unstack()
    ins["fluxos_com_timestamp_em_A_e_B"] = int(sum(
        1 for _, r in comp.iterrows()
        if isinstance(r.get("A"), set) and isinstance(r.get("B"), set) and (r["A"] & r["B"])))
    ins["n_periodo_A"] = int((df["periodo"] == "A").sum())
    ins["n_periodo_B"] = int((df["periodo"] == "B").sum())

    # o bruto da Tarefa 1 não pode ter sido alterado
    meta = pastas["raw"] / "metadados_coleta.json"
    alterados = []
    if meta.exists():
        for nome, h in ler_json(meta).get("sha256_json_bruto", {}).items():
            arq = pastas["raw_json"] / nome
            if not arq.exists() or sha256(arq) != h:
                alterados.append(nome)
    ins["json_bruto_alterado_ou_ausente"] = alterados

    df = df.sort_values(["fluxo_id", "timestamp_epoch"]).reset_index(drop=True)
    df.to_csv(pastas["interim"] / "ping_trabalho.csv", index=False, encoding="utf-8")
    return df, ins


# --------------------------------------------------------------------------- #
# 2. Baseline por fluxo — só Período A
# --------------------------------------------------------------------------- #
def ficha_do_fluxo(fluxo_id: str, a: pd.DataFrame, piso: int) -> dict:
    rtt = a["rtt_avg_ms"]
    validos = rtt[rtt > 0].dropna()  # timeout fica FORA da mediana e do MAD
    ficha = {"fluxo_id": fluxo_id, "n_medicoes_A": int(len(a)), "n_rtt_validos_A": int(len(validos)),
             **{c: np.nan for c in COLS_FICHA}}
    if len(validos) < piso:
        ficha.update(status="baseline_insuficiente",
                     motivo=f"{len(validos)} RTT válidos no Período A (< {piso}); fluxo não recebe classe")
        return ficha
    mediana = validos.median()
    jit = a["jitter_ms"].dropna()
    perda = a["perda_pct"].dropna()  # inclui timeouts (perda 100)
    ficha.update(
        mediana=mediana,
        mad=(validos - mediana).abs().median(),
        iqr=validos.quantile(0.75) - validos.quantile(0.25),  # só usado se MAD = 0
        jitter_tipico=jit.median() if len(jit) else np.nan,
        perda_tipica=perda.median() if len(perda) else np.nan,
        prop_resposta=len(validos) / len(a),
        status="ok", motivo="")
    return ficha


def calcular_baseline(df, cfg_col, cfg_rot, pastas, recalcular: bool) -> pd.DataFrame:
    piso = cfg_rot["piso_rtt_validos_periodo_a"]
    a_todo = df[df["periodo"] == "A"]  # o Período B nem entra na conta
    fichas = [ficha_do_fluxo(fid, g.sort_values("timestamp_epoch"), piso) for fid, g in a_todo.groupby("fluxo_id")]
    # pares do config sem nenhum dado no A entram como excluídos (lista completa de exclusões)
    vistos = {f["fluxo_id"] for f in fichas}
    for par in cfg_col["pares"]:
        fid = f"{par['probe_id']}|{par['dst_addr']}"
        if fid not in vistos:
            fichas.append(ficha_do_fluxo(fid, a_todo.iloc[0:0], piso))
    ficha = pd.DataFrame(fichas).sort_values("fluxo_id").reset_index(drop=True)
    cols = ["fluxo_id", "status", "motivo", "n_medicoes_A", "n_rtt_validos_A"] + COLS_FICHA
    ficha = ficha[cols]

    destino = pastas["processed"] / "baseline_por_fluxo.csv"
    if destino.exists() and not recalcular:
        antiga = pd.read_csv(destino, dtype={"fluxo_id": str}).sort_values("fluxo_id").reset_index(drop=True)
        iguais = (list(antiga["fluxo_id"]) == list(ficha["fluxo_id"]) and list(antiga["status"]) == list(ficha["status"])
                  and np.allclose(antiga[COLS_FICHA].astype(float).to_numpy(),
                                  ficha[COLS_FICHA].astype(float).to_numpy(), equal_nan=True, rtol=1e-9))
        if not iguais:
            sys.exit("O baseline congelado difere do recalculado a partir do Período A.\n"
                     "O Período A é congelado: se o bruto mudou de propósito, versione e rode com --recalcular-baseline.")
        print(f"Baseline já congelado e idêntico: {destino}")
    else:
        ficha.to_csv(destino, index=False, encoding="utf-8")
        print(f"Baseline gravado e congelado: {destino}")
    return ficha


# --------------------------------------------------------------------------- #
# 3. Métricas de cada medição do Período B (só com a ficha congelada)
# --------------------------------------------------------------------------- #
def metricas_do_fluxo(b: pd.DataFrame, f: pd.Series, cfg_rot: dict) -> pd.DataFrame:
    lim, n = cfg_rot["limiares"], cfg_rot["janela_ultimas_n"]
    b = b.sort_values("timestamp_epoch").copy()
    rtt = b["rtt_avg_ms"].where(b["rtt_avg_ms"] > 0)  # RTT ausente continua ausente (nunca 0)
    med, mad, iqr = f["mediana"], f["mad"], f["iqr"]
    dev = rtt - med

    if mad > 0:
        z = dev / (cfg_rot["mad_escala"] * mad)
    else:  # MAD = 0: RTT = mediana -> z = 0; senão denominador = max(IQR/1,349; 1 ms)
        den = max(iqr / cfg_rot["iqr_divisor"], cfg_rot["denominador_minimo_ms"])
        z = (dev / den).where(dev != 0, 0.0)
    aumento = dev / med * 100 if med > 0 else pd.Series(np.nan, index=b.index)

    ja, jt = b["jitter_ms"], f["jitter_tipico"]
    if pd.isna(jt):
        jrel = pd.Series(np.nan, index=b.index)
    elif jt == 0:  # jitter típico 0: atual 0 -> 1; atual > 0 -> trata como >= 3
        jrel = pd.Series(np.where(ja.isna(), np.nan, np.where(ja == 0, 1.0, float(lim["risco_jitter_relativo"]))), index=b.index)
    else:
        jrel = ja / jt  # jitter atual vazio -> NaN -> o critério de jitter não dispara

    perda = b["perda_pct"]
    timeout = (rtt.isna() | (perda == 100)).astype(int)
    crit_risco = (((z >= lim["risco_z_min"]) & (z < lim["falha_z_robusto"]))
                  | ((aumento >= lim["risco_aumento_min_pct"]) & (aumento <= lim["risco_aumento_max_pct"]))
                  | (jrel >= lim["risco_jitter_relativo"])).astype(int)

    def ult(s):  # últimas n medições do fluxo, incluindo a atual, SÓ dentro do Período B
        return s.rolling(n, min_periods=1).sum().astype(int)

    return pd.DataFrame({
        "timestamp": b["timestamp"], "timestamp_epoch": b["timestamp_epoch"], "fluxo_id": b["fluxo_id"],
        "rtt_ms": rtt, "jitter_ms": ja,
        "z_robusto": z, "aumento_pct": aumento, "jitter_relativo": jrel, "perda_pct": perda,
        "timeout_atual": timeout,
        "n5_timeout": ult(timeout),
        "n5_aumento80": ult((aumento > lim["aumento_alto_pct"]).astype(int)),
        "criterio_risco_atual": crit_risco,
        "n5_risco": ult(crit_risco),
    })


# --------------------------------------------------------------------------- #
# 4. Rotulagem — tabela aplicada na ordem; a primeira linha verdadeira vence
# --------------------------------------------------------------------------- #
def rotular(m: pd.DataFrame, cfg_rot: dict) -> pd.DataFrame:
    lim = cfg_rot["limiares"]
    cond = [
        m["perda_pct"] >= lim["falha_perda_pct"],                          # 1 FALHA
        m["n5_timeout"] >= lim["falha_n5_timeout"],                        # 2 FALHA
        (m["z_robusto"] >= lim["falha_z_robusto"]) & m["rtt_ms"].notna(),  # 3 FALHA
        m["n5_aumento80"] >= lim["falha_n5_aumento80"],                    # 4 FALHA
        (m["criterio_risco_atual"] == 1) & (m["n5_risco"] >= lim["risco_n5_risco_min"]),  # 5 RISCO
    ]
    m = m.copy()
    m["regra_disparada"] = np.select(cond, ["1_perda", "2_n5_timeout", "3_z_robusto", "4_n5_aumento80", "5_risco"],
                                     default="6_ok")
    m["classe"] = np.select(cond, ["FALHA", "FALHA", "FALHA", "FALHA", "RISCO"], default="OK")
    return m


# --------------------------------------------------------------------------- #
# 5. Recorte temporal dentro de B (50/20/30, ajustado se faltar RISCO)
# --------------------------------------------------------------------------- #
def atribuir_split(d: pd.DataFrame, p_tr: float, p_va: float) -> pd.Series:
    g = d.groupby("fluxo_id")["timestamp_epoch"]
    frac = g.cumcount() / g.transform("size")  # d já está em ordem de tempo por fluxo
    return pd.Series(np.where(frac < p_tr, "treino", np.where(frac < p_tr + p_va, "validacao", "teste")), index=d.index)


def escolher_recorte(d: pd.DataFrame, cfg_rot: dict) -> tuple:
    r = cfg_rot["recorte"]
    alvo = (r["treino"], r["validacao"], r["teste"])

    def todos_com_risco(sp):
        return all((d.loc[sp == s, "classe"] == "RISCO").any() for s in ("treino", "validacao", "teste"))

    sp = atribuir_split(d, alvo[0], alvo[1])
    if todos_com_risco(sp):
        return sp, alvo, False
    passo, candidatos = r["passo_ajuste"], []
    for tr in np.arange(0.40, 0.701, passo):
        for va in np.arange(0.10, 0.301, passo):
            te = 1 - tr - va
            if te >= 0.20 - 1e-9:
                s = atribuir_split(d, tr, va)
                if todos_com_risco(s):
                    candidatos.append((abs(tr - alvo[0]) + abs(va - alvo[1]) + abs(te - alvo[2]), tr, va, te))
    if candidatos:
        _, tr, va, te = min(candidatos)
        return atribuir_split(d, tr, va), (round(tr, 2), round(va, 2), round(te, 2)), True
    print("AVISO: nenhuma proporção próxima de 50/20/30 deixa RISCO em todos os blocos; mantida a de partida.")
    return sp, alvo, False


def tabela_de_corte(d: pd.DataFrame) -> pd.DataFrame:
    linhas = []
    for fid, g in d.groupby("fluxo_id"):
        r = {"fluxo_id": fid}
        for s in ("treino", "validacao", "teste"):
            x = g[g["split"] == s]
            r[f"n_{s}"] = len(x)
            r[f"inicio_{s}"] = x["timestamp"].min() if len(x) else None
            r[f"fim_{s}"] = x["timestamp"].max() if len(x) else None
        linhas.append(r)
    return pd.DataFrame(linhas)


# --------------------------------------------------------------------------- #
# Exemplos auditáveis (curto/longo, RISCO, FALHA)
# --------------------------------------------------------------------------- #
def exemplos_auditaveis(d: pd.DataFrame, ficha_ok: pd.DataFrame) -> pd.DataFrame:
    ordem = ficha_ok.sort_values("mediana")
    curto, longo = ordem.iloc[0]["fluxo_id"], ordem.iloc[-1]["fluxo_id"]
    ex = []
    ok = d[(d["fluxo_id"] == longo) & (d["classe"] == "OK") & (d["z_robusto"].abs() < 1)]
    if len(ok):
        ex.append(("OK em caminho longo (RTT alto, z_robusto baixo)", ok.iloc[0]))
    risco = d[d["classe"] == "RISCO"]
    if len(risco):
        ex.append(("RISCO", risco.iloc[0]))
    falha = pd.DataFrame()
    for filtro in ((d["fluxo_id"] == curto) & (d["timeout_atual"] == 1),   # preferência: timeout em caminho curto
                   d["timeout_atual"] == 1,
                   d["fluxo_id"] == curto,
                   d["classe"] == "FALHA"):
        falha = d[(d["classe"] == "FALHA") & filtro]
        if len(falha):
            break
    if len(falha):
        ex.append(("FALHA (caminho curto ou timeout)", falha.iloc[0]))
    out = pd.DataFrame([{"exemplo": nome, **r.to_dict()} for nome, r in ex])
    out.attrs["curto"], out.attrs["longo"] = curto, longo
    return out


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Tarefa 2 — baseline por fluxo e rotulagem do Período B")
    ap.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--drive", nargs="?", const="", default=None, metavar="PASTA",
                    help="Google Colab: salva tudo em Meu Drive/PASTA (padrão: netvision)")
    ap.add_argument("--recalcular-baseline", action="store_true",
                    help="regrava o baseline congelado (só se o bruto foi versionado de propósito)")
    args = ap.parse_args()
    from drive_colab import resolver_base
    pastas = pastas_do_projeto(resolver_base(args.base_dir, args.drive))
    cfg_col = ler_json(pastas["config"] / "config_coleta.json")
    cfg_rot = ler_json(pastas["config"] / "config_rotulagem.json")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", None)

    print("== 1. Inspeção do bruto (sem rótulo) ==")
    df, ins = inspecionar(pastas, cfg_col)
    for k, v in ins.items():
        print(f"  {k}: {v}")
    if ins["rtt_gravado_como_zero_ou_negativo"] or ins["fluxos_com_timestamp_em_A_e_B"] or ins["json_bruto_alterado_ou_ausente"]:
        print("  AVISO: o bruto viola uma regra da Tarefa 1; revise antes de seguir.")

    print("\n== 2. Baseline por fluxo (somente Período A) ==")
    ficha = calcular_baseline(df, cfg_col, cfg_rot, pastas, args.recalcular_baseline)
    print(ficha.to_string(index=False))
    com_ficha = ficha[ficha["status"] == "ok"]
    excluidos = ficha[ficha["status"] != "ok"]
    print(f"\n  fluxos com ficha: {len(com_ficha)} | excluídos: {len(excluidos)}")
    for r in excluidos.itertuples():
        print(f"    excluído {r.fluxo_id}: {r.motivo}")
    if com_ficha.empty:
        sys.exit("Nenhum fluxo com baseline suficiente; nada a rotular.")

    print("\n== 3 e 4. Métricas e rótulo do Período B ==")
    b_todo = df[df["periodo"] == "B"]
    partes = []
    for _, f in com_ficha.iterrows():
        b = b_todo[b_todo["fluxo_id"] == f["fluxo_id"]]
        if len(b):
            partes.append(rotular(metricas_do_fluxo(b, f, cfg_rot), cfg_rot))
    if not partes:
        sys.exit("Sem medições do Período B nos fluxos com ficha.")
    d = pd.concat(partes, ignore_index=True).sort_values(["fluxo_id", "timestamp_epoch"]).reset_index(drop=True)
    contagem = d["classe"].value_counts().reindex(["OK", "RISCO", "FALHA"], fill_value=0)
    print("  contagem OK / RISCO / FALHA:", contagem.to_dict())
    print("  regra que disparou:", d["regra_disparada"].value_counts().sort_index().to_dict())
    print("  por fluxo:\n" + pd.crosstab(d["fluxo_id"], d["classe"]).to_string())

    print("\n== 5. Recorte temporal dentro de B ==")
    d["split"], props, ajustado = escolher_recorte(d, cfg_rot)
    corte = tabela_de_corte(d)
    n_split = d["split"].value_counts().reindex(["treino", "validacao", "teste"], fill_value=0)
    print(f"  proporção usada: {props} ({'ajustada' if ajustado else 'de partida'}) | N: {n_split.to_dict()}")
    print(pd.crosstab(d["split"], d["classe"]).to_string())
    print(corte.to_string(index=False))
    assert d["timestamp_epoch"].min() >= epoch(cfg_col["periodo_b"]["inicio_utc"]), "há registro do Período A no dataset rotulado"

    # saídas
    d_out = d[["timestamp", "fluxo_id", "split", "rtt_ms", "jitter_ms"] + COLUNAS_FEATURES
              + ["criterio_risco_atual", "classe", "regra_disparada"]]
    d_out.to_csv(pastas["processed"] / "dataset_rotulado_B.csv", index=False, encoding="utf-8")
    corte.to_csv(pastas["processed"] / "corte_temporal.csv", index=False, encoding="utf-8")
    (pastas["processed"] / "colunas_arvore.json").write_text(json.dumps(
        {"entradas_permitidas": COLUNAS_FEATURES, "alvo": "classe", "proibidas": COLUNAS_PROIBIDAS},
        ensure_ascii=False, indent=2), encoding="utf-8")
    # país/IP/rota ficam FORA do dataset da árvore, só em arquivo de auditoria
    aud = df.drop_duplicates("fluxo_id")[["fluxo_id", "par_id", "probe_pais", "probe_cidade", "anchor_pais", "anchor_cidade", "dst_addr"]] \
        if "probe_pais" in df.columns else None
    if aud is not None:
        aud.to_csv(pastas["interim"] / "auditoria_fluxos.csv", index=False, encoding="utf-8")

    ex = exemplos_auditaveis(d, com_ficha)
    print(f"\n== Exemplos auditáveis (fluxo curto: {ex.attrs.get('curto')} | longo: {ex.attrs.get('longo')}) ==")
    if len(ex):
        ex.to_csv(pastas["reports"] / "exemplos_auditaveis.csv", index=False, encoding="utf-8")
        print(ex.drop(columns=["timestamp_epoch"]).to_string(index=False))
    f_ordem = com_ficha.sort_values("mediana")
    print("\n  ficha conferida — mais curto:", f_ordem.iloc[0][["fluxo_id", "mediana", "mad"]].to_dict())
    print("  ficha conferida — mais longo:", f_ordem.iloc[-1][["fluxo_id", "mediana", "mad"]].to_dict())

    resumo = {"inspecao": ins, "fluxos_com_ficha": int(len(com_ficha)), "fluxos_excluidos": excluidos["fluxo_id"].tolist(),
              "contagem_classes_B": {k: int(v) for k, v in contagem.items()},
              "recorte": {"proporcao": list(props), "ajustada": bool(ajustado), "n": {k: int(v) for k, v in n_split.items()}}}
    (pastas["reports"] / "resumo_tarefa2.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nConcluído. Árvore, profundidade, acurácia e F1 ficam para a Tarefa 3.")


if __name__ == "__main__":
    main()

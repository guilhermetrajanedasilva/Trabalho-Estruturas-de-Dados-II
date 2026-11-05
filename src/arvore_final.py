import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree

import arvore_comum as ac

CONJUNTOS = {"oficiais": ac.COLUNAS_OFICIAIS, "oficiais+delta_z_robusto": ac.COLUNAS_OFICIAIS + [ac.COLUNA_NOVA]}


def main():
    ap = argparse.ArgumentParser(description="Tarefa 5 — árvore final e teste único")
    ap.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--drive", nargs="?", const="", default=None, metavar="PASTA",
                    help="Google Colab: salva tudo em Meu Drive/PASTA (padrão: netvision)")
    ap.add_argument("--repetir", action="store_true", help="mede o teste de novo (fica registrado; não use para escolher a árvore)")
    args = ap.parse_args()
    from drive_colab import resolver_base
    p = ac.pastas(resolver_base(args.base_dir, args.drive))
    cfg = json.loads((p["config"] / "config_arvore.json").read_text(encoding="utf-8"))
    final = cfg.get("final")
    if not final:
        raise SystemExit("Parâmetros finais ausentes. Rode antes: python ajuste_arvore.py")
    trava = p["reports"] / "t5_teste_unico.json"
    if trava.exists() and not args.repetir:
        raise SystemExit(f"O teste já foi medido ({trava}). Ele só é medido uma vez. Para repetir de propósito, use --repetir.")

    cols = CONJUNTOS[final["colunas"]]
    assert not set(cols) & set(ac.PROIBIDAS), "coluna proibida na árvore"
    d = ac.carregar_dataset(p)
    tr, va, te = ac.blocos(d, usar_teste=True)
    print(f"parâmetros finais: {final}\ntreino={len(tr)} validação={len(va)} teste={len(te)}")
    assert te["timestamp"].min() > tr["timestamp"].max() - pd.Timedelta(days=1), "corte temporal inconsistente"

    # ---------------- 1. árvore e teste único ----------------
    arv = ac.nova_arvore(final).fit(tr[cols], tr["classe"])  # fit só no treino
    joblib.dump(arv, p["models"] / "arvore_final.joblib")
    res = ac.resumo_arvore(arv, cols)
    regras = ac.regras_folhas(arv, cols).sort_values("amostras", ascending=False)
    (p["reports"] / "t5_regras.txt").write_text("\n".join(regras["regra"]) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(26, 11))
    plot_tree(arv, feature_names=cols, class_names=list(arv.classes_), filled=True, rounded=True, impurity=False,
              proportion=False, fontsize=8, ax=ax)
    fig.savefig(p["reports"] / "arvore_final.png", dpi=110, bbox_inches="tight")
    plt.close(fig)

    prev = arv.predict(te[cols])
    m = ac.avaliar(te["classe"], prev)
    print("\n== Teste temporal (medido uma vez) ==")
    print(ac.matriz_md(m))
    print({k: m[k] for k in ("precisao", "recall", "f1", "f1_macro", "acuracia", "acuracia_balanceada")})
    t = te.assign(previsto=prev)
    cm = m["matriz"]
    print(f"troca RISCO->FALHA: {cm[1][2]} | FALHA->RISCO: {cm[2][1]} | FALHA->OK: {cm[2][0]} | RISCO->OK: {cm[1][0]}")

    base = pd.read_csv(p["processed"] / "baseline_por_fluxo.csv", dtype={"fluxo_id": str}).dropna(subset=["mediana"])
    curto = base.sort_values("mediana").iloc[0]["fluxo_id"]
    cols_caso = ["fluxo_id", "timestamp", "rtt_ms"] + cols + ["classe", "previsto"]
    longos_ok = t[(t["fluxo_id"] != curto) & (t["classe"] == "OK") & (t["previsto"] == "OK") & (t["z_robusto"].abs() < 1)]
    # caso de acerto: o fluxo mais longo (maior mediana de A), primeira medição OK com z baixo
    ordem = base.sort_values("mediana", ascending=False)["fluxo_id"].tolist()
    acerto = next((longos_ok[longos_ok["fluxo_id"] == f].iloc[[0]] for f in ordem if len(longos_ok[longos_ok["fluxo_id"] == f])), longos_ok.head(1))
    erros = t[t["classe"] != t["previsto"]][cols_caso]
    print("\nCaso de acerto (caminho longo estável):\n", acerto[cols_caso].to_string(index=False))
    print(f"\nErros no teste: {len(erros)}")
    print(erros.head(10).to_string(index=False) if len(erros) else "(nenhum erro no teste)")
    erros.to_csv(p["reports"] / "t5_erros_teste.csv", index=False)

    # ---------------- 2. fluxos que a árvore não viu (leave-one-flow-out) ----------------
    print("\n== Fluxos não vistos (treina sem o fluxo e avalia nele; ficha só do Período A dele) ==")
    ficha = base.set_index("fluxo_id")
    linhas, erros_nv = [], []
    for fid in sorted(d["fluxo_id"].unique()):
        treino_sem = tr[tr["fluxo_id"] != fid]
        alvo = d[d["fluxo_id"] == fid]  # todo o Período B do fluxo novo
        assert fid not in set(treino_sem["fluxo_id"]), "fluxo novo apareceu no treino"
        if ficha.loc[fid, "n_rtt_validos_A"] < 1500:
            linhas.append({"fluxo_id": fid, "avaliado": False}); continue
        a2 = ac.nova_arvore(final).fit(treino_sem[cols], treino_sem["classe"])
        pr = a2.predict(alvo[cols])
        mm = ac.avaliar(alvo["classe"], pr)
        real_ok = alvo["classe"] == "OK"
        presentes = [c for c in ac.CLASSES if mm["suporte"][c] > 0]  # F1 macro só sobre as classes que existem no fluxo
        f1_pres = round(sum(mm["f1"][c] for c in presentes) / len(presentes), 4)
        erros_nv.append(alvo.assign(previsto=pr)[lambda x: x["classe"] != x["previsto"]][["fluxo_id", "timestamp", "rtt_ms"] + cols + ["classe", "previsto"]])
        linhas.append({
            "fluxo_id": fid, "mediana_A_ms": round(float(ficha.loc[fid, "mediana"]), 1), "n_B": len(alvo),
            "n_OK": int(real_ok.sum()), "n_RISCO": int((alvo["classe"] == "RISCO").sum()), "n_FALHA": int((alvo["classe"] == "FALHA").sum()),
            "acuracia": mm["acuracia"], "f1_macro_classes_presentes": f1_pres,
            "recall_OK": mm["recall"]["OK"] if mm["suporte"]["OK"] else None,
            "recall_RISCO": mm["recall"]["RISCO"] if mm["suporte"]["RISCO"] else None,
            "recall_FALHA": mm["recall"]["FALHA"] if mm["suporte"]["FALHA"] else None,
            "erros": int((alvo["classe"] != pr).sum()), "avaliado": True})
    nv = pd.DataFrame(linhas)
    nv["fluxo_curto"] = nv["fluxo_id"] == curto
    nv.to_csv(p["reports"] / "t5_fluxos_nao_vistos.csv", index=False)
    pd.concat(erros_nv).to_csv(p["reports"] / "t5_fluxos_nao_vistos_erros.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", None)
    print(nv.to_string(index=False))

    # ---------------- 3. registro do teste único ----------------
    resumo = {
        "medido_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "repetido": bool(args.repetir),
        "parametros": final, "colunas": cols, "resumo_arvore": res, "n_treino": len(tr), "n_validacao": len(va), "n_teste": len(te),
        "teste": m, "troca_risco_falha": {"risco_para_falha": cm[1][2], "falha_para_risco": cm[2][1],
                                         "falha_para_ok": cm[2][0], "risco_para_ok": cm[1][0]},
        "fluxo_curto": curto, "erros_teste": int(len(erros)), "fluxos_nao_vistos": nv.to_dict(orient="records")}
    ac.gravar_json(trava, resumo)
    print(f"\nTeste registrado em {trava}. Figura da árvore: reports/arvore_final.png")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Tarefa 4 — Ajuste da árvore a partir do erro — Projeto NetVision (Grupo 15)

Mantém o rótulo, o baseline e o corte da Tarefa 2 e NÃO troca o algoritmo (continua CART).
Ajustes permitidos: profundidade, mínimo de amostras na folha, critério (Gini/entropia), poda (ccp_alpha),
peso de classes e uma coluna relativa nova (tendência do z_robusto: `delta_z_robusto`).

  1. Lê o resultado e os erros da Tarefa 3 (reports/t3_*.json|csv).
  2. Busca a configuração com melhor F1 macro NA VALIDAÇÃO (o teste não é carregado).
  3. Compara Tarefa 3 -> Tarefa 4 (F1 macro e recalls), lista as mudanças e grava os parâmetros em
     config/config_arvore.json ("final"), que a Tarefa 5 vai usar.

Uso: python ajuste_arvore.py [--base-dir CAMINHO]
"""
import argparse
import itertools
import json
from pathlib import Path

import joblib
import pandas as pd

import arvore_comum as ac

CONJUNTOS = {"oficiais": ac.COLUNAS_OFICIAIS,
             "oficiais+delta_z_robusto": ac.COLUNAS_OFICIAIS + [ac.COLUNA_NOVA]}


def main():
    ap = argparse.ArgumentParser(description="Tarefa 4 — ajuste da árvore")
    ap.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--drive", nargs="?", const="", default=None, metavar="PASTA",
                    help="Google Colab: salva tudo em Meu Drive/PASTA (padrão: netvision)")
    from drive_colab import resolver_base
    args = ap.parse_args()
    p = ac.pastas(resolver_base(args.base_dir, args.drive))
    cfg_caminho = p["config"] / "config_arvore.json"
    cfg = json.loads(cfg_caminho.read_text(encoding="utf-8"))
    g = cfg["tarefa4"]

    t3_caminho = p["reports"] / "t3_resumo.json"
    if not t3_caminho.exists():
        raise SystemExit("Rode antes: python arvore_inicial.py")
    t3 = json.loads(t3_caminho.read_text(encoding="utf-8"))

    d = ac.carregar_dataset(p)
    tr, va, _ = ac.blocos(d)  # o teste NÃO é carregado nesta tarefa
    print(f"treino={len(tr)} | validação={len(va)}")
    print(f"Tarefa 3: {t3['parametros']} | F1 macro val={t3['validacao']['f1_macro']} | "
          f"erros: FALHA->OK {t3['validacao']['matriz'][2][0]}, outros {sum(map(sum, t3['validacao']['matriz'])) - sum(t3['validacao']['matriz'][i][i] for i in range(3)) - t3['validacao']['matriz'][2][0]}")

    # erros da Tarefa 3 que motivam o ajuste
    erros = pd.read_csv(p["reports"] / "t3_erros_validacao.csv")
    erros = erros[erros["tipo"] == "erro da validação"]
    print("\nErros da validação na Tarefa 3:")
    print(erros[["fluxo_id", "timestamp", "z_robusto", "perda_pct", "n5_timeout", "classe", "previsto"]].to_string(index=False))

    print("\n== Busca na validação ==")
    linhas = []
    for crit, prof, folha, ccp, peso, conj in itertools.product(
            g["grade_criterion"], g["grade_max_depth"], g["grade_min_samples_leaf"],
            g["grade_ccp_alpha"], g["grade_class_weight"], g["grade_colunas"]):
        params = {"criterion": crit, "max_depth": prof, "min_samples_leaf": folha, "ccp_alpha": ccp,
                  "class_weight": peso, "random_state": cfg["random_state"]}
        cols = CONJUNTOS[conj]
        arv = ac.nova_arvore(params).fit(tr[cols], tr["classe"])
        m = ac.avaliar(va["classe"], arv.predict(va[cols]))
        linhas.append({**params, "colunas": conj, "f1_macro_val": m["f1_macro"], "recall_falha_val": m["recall"]["FALHA"],
                       "recall_risco_val": m["recall"]["RISCO"], "recall_ok_val": m["recall"]["OK"],
                       "folhas": int(arv.get_n_leaves()), "profundidade": int(arv.get_depth())})
    busca = pd.DataFrame(linhas)
    busca.to_csv(p["reports"] / "t4_busca_validacao.csv", index=False)
    # melhor F1 macro; empate -> maior recall de FALHA -> menos folhas -> menor profundidade
    melhor = busca.sort_values(["f1_macro_val", "recall_falha_val", "folhas", "profundidade"],
                               ascending=[False, False, True, True]).iloc[0]
    print(busca.sort_values(["f1_macro_val", "recall_falha_val", "folhas"], ascending=[False, False, True])
          .head(8)[["criterion", "max_depth", "min_samples_leaf", "ccp_alpha", "class_weight", "colunas",
                    "f1_macro_val", "recall_falha_val", "folhas"]].to_string(index=False))
    # efeito isolado da coluna nova: melhor com e sem ela
    for conj in g["grade_colunas"]:
        b = busca[busca["colunas"] == conj].sort_values(["f1_macro_val", "recall_falha_val", "folhas"], ascending=[False, False, True]).iloc[0]
        print(f"melhor com colunas '{conj}': F1 macro={b['f1_macro_val']} recall FALHA={b['recall_falha_val']} folhas={int(b['folhas'])}")

    final = {"criterion": melhor["criterion"], "max_depth": int(melhor["max_depth"]),
             "min_samples_leaf": int(melhor["min_samples_leaf"]), "ccp_alpha": float(melhor["ccp_alpha"]),
             "class_weight": None if pd.isna(melhor["class_weight"]) else melhor["class_weight"],
             "random_state": cfg["random_state"], "colunas": melhor["colunas"]}
    cols = CONJUNTOS[final["colunas"]]
    arv = ac.nova_arvore(final).fit(tr[cols], tr["classe"])
    joblib.dump(arv, p["models"] / "arvore_tarefa4.joblib")
    prev = arv.predict(va[cols])
    m4 = ac.avaliar(va["classe"], prev)
    res = ac.resumo_arvore(arv, cols)
    regras = ac.regras_folhas(arv, cols).sort_values("amostras", ascending=False)
    (p["reports"] / "t4_regras.txt").write_text("\n".join(regras["regra"]) + "\n", encoding="utf-8")

    print("\n== Árvore ajustada ==")
    print(final, res, sep="\n")
    print(regras[["regra", "amostras", "pureza"]].head(8).to_string(index=False))
    print("\n== Validação: Tarefa 3 -> Tarefa 4 ==")
    m3 = t3["validacao"]
    tabela = pd.DataFrame({"modelo": ["Tarefa 3", "Tarefa 4"],
                           "f1_macro": [m3["f1_macro"], m4["f1_macro"]],
                           "recall_FALHA": [m3["recall"]["FALHA"], m4["recall"]["FALHA"]],
                           "recall_RISCO": [m3["recall"]["RISCO"], m4["recall"]["RISCO"]],
                           "recall_OK": [m3["recall"]["OK"], m4["recall"]["OK"]],
                           "folhas": [t3["resumo_arvore"]["folhas"], res["folhas"]],
                           "profundidade": [t3["resumo_arvore"]["profundidade_obtida"], res["profundidade_obtida"]]})
    print(tabela.to_string(index=False))
    print(ac.matriz_md(m4))
    v = va.assign(previsto=prev)
    erros4 = v[v["classe"] != v["previsto"]][["fluxo_id", "timestamp", "rtt_ms"] + cols + ["classe", "previsto"]]
    print("\nerros restantes na validação:", len(erros4))
    print(erros4.to_string(index=False) if len(erros4) else "")

    # mudanças em relação à Tarefa 3 (para o diário)
    p3 = t3["parametros"]
    mud = []
    for k in ("criterion", "max_depth", "min_samples_leaf", "ccp_alpha", "class_weight"):
        a, b = p3.get(k), final.get(k)
        if (a or 0) != (b or 0) if k in ("ccp_alpha",) else a != b:
            mud.append(f"{k}: {a} -> {b}")
    if final["colunas"] != "oficiais":
        mud.append("coluna nova: delta_z_robusto")
    print("\nmudanças:", mud or "nenhuma")

    cfg["final"] = final
    cfg_caminho.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nConcluído. O teste não foi aberto; parâmetros gravados em config/config_arvore.json ('final').")


if __name__ == "__main__":
    main()

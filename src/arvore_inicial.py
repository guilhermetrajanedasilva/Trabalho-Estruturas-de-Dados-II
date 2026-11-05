import argparse
import itertools
from pathlib import Path

import joblib
import pandas as pd

import arvore_comum as ac


def escolher_parametros(tr, va, cfg):
    t3, linhas = cfg["tarefa3"], []
    for prof, folha in itertools.product(t3["grade_max_depth"], t3["grade_min_samples_leaf"]):
        arv = ac.nova_arvore({"criterion": t3["criterion"], "max_depth": prof, "min_samples_leaf": folha,
                              "class_weight": t3["class_weight"], "random_state": cfg["random_state"]})
        arv.fit(tr[ac.COLUNAS_OFICIAIS], tr["classe"])
        m = ac.avaliar(va["classe"], arv.predict(va[ac.COLUNAS_OFICIAIS]))
        linhas.append({"max_depth": prof, "min_samples_leaf": folha, "f1_macro_val": m["f1_macro"],
                       "recall_falha_val": m["recall"]["FALHA"], "recall_risco_val": m["recall"]["RISCO"],
                       "folhas": int(arv.get_n_leaves())})
    grade = pd.DataFrame(linhas)
    # melhor F1 macro na validação; empate -> árvore mais simples (menor profundidade, folha maior)
    melhor = grade.sort_values(["f1_macro_val", "max_depth", "min_samples_leaf"], ascending=[False, True, False]).iloc[0]
    return grade, int(melhor["max_depth"]), int(melhor["min_samples_leaf"])


def erros_concretos(va, prev, p, n=3):
    """Falsos alarmes em caminho longo estável (OK real) e FALHA real em caminho curto."""
    base = pd.read_csv(p["processed"] / "baseline_por_fluxo.csv", dtype={"fluxo_id": str}).dropna(subset=["mediana"])
    curto = base.sort_values("mediana").iloc[0]["fluxo_id"]
    v = va.assign(previsto=prev)
    cols = ["fluxo_id", "timestamp", "rtt_ms"] + ac.COLUNAS_OFICIAIS + ["classe", "previsto"]
    longo_alarme = v[(v["fluxo_id"] != curto) & (v["classe"] == "OK") & (v["previsto"] != "OK")]
    curto_falha = v[(v["fluxo_id"] == curto) & (v["classe"] == "FALHA") & (v["previsto"] == "OK")]
    return curto, longo_alarme[cols].head(n), curto_falha[cols].head(n), int(len(longo_alarme)), int(len(curto_falha))


def main():
    ap = argparse.ArgumentParser(description="Tarefa 3 — primeira árvore de decisão")
    ap.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--drive", nargs="?", const="", default=None, metavar="PASTA",
                    help="Google Colab: salva tudo em Meu Drive/PASTA (padrão: netvision)")
    from drive_colab import resolver_base
    args = ap.parse_args()
    p = ac.pastas(resolver_base(args.base_dir, args.drive))
    cfg = __import__("json").loads((p["config"] / "config_arvore.json").read_text(encoding="utf-8"))

    d = ac.carregar_dataset(p)
    tr, va, _ = ac.blocos(d)  # o teste NÃO é carregado nesta tarefa
    print(f"treino={len(tr)} | validação={len(va)} | colunas oficiais: {ac.COLUNAS_OFICIAIS}")
    assert not set(ac.COLUNAS_OFICIAIS) & set(ac.PROIBIDAS)

    print("\n== 1. Escolha de max_depth e min_samples_leaf (só validação) ==")
    grade, prof, folha = escolher_parametros(tr, va, cfg)
    grade.to_csv(p["reports"] / "t3_grade_validacao.csv", index=False)
    print(grade.sort_values("f1_macro_val", ascending=False).head(8).to_string(index=False))
    print(f"-> escolhido: max_depth={prof}, min_samples_leaf={folha}")

    print("\n== 2. Árvore oficial ==")
    params = {"criterion": cfg["tarefa3"]["criterion"], "max_depth": prof, "min_samples_leaf": folha,
              "class_weight": cfg["tarefa3"]["class_weight"], "random_state": cfg["random_state"]}
    arv = ac.nova_arvore(params).fit(tr[ac.COLUNAS_OFICIAIS], tr["classe"])
    joblib.dump(arv, p["models"] / "arvore_tarefa3.joblib")
    res = ac.resumo_arvore(arv, ac.COLUNAS_OFICIAIS)
    print(res)
    regras = ac.regras_folhas(arv, ac.COLUNAS_OFICIAIS).sort_values("amostras", ascending=False)
    (p["reports"] / "t3_regras.txt").write_text("\n".join(regras["regra"]) + "\n", encoding="utf-8")
    print(regras[["regra", "amostras", "pureza"]].head(8).to_string(index=False))

    print("\n== 3. Validação ==")
    prev = arv.predict(va[ac.COLUNAS_OFICIAIS])
    m = ac.avaliar(va["classe"], prev)
    print(ac.matriz_md(m))
    print({k: m[k] for k in ("precisao", "recall", "f1", "f1_macro", "acuracia", "acuracia_balanceada")})

    curto, longo_alarme, curto_falha, n_la, n_cf = erros_concretos(va, prev, p)
    cols_erro = ["fluxo_id", "timestamp", "rtt_ms"] + ac.COLUNAS_OFICIAIS + ["classe", "previsto"]
    todos = va.assign(previsto=prev)
    todos = todos[todos["classe"] != todos["previsto"]][cols_erro]
    erros = pd.concat([longo_alarme.assign(tipo="OK real em caminho longo, alarme falso"),
                       curto_falha.assign(tipo="FALHA real em caminho curto, prevista OK"),
                       todos.assign(tipo="erro da validação")]).drop_duplicates(subset=["fluxo_id", "timestamp"])
    erros.to_csv(p["reports"] / "t3_erros_validacao.csv", index=False)
    print(f"\nfluxo curto: {curto} | alarmes falsos em caminho longo: {n_la} | FALHA do fluxo curto prevista OK: {n_cf}")
    print(erros.to_string(index=False) if len(erros) else "(nenhum caso)")
    # onde a árvore mais erra
    v = va.assign(previsto=prev)
    print("\nerros por fluxo:\n", v.assign(erro=v["classe"] != v["previsto"]).groupby("fluxo_id")["erro"].agg(["sum", "size"]).to_string())

    print("\n== 4. Árvore de contraste (NÃO é o modelo) ==")
    rotas = ac.auditoria_rotas(p)[["fluxo_id", "probe_pais", "anchor_pais"]]
    def com_rota(df):
        x = df.merge(rotas, on="fluxo_id", how="left")
        dummies = pd.get_dummies(x[["probe_pais", "anchor_pais"]], prefix=["origem", "destino"]).astype(int)
        return pd.concat([x.reset_index(drop=True), dummies], axis=1), list(dummies.columns)
    tr_c, rota_cols = com_rota(tr)
    va_c, _ = com_rota(va)
    contraste = {}
    for nome, colunas in (("oficiais + rtt_ms + rota", ac.COLUNAS_OFICIAIS + ["rtt_ms"] + rota_cols),
                          ("somente rtt_ms + rota", ["rtt_ms"] + rota_cols)):
        c = ac.nova_arvore(params).fit(tr_c[colunas], tr_c["classe"])
        mc = ac.avaliar(va_c["classe"], c.predict(va_c[colunas]))
        r = ac.resumo_arvore(c, colunas)
        contraste[nome] = {"raiz": r["raiz"], "divisoes_nivel_1": r["divisoes_nivel_1"], "importancias": r["importancias"],
                           "f1_macro_val": mc["f1_macro"], "recall_falha_val": mc["recall"]["FALHA"],
                           "recall_risco_val": mc["recall"]["RISCO"], "matriz": mc["matriz"]}
        print(nome, "->", contraste[nome]["raiz"], "| F1 macro val:", mc["f1_macro"], "| recall FALHA:", mc["recall"]["FALHA"],
              "| importâncias:", r["importancias"])
    # o que a árvore só-distância faz: previsão por fluxo
    colunas = ["rtt_ms"] + rota_cols
    c = ac.nova_arvore(params).fit(tr_c[colunas], tr_c["classe"])
    vc = va_c.assign(previsto=c.predict(va_c[colunas]))
    tabela = pd.crosstab(vc["fluxo_id"], vc["previsto"]).reindex(columns=ac.CLASSES, fill_value=0)
    print("\nárvore só-distância, previsão por fluxo (validação):\n", tabela.to_string())
    contraste["somente rtt_ms + rota"]["previsao_por_fluxo"] = tabela.to_dict()
    ac.gravar_json(p["reports"] / "t3_contraste.json", contraste)

    ac.gravar_json(p["reports"] / "t3_resumo.json", {
        "parametros": params, "resumo_arvore": res, "validacao": m, "colunas": ac.COLUNAS_OFICIAIS,
        "fluxo_curto": curto, "alarmes_falsos_caminho_longo": n_la, "falha_curto_prevista_ok": n_cf,
        "n_treino": len(tr), "n_validacao": len(va), "teste_usado": False})
    print("\nConcluído. O teste não foi aberto.")


if __name__ == "__main__":
    main()

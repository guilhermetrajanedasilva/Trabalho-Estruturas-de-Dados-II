import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

FEATURES = ["z_robusto", "aumento_pct", "jitter_relativo", "perda_pct",
            "timeout_atual", "n5_timeout", "n5_aumento80", "n5_risco"]
NOME_MODELO, VERSAO_MODELO = "netvision_detector_arvore", "1.0.0"
# limite (decisão do grupo, ver RFC seção 8.5) para sinalizar troca de patamar: fração do Período B com
# z_robusto >= 3,5 sem perda (desvio extremo "estável", típico de rota nova e não de pane)
LIMITE_PATAMAR_NOVO = 0.25


def ler(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def limpo(x):
    """Converte para tipos JSON (NaN -> None)."""
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if np.isnan(x) else round(float(x), 6)
    return x


def main():
    ap = argparse.ArgumentParser(description="Gera modelo.joblib, metadados.json e baseline.csv")
    ap.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--saida", type=Path, default=None, help="pasta de saída (padrão: <base>/entrega)")
    args = ap.parse_args()
    base = args.base_dir.resolve()
    out = (args.saida or base / "entrega").resolve()
    out.mkdir(parents=True, exist_ok=True)

    cfg_col = ler(base / "config" / "config_coleta.json")
    cfg_rot = ler(base / "config" / "config_rotulagem.json")
    cfg_arv = ler(base / "config" / "config_arvore.json")["final"]
    lim, n_jan = cfg_rot["limiares"], cfg_rot["janela_ultimas_n"]

    # ------------------------------------------------------------------ modelo.joblib
    cand = [base / "models" / "arvore_final.joblib", base / "Tarefas" / "modelos_arvores" / "arvore_final.joblib"]
    origem = next((c for c in cand if c.exists()), None)
    if origem is None:
        sys.exit("arvore_final.joblib não encontrado. Rode antes: python src/arvore_final.py --base-dir .")
    arv = joblib.load(origem)
    assert list(arv.feature_names_in_) == FEATURES, "ordem das features difere do treino"
    params_cfg = {k: v for k, v in cfg_arv.items() if k != "colunas"}
    params_mod = arv.get_params()
    assert all(params_mod[k] == v for k, v in params_cfg.items()), "árvore salva difere de config_arvore.json"

    pacote = {
        "modelo": arv,
        "features": list(arv.feature_names_in_),  # mesmos nomes e mesma ordem do treino
        "familia": "Árvore de decisão (CART) — sklearn.tree.DecisionTreeClassifier",
        "params": params_mod,
    }
    joblib.dump(pacote, out / "modelo.joblib")

    # confere: recarrega e reproduz o teste registrado na Tarefa 5 (só leitura, não reescolhe nada)
    pac = joblib.load(out / "modelo.joblib")
    d = pd.read_csv(base / "data" / "processed" / "dataset_rotulado_B.csv", dtype={"fluxo_id": str})
    te = d[d["split"] == "teste"]
    prev = pac["modelo"].predict(te[pac["features"]])
    erros = int((prev != te["classe"]).sum())
    reg = ler(base / "reports" / "t5_teste_unico.json")
    assert erros == reg["erros_teste"], f"modelo recarregado não reproduz o teste ({erros} != {reg['erros_teste']})"

    # ------------------------------------------------------------------ baseline.csv
    ficha = pd.read_csv(base / "data" / "processed" / "baseline_por_fluxo.csv", dtype={"fluxo_id": str})
    pares = pd.DataFrame(cfg_col["pares"])
    pares["fluxo_id"] = pares["probe_id"].astype(str) + "|" + pares["dst_addr"]
    bruto = pd.read_csv(base / "data" / "raw" / "ping_bruto.csv", dtype={"fluxo_id": str},
                        usecols=["fluxo_id", "timestamp", "periodo"])
    a_real = bruto[bruto["periodo"] == "A"].groupby("fluxo_id")["timestamp"].agg(["min", "max"])

    # sinal de troca de patamar no Período B (só auditoria/recomendação; não muda a ficha congelada)
    d["_patamar"] = (d["z_robusto"] >= lim["falha_z_robusto"]) & (d["perda_pct"] == 0)
    pB = d.groupby("fluxo_id").agg(n_B=("classe", "size"),
                                   pct_ok_B=("classe", lambda s: (s == "OK").mean()),
                                   pct_patamar_novo_B=("_patamar", "mean"),
                                   mediana_rtt_B_ms=("rtt_ms", "median"))

    b = pares.merge(ficha, on="fluxo_id", how="left").merge(pB, on="fluxo_id", how="left")
    b = b.join(a_real, on="fluxo_id")
    piso = cfg_rot["piso_rtt_validos_periodo_a"]
    b["status"] = b["status"].fillna("sem_dados")
    b["valido"] = (b["status"] == "ok") & (b["n_rtt_validos_A"].fillna(0) >= piso) & (b["mad"].notna())

    def recomendar(r):
        if not r["valido"]:
            return "nao_usar", (f"sem baseline: {int(r['n_rtt_validos_A'] or 0)} RTT válidos no Período A "
                                f"(piso {piso}); fluxo não recebe classe")
        if r["pct_patamar_novo_B"] > LIMITE_PATAMAR_NOVO:
            return "usar_com_cautela_recalibrar", (
                f"{r['pct_patamar_novo_B']:.0%} do Período B com z_robusto >= {lim['falha_z_robusto']} sem perda: "
                "indício de troca de rota (patamar novo estável). FALHA desse fluxo pode ser mudança de caminho; "
                "abrir novo período de baseline (RECALIBRAR, RFC 8.5)")
        return "usar", "baseline válido e estável no Período B"

    b[["recomendacao_uso", "motivo_recomendacao"]] = b.apply(lambda r: pd.Series(recomendar(r)), axis=1)
    b["n_rtt_validos_A"] = b["n_rtt_validos_A"].fillna(0).astype(int)
    b["n_medicoes_A"] = b["n_medicoes_A"].fillna(0).astype(int)
    saida_b = pd.DataFrame({
        # identificação do fluxo
        "fluxo_id": b["fluxo_id"], "par_id": b["par_id"], "measurement_id": b["measurement_id"],
        "probe_id": b["probe_id"], "anchor_id": b["anchor_id"], "dst_addr": b["dst_addr"],
        "origem": b["probe_cidade"] + " (" + b["probe_pais"] + ")",
        "destino": b["anchor_cidade"] + " (" + b["anchor_pais"] + ")",
        # valores de referência usados nas features
        "mediana_rtt_ms": b["mediana"], "mad_rtt_ms": b["mad"], "iqr_rtt_ms": b["iqr"],
        "jitter_tipico_ms": b["jitter_tipico"], "perda_tipica_pct": b["perda_tipica"],
        "prop_resposta": b["prop_resposta"],
        # período de cálculo
        "periodo_calculo": "A",
        "inicio_calculo_utc": cfg_col["periodo_a"]["inicio_utc"], "fim_calculo_utc": cfg_col["periodo_a"]["fim_utc"],
        "primeira_medicao_A_utc": b["min"], "ultima_medicao_A_utc": b["max"],
        "n_medicoes_A": b["n_medicoes_A"], "n_rtt_validos_A": b["n_rtt_validos_A"],
        # validade e recomendação
        "piso_rtt_validos": piso, "status_baseline": b["status"], "valido": b["valido"],
        "pct_ok_periodo_B": b["pct_ok_B"].round(4), "pct_patamar_novo_periodo_B": b["pct_patamar_novo_B"].round(4),
        "recomendacao_uso": b["recomendacao_uso"], "motivo_recomendacao": b["motivo_recomendacao"],
    }).sort_values("par_id")
    saida_b.to_csv(out / "baseline.csv", index=False, encoding="utf-8")

    # ------------------------------------------------------------------ exemplo real (do teste)
    bruto_full = pd.read_csv(base / "data" / "raw" / "ping_bruto.csv", dtype={"fluxo_id": str})
    te = te.assign(previsto=prev)
    fluxo_curto = ficha.sort_values("mediana").iloc[0]["fluxo_id"]
    fluxo_longo = ficha.sort_values("mediana").iloc[-1]["fluxo_id"]

    def exemplo(linha, titulo):
        hist = d[(d["fluxo_id"] == linha["fluxo_id"]) & (d["timestamp"] <= linha["timestamp"])].tail(n_jan)
        cru = bruto_full[(bruto_full["fluxo_id"] == linha["fluxo_id"]) & (bruto_full["timestamp"] == linha["timestamp"])].iloc[0]
        f = ficha.set_index("fluxo_id").loc[linha["fluxo_id"]]
        x = pd.DataFrame([linha[pac["features"]].astype(float)])[pac["features"]]
        proba = pac["modelo"].predict_proba(x)[0]
        return {
            "descricao": titulo,
            "fluxo_id": linha["fluxo_id"], "timestamp_utc": linha["timestamp"],
            "medicao_bruta": {k: limpo(cru[k]) for k in ("rtt_avg_ms", "rtt_min_ms", "rtt_max_ms", "enviados",
                                                         "recebidos", "perda_pct", "jitter_ms")},
            "baseline_usado": {k: limpo(f[k]) for k in ("mediana", "mad", "iqr", "jitter_tipico")},
            "historico_ultimas_5": [{"timestamp_utc": h["timestamp"], "timeout_atual": int(h["timeout_atual"]),
                                     "aumento_pct": limpo(h["aumento_pct"]),
                                     "criterio_risco_atual": int(h["criterio_risco_atual"])} for _, h in hist.iterrows()],
            "entrada_modelo": {c: limpo(linha[c]) for c in pac["features"]},
            "saida_modelo": {"classe_prevista": str(pac["modelo"].predict(x)[0]),
                             "probabilidades": {c: round(float(p), 4) for c, p in zip(pac["modelo"].classes_, proba)}},
            "classe_real_rotulo": linha["classe"],
        }

    ok_longo = te[(te["fluxo_id"] == fluxo_longo) & (te["classe"] == "OK") & (te["z_robusto"].abs() < 1)].iloc[0]
    risco = te[(te["classe"] == "RISCO") & (te["previsto"] == "RISCO") & (te["fluxo_id"] == fluxo_curto)]
    risco = (risco if len(risco) else te[(te["classe"] == "RISCO") & (te["previsto"] == "RISCO")]).iloc[0]
    falha = te[(te["classe"] == "FALHA") & (te["previsto"] == "FALHA") & (te["fluxo_id"] == fluxo_curto)]
    falha = (falha if len(falha) else te[(te["classe"] == "FALHA") & (te["previsto"] == "FALHA")]).iloc[0]
    exemplos = [exemplo(ok_longo, "Caminho longo estável: RTT alto, mas no normal do fluxo -> OK"),
                exemplo(risco, "RISCO: afastamento moderado e persistente do normal do fluxo"),
                exemplo(falha, "FALHA: desvio extremo, perda ou timeout persistente")]

    # ------------------------------------------------------------------ metadados.json
    def versao(mod):
        try:
            return __import__(mod).__version__
        except Exception:
            return None

    tipos = {"z_robusto": "float64", "aumento_pct": "float64", "jitter_relativo": "float64", "perda_pct": "float64",
             "timeout_atual": "int (0/1)", "n5_timeout": "int (0..5)", "n5_aumento80": "int (0..5)", "n5_risco": "int (0..5)"}
    meta = {
        "modelo": {
            "nome": NOME_MODELO, "versao": VERSAO_MODELO, "projeto": "NetVision — Grupo 15 (Estrutura de Dados II)",
            "gerado_em_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "familia": pacote["familia"], "params": {k: limpo(v) if not isinstance(v, (str, type(None))) else v
                                                     for k, v in params_mod.items()},
            "profundidade": int(arv.get_depth()), "folhas": int(arv.get_n_leaves()),
            "arquivo": "modelo.joblib",
            "como_carregar": ("import joblib, pandas as pd; pac = joblib.load('modelo.joblib'); "
                              "pac['modelo'].predict(pd.DataFrame([x])[pac['features']])"),
            "depende_de_codigo_proprio": False,
            "tipo": "detector do estado atual da medição (classificação OK / RISCO / FALHA)",
        },
        "ambiente": {
            "python": platform.python_version(),
            "bibliotecas": {"scikit-learn": sklearn.__version__, "joblib": joblib.__version__,
                            "pandas": pd.__version__, "numpy": np.__version__, "matplotlib": versao("matplotlib")},
            "observacao": "Carregar com a mesma versão do scikit-learn; versões diferentes podem emitir "
                          "InconsistentVersionWarning ou falhar.",
        },
        "descricao": (
            "Árvore de decisão que classifica cada medição de ping (mesh IPv4 do RIPE Atlas, 3 pacotes a cada 240 s) "
            "em OK, RISCO ou FALHA em relação ao normal do próprio fluxo (probe -> anchor). RTT alto não é falha: "
            "as entradas são todas relativas ao baseline congelado do fluxo (Período A). País, IP, rota, timestamp "
            "e RTT absoluto não entram no modelo. Treinada só no bloco de treino do Período B (10.067 linhas)."),
        "entradas": {
            "ordem": pac["features"],
            "detalhe": [{"posicao": i, "nome": c, "tipo": tipos[c]} for i, c in enumerate(pac["features"])],
            "formato": "pandas.DataFrame com essas colunas, nesta ordem (feature_names_in_ do modelo)",
            "colunas_proibidas": ["fluxo_id", "timestamp", "rtt_ms", "jitter_ms", "país", "cidade", "dst_addr/IP",
                                  "par_id", "rota_id", "split", "classe", "regra_disparada", "criterio_risco_atual"],
        },
        "calculo_das_features": {
            "dados_da_medicao": {
                "rtt_ms": "rtt_avg_ms da rajada (média das respostas); vazio se nenhuma resposta (nunca 0)",
                "perda_pct": "(enviados - recebidos) / enviados * 100",
                "jitter_ms": "desvio-padrão amostral dos RTT da rajada; só existe com >= 2 respostas",
            },
            "baseline_do_fluxo": "linha do baseline.csv do mesmo fluxo_id (mediana_rtt_ms, mad_rtt_ms, iqr_rtt_ms, jitter_tipico_ms)",
            "formulas": {
                "z_robusto": f"(rtt_ms - mediana) / ({cfg_rot['mad_escala']} * MAD)",
                "aumento_pct": "(rtt_ms - mediana) / mediana * 100",
                "jitter_relativo": "jitter_ms / jitter_tipico",
                "perda_pct": "(enviados - recebidos) / enviados * 100",
                "timeout_atual": "1 se rtt_ms vazio ou perda_pct == 100; senão 0",
                "n5_timeout": f"soma de timeout_atual nas últimas {n_jan} medições do fluxo (inclui a atual)",
                "n5_aumento80": f"quantas das últimas {n_jan} medições têm aumento_pct > {lim['aumento_alto_pct']}",
                "n5_risco": f"soma de criterio_risco_atual nas últimas {n_jan} medições",
                "criterio_risco_atual (auxiliar, não é entrada)": (
                    f"1 se ({lim['risco_z_min']} <= z_robusto < {lim['falha_z_robusto']}) ou "
                    f"({lim['risco_aumento_min_pct']} <= aumento_pct <= {lim['risco_aumento_max_pct']}) ou "
                    f"(jitter_relativo >= {lim['risco_jitter_relativo']}); senão 0"),
            },
            "etapas": [
                "1. Ler a medição bruta (rtt_avg_ms, enviados, recebidos, RTTs individuais).",
                "2. Calcular rtt_ms, perda_pct, jitter_ms e timeout_atual da rajada.",
                "3. Buscar a ficha do fluxo em baseline.csv; só seguir se valido == True.",
                "4. Calcular z_robusto, aumento_pct e jitter_relativo com a ficha (sem atualizar a ficha).",
                "5. Calcular criterio_risco_atual da medição.",
                f"6. Somar timeout_atual, (aumento_pct > {lim['aumento_alto_pct']}) e criterio_risco_atual nas últimas "
                f"{n_jan} medições do mesmo fluxo, em ordem de tempo, incluindo a atual.",
                "7. Montar o vetor na ordem de 'entradas.ordem' e chamar modelo.predict / predict_proba.",
            ],
        },
        "valores_ausentes_e_divisoes_por_zero": {
            "rtt_ausente": "timeout: rtt_ms, z_robusto e aumento_pct ficam NaN (nunca 0); timeout_atual = 1",
            "jitter_ausente": "menos de 2 respostas: jitter_ms e jitter_relativo ficam NaN (critério de jitter não dispara)",
            "NaN_no_modelo": "o DecisionTreeClassifier (scikit-learn >= 1.3) aceita NaN nativamente; não imputar",
            "MAD_igual_a_zero": (f"se rtt_ms == mediana, z = 0; senão z = (rtt_ms - mediana) / "
                                 f"max(IQR / {cfg_rot['iqr_divisor']}, {cfg_rot['denominador_minimo_ms']} ms)"),
            "mediana_igual_a_zero": "aumento_pct = NaN",
            "jitter_tipico_igual_a_zero": f"jitter atual 0 -> jitter_relativo = 1; jitter atual > 0 -> {float(lim['risco_jitter_relativo'])}",
            "jitter_tipico_ausente": "jitter_relativo = NaN",
            "enviados_igual_a_zero": "perda_pct = NaN",
            "inicio_do_fluxo": f"as {n_jan - 1} primeiras medições usam janela menor (min_periods = 1)",
        },
        "saidas": {
            "ordem_das_classes": [str(c) for c in arv.classes_],
            "observacao_ordem": "predict_proba devolve as probabilidades nesta ordem (alfabética: modelo.classes_)",
            "significado": {
                "OK": "medição dentro do normal do fluxo; nenhuma ação",
                "RISCO": "afastamento relevante e persistente (latência, jitter) sem indisponibilidade; observar e priorizar",
                "FALHA": "desvio extremo, perda >= 10%, timeout persistente ou aumento > 80% repetido; investigar o enlace",
            },
            "predict": "string com a classe", "predict_proba": "vetor de 3 probabilidades (fração da folha)",
        },
        "horizonte_de_previsao": {
            "valor": "0 (estado atual)",
            "descricao": ("Detector: classifica a medição corrente (janela de 240 s) usando ela e as 4 anteriores "
                          "(~20 min). O preditor de status_futuro em 12 min previsto no RFC não foi treinado."),
            "intervalo_entre_medicoes_s": 240,
        },
        "requisitos_do_historico": {
            "baseline": (f"ficha do fluxo calculada só no Período A ({cfg_col['periodo_a']['inicio_utc']} a "
                         f"{cfg_col['periodo_a']['fim_utc']}), com pelo menos {piso} RTT válidos; congelada"),
            "janela_recente": f"últimas {n_jan} medições do mesmo fluxo, ordenadas por tempo, incluindo a atual",
            "fluxo_sem_baseline": "não classificar",
        },
        "regras_de_uso_do_baseline": [
            "Usar só a linha do mesmo fluxo_id (probe_id|dst_addr); nunca a de outro fluxo.",
            "Só usar se valido == True; 'nao_usar' significa que o fluxo não recebe classe.",
            "A ficha é congelada: não recalcular com dados novos nem com o período avaliado.",
            "Timeouts ficam fora da mediana e do MAD, mas contam em prop_resposta e perda_tipica.",
            (f"Se recomendacao_uso == 'usar_com_cautela_recalibrar' (mais de {LIMITE_PATAMAR_NOVO:.0%} do Período B com "
             "z_robusto >= 3,5 sem perda), FALHA pode ser troca de rota: abrir novo baseline (24-48 h, mantendo o piso) "
             "antes de abrir chamado."),
        ],
        "desempenho_teste_temporal": {
            "n_teste": int(len(te)), "f1_macro": reg["teste"]["f1_macro"], "recall": reg["teste"]["recall"],
            "erros": reg["erros_teste"],
            "limitacao": "o rótulo usa as mesmas métricas das entradas; a árvore reaprende a política de rotulagem",
        },
        "exemplo_real": exemplos[0],
        "outros_exemplos_reais": exemplos[1:],
    }
    (out / "metadados.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(f"modelo de origem: {origem}")
    print(f"teste reproduzido com o modelo recarregado: {erros} erros (registrado: {reg['erros_teste']})")
    print(saida_b[["fluxo_id", "origem", "destino", "mediana_rtt_ms", "valido", "recomendacao_uso"]].to_string(index=False))
    print(f"arquivos em {out}: modelo.joblib, metadados.json, baseline.csv")


if __name__ == "__main__":
    main()

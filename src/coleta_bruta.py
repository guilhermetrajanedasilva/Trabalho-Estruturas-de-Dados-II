import argparse
import hashlib
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

HEADERS = {"User-Agent": "NetVision-Coleta/1.0 (trabalho academico)"}
TRANSITORIOS = {429, 500, 502, 503, 504}
CHAVE_DUPLICATA = ["measurement_id", "probe_id", "timestamp_epoch"]


# --------------------------------------------------------------------------- #
# Configuração e pastas
# --------------------------------------------------------------------------- #
def pastas_do_projeto(base: Path) -> dict:
    p = {
        "base": base,
        "config": base / "config",
        "raw": base / "data" / "raw",
        "raw_json": base / "data" / "raw" / "json",
        "reports": base / "reports",
    }
    for chave in ("raw", "raw_json", "reports"):
        p[chave].mkdir(parents=True, exist_ok=True)
    return p


def carregar_config(pastas: dict) -> tuple:
    caminho = pastas["config"] / "config_coleta.json"
    if not caminho.exists():
        sys.exit(f"Config não encontrado: {caminho}\n"
                 "Os parâmetros (períodos, probes, destinos) ficam em config/, não no código.")
    return caminho, json.loads(caminho.read_text(encoding="utf-8"))


def gravar_json_atomico(caminho: Path, conteudo, **kw):
    tmp = caminho.with_suffix(caminho.suffix + ".tmp")
    tmp.write_text(json.dumps(conteudo, ensure_ascii=False, **kw), encoding="utf-8")
    tmp.replace(caminho)  # o arquivo final só existe se a escrita terminou


def epoch(iso_utc: str) -> int:
    dt = datetime.strptime(iso_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def periodos(cfg: dict) -> dict:
    p = {"A": (epoch(cfg["periodo_a"]["inicio_utc"]), epoch(cfg["periodo_a"]["fim_utc"])),
         "B": (epoch(cfg["periodo_b"]["inicio_utc"]), epoch(cfg["periodo_b"]["fim_utc"]))}
    if not (p["A"][0] < p["A"][1] <= p["B"][0] < p["B"][1]):
        sys.exit("Períodos inválidos: A e B precisam ser contíguos e sem sobreposição (A termina quando B começa).")
    return p


# --------------------------------------------------------------------------- #
# HTTP (somente GET) com timeout e releitura em erro transitório
# --------------------------------------------------------------------------- #
def http_get_json(cfg: dict, url: str, params: dict = None):
    http = cfg["http"]
    ultimo_erro = None
    for tentativa in range(1, http["max_tentativas"] + 1):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=http["timeout_s"])
            if r.status_code == 200:
                return r.json()
            if r.status_code in TRANSITORIOS:
                ultimo_erro = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()  # erro não transitório (ex.: 404): não adianta reler
        except (requests.Timeout, requests.ConnectionError) as e:
            ultimo_erro = repr(e)
        time.sleep(http["espera_base_s"] * tentativa)
    raise RuntimeError(f"Falha após {http['max_tentativas']} tentativas em {url}: {ultimo_erro}")


# --------------------------------------------------------------------------- #
# 1. Validação dos pares (informativa)
# --------------------------------------------------------------------------- #
def validar_pares(cfg: dict, pastas: dict) -> pd.DataFrame:
    api = cfg["api_base"]
    linhas = []
    for par in cfg["pares"]:
        ip_api, status_probe, obs = None, None, ""
        try:
            ip_api = http_get_json(cfg, f"{api}/anchors/{par['anchor_id']}/").get("ip_v4")
        except Exception as e:  # validação não deve derrubar a coleta
            obs += f"anchor: {e}; "
        try:
            status_probe = (http_get_json(cfg, f"{api}/probes/{par['probe_id']}/").get("status") or {}).get("name")
        except Exception as e:
            obs += f"probe: {e}; "
        linhas.append({
            "par_id": par["par_id"], "probe_id": par["probe_id"], "anchor_id": par["anchor_id"],
            "dst_addr_config": par["dst_addr"], "ip_anchor_api": ip_api,
            "ip_confere": (ip_api == par["dst_addr"]) if ip_api else None,
            "status_probe_hoje": status_probe, "obs": obs.strip(),
        })
    df = pd.DataFrame(linhas)
    df.to_csv(pastas["raw"] / "validacao_pares.csv", index=False, encoding="utf-8")
    return df


# --------------------------------------------------------------------------- #
# 2. Descoberta do measurement_id de cada par
# --------------------------------------------------------------------------- #
def _id_da_url(url) -> int:
    return int(str(url).rstrip("/").split("/")[-1])


def _candidatas(cfg: dict, par: dict, fqdn: str) -> list:
    api = cfg["api_base"]
    ids = []
    # a) medições ligadas à anchor
    try:
        d = http_get_json(cfg, f"{api}/anchors/{par['anchor_id']}/measurements/", {"page_size": 100})
        for it in d.get("results", []):
            if it.get("type") == "ping" and it.get("is_active", True):
                ids.append(_id_da_url(it["measurement"]) if it.get("measurement") else it["id"])
    except Exception as e:
        print(f"  [aviso] anchors/{par['anchor_id']}/measurements: {e}")
    # b) busca em /measurements/ pelo nome da anchor
    if not ids and fqdn:
        try:
            d = http_get_json(cfg, f"{api}/measurements/",
                              {"target": fqdn, "type": "ping", "af": 4, "tags": "mesh", "page_size": 100})
            ids += [m["id"] for m in d.get("results", [])]
        except Exception as e:
            print(f"  [aviso] busca por alvo {fqdn}: {e}")
    return list(dict.fromkeys(ids))


def descobrir_medicao(cfg: dict, par: dict):
    """measurement_id de ping IPv4 contínuo (não one-off) cujo alvo é o IP da anchor do par."""
    api = cfg["api_base"]
    fqdn = http_get_json(cfg, f"{api}/anchors/{par['anchor_id']}/").get("fqdn")
    for mid in _candidatas(cfg, par, fqdn):
        m = http_get_json(cfg, f"{api}/measurements/{mid}/")
        if (m.get("type") == "ping" and m.get("af") == 4 and not m.get("is_oneoff")
                and m.get("target_ip") == par["dst_addr"]):
            return mid
    return None


def garantir_medicoes(cfg: dict, caminho_cfg: Path):
    mudou = False
    for par in cfg["pares"]:
        if not par.get("measurement_id"):
            par["measurement_id"] = descobrir_medicao(cfg, par)
            mudou = True
        print(f"par {par['par_id']:>2} | probe {par['probe_id']} -> anchor {par['anchor_id']} "
              f"({par['dst_addr']}) | measurement_id = {par['measurement_id']}")
    if mudou:
        gravar_json_atomico(caminho_cfg, cfg, indent=2)
        print("measurement_id gravados em", caminho_cfg)
    sem = [p["par_id"] for p in cfg["pares"] if not p.get("measurement_id")]
    if sem:
        print("ATENÇÃO — pares sem medição mesh encontrada (preencha measurement_id no config):", sem)


# --------------------------------------------------------------------------- #
# 3. Coleta idempotente do JSON bruto
# --------------------------------------------------------------------------- #
def caminho_json(pastas: dict, par: dict, periodo: str) -> Path:
    return pastas["raw_json"] / f"m{par['measurement_id']}_probe{par['probe_id']}_periodo{periodo}.json"


def coletar_periodo(cfg, pastas, par, periodo, janelas, forcar):
    destino = caminho_json(pastas, par, periodo)
    if destino.exists() and not forcar:
        return "existente", len(json.loads(destino.read_text(encoding="utf-8")))
    ini, fim = janelas[periodo]
    passo = cfg["http"]["tamanho_bloco_horas"] * 3600
    brutos, t = [], ini
    while t < fim:
        stop = min(t + passo, fim) - 1  # 'stop' é inclusivo na API: evita repetir o 1º segundo do bloco seguinte
        brutos.extend(http_get_json(
            cfg, f"{cfg['api_base']}/measurements/{par['measurement_id']}/results/",
            {"start": t, "stop": stop, "probe_ids": par["probe_id"], "format": "json"}))
        t += passo
    gravar_json_atomico(destino, brutos)  # JSON exatamente como veio da API
    return "coletado", len(brutos)


def coletar_tudo(cfg, pastas, janelas, forcar):
    resumo = []
    for par in cfg["pares"]:
        if not par.get("measurement_id"):
            resumo.append({"par_id": par["par_id"], "periodo": "-", "status": "sem measurement_id", "n_json": 0})
            continue
        for periodo in ("A", "B"):
            try:
                status, n = coletar_periodo(cfg, pastas, par, periodo, janelas, forcar)
            except Exception as e:
                status, n = f"erro: {e}", 0
            resumo.append({"par_id": par["par_id"], "periodo": periodo, "status": status, "n_json": n})
            print(f"par {par['par_id']:>2} período {periodo}: {status} ({n} registros)")
    return pd.DataFrame(resumo)


# --------------------------------------------------------------------------- #
# 4. Tabela bruta (uma linha = uma medição ICMP de um fluxo; sem classe)
# --------------------------------------------------------------------------- #
def _valido(x) -> bool:
    """RTT só existe se for número positivo. -1 da API, None, NaN e 0 são ausência."""
    return isinstance(x, (int, float)) and not math.isnan(x) and x > 0


def linha_bruta(item: dict, par: dict) -> dict:
    rtts = [r["rtt"] for r in item.get("result", []) if isinstance(r, dict) and _valido(r.get("rtt"))]
    enviados = item.get("sent")
    recebidos = item.get("rcvd")
    if enviados is None:
        enviados = len(item.get("result", []))
    if recebidos is None:
        recebidos = len(rtts)

    def pick(campo, fallback):
        v = item.get(campo)
        return v if _valido(v) else fallback

    rtt_avg = pick("avg", statistics.mean(rtts) if rtts else None)
    rtt_min = pick("min", min(rtts) if rtts else None)
    rtt_max = pick("max", max(rtts) if rtts else None)
    perda = max(0.0, (enviados - recebidos) / enviados * 100) if enviados else None
    jitter = statistics.stdev(rtts) if len(rtts) >= 2 else None  # vazio com <2 respostas (nunca 0)
    timeout = 1 if (rtt_avg is None or perda == 100) else 0
    ts = item.get("timestamp")
    prb = item.get("prb_id", par["probe_id"])
    dst = item.get("dst_addr") or par["dst_addr"]
    return {
        "timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts is not None else None,
        "timestamp_epoch": ts,
        "measurement_id": item.get("msm_id", par["measurement_id"]),
        "probe_id": prb,
        "dst_addr": dst,
        "fluxo_id": f"{prb}|{dst}",
        "rtt_avg_ms": rtt_avg, "rtt_min_ms": rtt_min, "rtt_max_ms": rtt_max,
        "enviados": enviados, "recebidos": recebidos,
        "perda_pct": perda, "jitter_ms": jitter, "timeout_atual": timeout,
        # só auditoria de diversidade (fora da futura árvore)
        "par_id": par["par_id"],
        "probe_cidade": par["probe_cidade"], "probe_pais": par["probe_pais"],
        "anchor_cidade": par["anchor_cidade"], "anchor_pais": par["anchor_pais"],
    }


def montar_tabela(cfg, pastas) -> tuple:
    linhas = []
    for par in cfg["pares"]:
        if not par.get("measurement_id"):
            continue
        for periodo in ("A", "B"):
            arq = caminho_json(pastas, par, periodo)
            if not arq.exists():
                continue
            for item in json.loads(arq.read_text(encoding="utf-8")):
                linha = linha_bruta(item, par)
                linha["periodo"] = periodo  # bloco de tempo, NÃO é classe
                linhas.append(linha)
    df = pd.DataFrame(linhas)
    n_json = len(df)
    if n_json == 0:
        return df, 0, 0
    n_dup = int(df.duplicated(CHAVE_DUPLICATA).sum())
    df = (df.drop_duplicates(CHAVE_DUPLICATA)  # a duplicata sai só da tabela; o JSON fica intacto
            .sort_values(["fluxo_id", "timestamp_epoch"]).reset_index(drop=True))
    return df, n_json, n_dup


# --------------------------------------------------------------------------- #
# 5. Relatório de qualidade (sem classe) e metadados
# --------------------------------------------------------------------------- #
def relatorio_qualidade(df, cfg, janelas, n_json, n_dup, pastas):
    if df.empty:
        print("Sem registros brutos — verifique measurement_id e a coleta.")
        return None
    g = df.groupby("fluxo_id")
    rel = pd.DataFrame({
        "par_id": g["par_id"].first(),
        "rota": g["probe_cidade"].first() + " (" + g["probe_pais"].first() + ") -> "
                + g["anchor_cidade"].first() + " (" + g["anchor_pais"].first() + ")",
        "registros": g.size(),
        "reg_periodo_A": g["periodo"].apply(lambda s: int((s == "A").sum())),
        "reg_periodo_B": g["periodo"].apply(lambda s: int((s == "B").sum())),
        "inicio_utc": g["timestamp"].min(),
        "fim_utc": g["timestamp"].max(),
        "rtt_ausente": g["rtt_avg_ms"].apply(lambda s: int(s.isna().sum())),
        "jitter_ausente": g["jitter_ms"].apply(lambda s: int(s.isna().sum())),
        "timeouts": g["timeout_atual"].sum().astype(int),
        "rtt_min_ms": g["rtt_avg_ms"].min(),
        "rtt_mediana_ms": g["rtt_avg_ms"].median(),
        "rtt_max_ms": g["rtt_avg_ms"].max(),
        "perda_min_pct": g["perda_pct"].min(),
        "perda_mediana_pct": g["perda_pct"].median(),
        "perda_max_pct": g["perda_pct"].max(),
    }).sort_values("par_id")
    rel.to_csv(pastas["reports"] / "relatorio_qualidade_coleta.csv", encoding="utf-8")
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", None)
    print(rel.to_string())

    a = df.loc[df["periodo"] == "A", "timestamp_epoch"]
    b = df.loc[df["periodo"] == "B", "timestamp_epoch"]
    fora = ~(((df.periodo == "A") & df.timestamp_epoch.between(janelas["A"][0], janelas["A"][1] - 1))
             | ((df.periodo == "B") & df.timestamp_epoch.between(janelas["B"][0], janelas["B"][1] - 1)))
    aud = cfg["auditoria"]
    med = rel["rtt_mediana_ms"].dropna()
    curtos = rel.loc[med[med <= aud["caminho_curto_ate_ms"]].index, "rota"].tolist()
    longos = rel.loc[med[med >= aud["caminho_longo_a_partir_ms"]].index, "rota"].tolist()
    sem_dados = [p["par_id"] for p in cfg["pares"] if p["probe_id"] not in set(df["probe_id"])]

    linhas = [
        f"N de registros brutos (lidos do JSON): {n_json}",
        f"N de registros na tabela (sem duplicatas): {len(df)}",
        f"N de fluxos com dados: {df['fluxo_id'].nunique()} de {len(cfg['pares'])} pares do config",
        f"Pares sem nenhum registro: {sem_dados or 'nenhum'}",
        f"Duplicatas removidas da tabela: {n_dup}",
        f"Timeouts preservados (total): {int(df['timeout_atual'].sum())}",
        f"RTT ausente / jitter ausente: {int(df['rtt_avg_ms'].isna().sum())} / {int(df['jitter_ms'].isna().sum())}",
        f"Linhas fora da janela do próprio período: {int(fora.sum())}",
        f"Sobreposição entre Período A e B: {'NÃO' if (len(a) and len(b) and a.max() < b.min()) else 'verificar'}",
        f"Caminhos curtos (mediana <= {aud['caminho_curto_ate_ms']} ms): {curtos or 'NENHUM — considere incluir um par mais próximo'}",
        f"Caminhos longos (mediana >= {aud['caminho_longo_a_partir_ms']} ms): {longos or 'NENHUM'}",
        f"Pares geográficos (auditoria): {sorted({f'{r.probe_pais}->{r.anchor_pais}' for r in df.itertuples()})}",
        "(RTT alto não é falha; esta etapa não atribui classe.)",
    ]
    texto = "\n".join(linhas)
    print("\n" + texto)
    (pastas["reports"] / "resumo_qualidade_coleta.txt").write_text(texto + "\n", encoding="utf-8")
    return rel


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def salvar_metadados(df, cfg, n_json, n_dup, pastas):
    meta = {
        "projeto": "NetVision", "tarefa": "Tarefa 1 - coleta bruta (sem rotulo)",
        "fonte": "RIPE Atlas API v2 (GET) - medicoes mesh de ping IPv4",
        "timestamp_execucao_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "periodo_a": cfg["periodo_a"], "periodo_b": cfg["periodo_b"],
        "pares": [{k: p.get(k) for k in ("par_id", "probe_id", "anchor_id", "dst_addr", "measurement_id")}
                  for p in cfg["pares"]],
        "registros_json": int(n_json), "registros_tabela": int(len(df)),
        "duplicatas_removidas_da_tabela": int(n_dup),
        "fluxos_com_dados": int(df["fluxo_id"].nunique()) if len(df) else 0,
        # a Tarefa 2 confere estes hashes para provar que o bruto não foi alterado
        "sha256_json_bruto": {p.name: sha256(p) for p in sorted(pastas["raw_json"].glob("*.json"))},
    }
    gravar_json_atomico(pastas["raw"] / "metadados_coleta.json", meta, indent=2)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="Tarefa 1 — coleta bruta RIPE Atlas (sem rótulo)")
    ap.add_argument("--base-dir", type=Path, default=Path(__file__).resolve().parent,
                    help="raiz do projeto (contém config/ e recebe data/ e reports/)")
    ap.add_argument("--drive", nargs="?", const="", default=None, metavar="PASTA",
                    help="Google Colab: salva tudo em Meu Drive/PASTA (padrão: netvision)")
    ap.add_argument("--forcar-recoleta", action="store_true", help="rebaixa e sobrescreve os JSON brutos")
    ap.add_argument("--so-tabela", action="store_true", help="não acessa a rede: reconstrói tabela e relatório")
    ap.add_argument("--pular-validacao", action="store_true", help="não valida os pares na API")
    args = ap.parse_args()

    from drive_colab import resolver_base
    pastas = pastas_do_projeto(resolver_base(args.base_dir, args.drive))
    caminho_cfg, cfg = carregar_config(pastas)
    janelas = periodos(cfg)
    print(f"Período A: {cfg['periodo_a']} | Período B: {cfg['periodo_b']} | pares: {len(cfg['pares'])}")

    if not args.so_tabela:
        if not args.pular_validacao:
            print("\n== Validação dos pares ==")
            print(validar_pares(cfg, pastas).to_string(index=False))
        print("\n== Medição de cada par ==")
        garantir_medicoes(cfg, caminho_cfg)
        print("\n== Coleta do JSON bruto ==")
        coletar_tudo(cfg, pastas, janelas, args.forcar_recoleta)

    print("\n== Tabela bruta ==")
    df, n_json, n_dup = montar_tabela(cfg, pastas)
    if df.empty:
        sys.exit("Nenhum registro bruto encontrado.")
    df.to_csv(pastas["raw"] / "ping_bruto.csv", index=False, encoding="utf-8")  # NaN -> vazio, nunca 0
    amostra = df.groupby("fluxo_id").head(cfg["auditoria"]["amostra_linhas_por_fluxo"])
    amostra.to_csv(pastas["raw"] / "ping_bruto_amostra.csv", index=False, encoding="utf-8")
    print(f"{len(df)} linhas em {pastas['raw'] / 'ping_bruto.csv'}")

    print("\n== Relatório de qualidade (sem classe) ==")
    relatorio_qualidade(df, cfg, janelas, n_json, n_dup, pastas)
    salvar_metadados(df, cfg, n_json, n_dup, pastas)
    print("\nConcluído. Entrega: config/, data/raw/ (json + ping_bruto.csv), requirements.txt, reports/.")


if __name__ == "__main__":
    main()

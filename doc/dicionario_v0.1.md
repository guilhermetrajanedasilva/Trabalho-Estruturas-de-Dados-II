# Dicionário de Dados v0.1 — Variáveis Brutas da Coleta

**Projeto:** Preditor de degradação de rede com RTT normalizado  
**Versão:** 0.1 (somente variáveis brutas da medição ICMP)  
**Última atualização:** 01/11/2026  
**Origem:** `data/raw/ping_bruto.csv`, gerado por `coleta_bruta.py` a partir do JSON original em `data/raw/json/`

> **Nota:** este dicionário contém exclusivamente as colunas da coleta bruta do RIPE Atlas. Não inclui baseline, escores relativos (`z_robusto`, `aumento_pct`, `jitter_relativo`), janelas (`n5_*`) nem rótulo de classe (OK, RISCO, FALHA). `perda_pct`, `jitter_ms` e `timeout_atual` são campos brutos previstos na Tarefa 1 e dependem só da própria medição.

## 1. Escopo da coleta

| Item | Valor |
|---|---|
| Fonte | RIPE Atlas API v2, somente `GET`; medições mesh de ping IPv4 já existentes (nenhuma medição própria, nenhum crédito gasto) |
| Fluxos | 8 pares `probe → anchor` (de 10 pares formados; os pares 3 e 7 originais foram retirados, ver seção 4) |
| Período A | 06/09/2026 04:32 UTC a 13/09/2026 04:32 UTC (7 dias) |
| Período B | 13/09/2026 04:32 UTC a 20/09/2026 04:32 UTC (7 dias), contíguo ao A e sem sobreposição |
| Registros | 39.677 (19.547 no Período A e 20.130 no Período B), sem duplicatas |
| Timeouts | 88, preservados no arquivo |

## 2. Colunas de `data/raw/ping_bruto.csv`

Cada linha é **uma medição ICMP de um fluxo**, com timestamp. Ainda sem classe.

| Coluna | Tipo | Unidade | Descrição / regra |
|---|---|---|---|
| `timestamp` | String (ISO 8601) | UTC | Instante da medição, no formato `AAAA-MM-DDTHH:MM:SSZ`. |
| `timestamp_epoch` | Int64 | segundos (epoch UTC) | Mesmo instante em epoch. Usado para ordenar o fluxo e detectar duplicatas. |
| `measurement_id` | Int64 | — | Identificador da medição mesh no RIPE Atlas cujo destino é a anchor do par (descoberto via API e gravado em `config/config_coleta.json`). |
| `probe_id` | Int64 | — | Sonda de origem do fluxo. |
| `dst_addr` | String | IPv4 | Endereço IP do destino (a anchor do par). |
| `fluxo_id` | String | — | Chave do fluxo: `probe_id\|dst_addr`. |
| `rtt_avg_ms` | Float64 | ms | RTT médio da rajada (tipicamente 3 pacotes). **Vazio** se não houve resposta. Nunca 0; o `-1` da API também vira vazio. |
| `rtt_min_ms` | Float64 | ms | Menor RTT da rajada. Vazio se não houve resposta. |
| `rtt_max_ms` | Float64 | ms | Maior RTT da rajada. Vazio se não houve resposta. |
| `enviados` | Int64 | contagem | Pacotes ICMP enviados na rajada (3 no mesh). |
| `recebidos` | Int64 | contagem | Pacotes ICMP que retornaram. |
| `perda_pct` | Float64 | % | `(enviados − recebidos) / enviados × 100`. Com 3 pacotes só assume 0, 33,3, 66,7 ou 100. |
| `jitter_ms` | Float64 | ms | Desvio-padrão amostral dos RTT da rajada, **somente** com 2 ou mais respostas. Com 0 ou 1 resposta fica vazio. Nunca 0 fingindo estabilidade. |
| `timeout_atual` | Int (0 ou 1) | — | 1 se não há RTT ou `perda_pct` = 100; senão 0. |
| `periodo` | String (`A` ou `B`) | — | Bloco de tempo da coleta. **Não é classe.** A é só para o baseline (Tarefa 2); B é o que será rotulado. |

### Colunas de auditoria de diversidade (fora da matriz do modelo)

| Coluna | Tipo | Descrição |
|---|---|---|
| `par_id` | Int | Número do par no `config/config_coleta.json` (1 a 8). |
| `probe_cidade`, `probe_pais` | String | Cidade e país (ISO) da sonda de origem. |
| `anchor_cidade`, `anchor_pais` | String | Cidade e país (ISO) da anchor de destino. |

Servem só para documentar a diversidade geográfica. Não entram em classe, regra de rótulo nem modelo.

## 3. Outros arquivos da camada `raw`

| Arquivo | Conteúdo |
|---|---|
| `data/raw/json/m{measurement_id}_probe{probe_id}_periodo{A\|B}.json` | JSON exatamente como veio da API. Nunca sobrescrito. |
| `data/raw/metadados_coleta.json` | Parâmetros, contagens e SHA-256 de cada JSON bruto (a Tarefa 2 confere os hashes). |
| `data/raw/validacao_pares.csv` | Conferência informativa de cada par na API (IP da anchor e status atual da sonda). |
| `data/raw/ping_bruto_amostra.csv` | Amostra pequena (até 200 linhas por fluxo) para o repositório. |
| `reports/relatorio_qualidade_coleta.csv`, `reports/resumo_qualidade_coleta.txt` | Relatório de qualidade, sem classe. |

## 4. Pares da coleta

| par_id | Probe | Origem | Anchor | Destino | `measurement_id` |
|---|---|---|---|---|---|
| 1 | 7586 | Cochabamba (BO) | 2825 Dubai (AE) | 80.77.4.60 | 34466562 |
| 2 | 6891 | Belo Horizonte (BR) | 3387 Dubai (AE) | 63.222.248.5 | 51454782 |
| 3 | 7307 | Feira de Santana (BR) | 1213 Dubai (AE) | 37.252.245.94 | 15872959 |
| 4 | 7508 | Osasco (BR) | 1370 Feldkirch (AT) | 94.199.170.201 | 18840705 |
| 5 | 6878 | Minsk (BY) | 2248 Klagenfurt (AT) | 143.205.170.32 | 26365043 |
| 6 | 6719 | Beauharnois (CA) | 3743 Melbourne (AU) | 203.41.0.51 | 68443192 |
| 7 | 7258 | Richterswil (CH) | 4302 Perth (AU) | 202.87.175.244 | 107969426 |
| 8 | 7656 | Satigny (CH) | 4542 Sydney (AU) | 103.153.238.101 | 153102772 |

Pares retirados: Camaçari (BR) → 185.34.2.114 (sonda 7457) e Mississauga (CA) → 92.60.13.86 (sonda 7682). A medição mesh devolveu JSON vazio para os dois nos Períodos A e B, então não havia dado para formar fluxo. A numeração acima foi refeita de 1 a 8.

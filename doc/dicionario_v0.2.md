# Dicionário de Dados — Versão 0.2

**Projeto:** Preditor de degradação de rede com RTT normalizado  
**Última atualização:** 01/11/2026  
**Gerado por:** `baseline_rotulagem.py` (Tarefa 2), lendo o bruto da Tarefa 1  
**Configuração:** `config/config_rotulagem.json` (limiares e fórmulas) e `config/config_coleta.json` (períodos)

---

## 1. Dados brutos (`data/raw/`) — Tarefa 1

Herdados da Tarefa 1 e mantidos sem alteração. Colunas completas em `dicionario_v0.1.md`. Resumo:

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `timestamp`, `timestamp_epoch` | String UTC / Int64 | Instante da medição |
| `measurement_id`, `probe_id`, `dst_addr` | Int64 / Int64 / String | Medição, sonda de origem e IP de destino |
| `fluxo_id` | String | `probe_id\|dst_addr` |
| `rtt_avg_ms`, `rtt_min_ms`, `rtt_max_ms` | Float | RTT da rajada (ms). Vazio se não houve resposta, nunca 0 |
| `enviados`, `recebidos` | Int | Pacotes da rajada |
| `perda_pct` | Float | `(enviados − recebidos) / enviados × 100` |
| `jitter_ms` | Float | Desvio-padrão dos RTT da rajada, só com 2 ou mais respostas |
| `timeout_atual` | Int (0/1) | 1 se não há RTT ou `perda_pct` = 100 |
| `periodo` | String | `A` ou `B` (bloco de tempo, não classe) |
| `par_id`, `probe_cidade`, `probe_pais`, `anchor_cidade`, `anchor_pais` | — | Auditoria de diversidade |

A Tarefa 2 recalcula o período pelo timestamp (A: 06/09 04:32 a 13/09 04:32 UTC; B: 13/09 04:32 a 20/09 04:32 UTC) e confere o SHA-256 dos JSON brutos.

---

## 2. Tabela de trabalho (`data/interim/`)

| Arquivo | Conteúdo |
| :--- | :--- |
| `ping_trabalho.csv` | Bruto sem duplicatas, ordenado por fluxo e tempo, com `periodo` recalculado. Não substitui o bruto. |
| `auditoria_fluxos.csv` | Um fluxo por linha, com `par_id`, país, cidade e IP. **Só auditoria**, nunca entra na árvore. |

---

## 3. Ficha de baseline (`data/processed/baseline_por_fluxo.csv`) — somente Período A

Uma linha por `fluxo_id`, calculada só com o Período A e congelada. O Período B não entra na conta. Se o bruto mudar, o script para (a ficha só é regravada com `--recalcular-baseline`).

| Coluna | Tipo | Descrição / fórmula |
| :--- | :--- | :--- |
| `fluxo_id` | String | Identificador do fluxo |
| `status` | String | `ok` ou `baseline_insuficiente` |
| `motivo` | String | Texto do motivo quando não há ficha (vazio se `ok`) |
| `n_medicoes_A` | Int | Medições do fluxo no Período A |
| `n_rtt_validos_A` | Int | Medições com RTT presente no Período A. Menos de **1.500** → `baseline_insuficiente`, sem classe e sem mediana inventada |
| `mediana` | Float (ms) | Mediana dos RTT válidos |
| `mad` | Float (ms) | `mediana(abs(RTT − mediana))` dos RTT válidos |
| `iqr` | Float (ms) | `Q3 − Q1` dos RTT válidos. Usado só quando `mad` = 0 |
| `jitter_tipico` | Float (ms) | Mediana do jitter nas medições em que o jitter existe |
| `perda_tipica` | Float (%) | Mediana de `perda_pct` em todas as medições do período, inclusive timeout |
| `prop_resposta` | Float | Medições com RTT válido / medições do período |

Timeout fica fora da mediana e do MAD e continua no dataset como evento.

**Resultado nesta coleta:** 8 fluxos com ficha, 0 excluídos. Medianas do Período A: 26,0 ms (Minsk → Klagenfurt) a 373,1 ms (Cochabamba → Dubai).

---

## 4. Dataset rotulado do Período B (`data/processed/dataset_rotulado_B.csv`)

Uma linha por medição do Período B de um fluxo com ficha (20.130 linhas). O Período A não é rotulado. Métricas calculadas só com a ficha congelada daquele fluxo.

| Coluna | Tipo | Descrição / regra |
| :--- | :--- | :--- |
| `timestamp` | String UTC | Instante da medição (chave de ordenação) |
| `fluxo_id` | String | Identificador do fluxo (só para ordenar e agrupar) |
| `split` | String | `treino`, `validacao` ou `teste` (recorte temporal dentro de B) |
| `rtt_ms` | Float | RTT médio da rajada. Vazio se timeout. Guardado para rastreio, não é feature |
| `jitter_ms` | Float | Jitter da rajada. Vazio com menos de 2 respostas. Guardado para rastreio |
| `z_robusto` | Float | `(RTT − mediana) / (1,4826 × MAD)`. Vazio se RTT ausente |
| `aumento_pct` | Float | `(RTT − mediana) / mediana × 100`. Vazio se RTT ausente |
| `jitter_relativo` | Float | `jitter_atual / jitter_tipico`. Vazio se jitter atual vazio |
| `perda_pct` | Float | `(enviados − recebidos) / enviados × 100` |
| `timeout_atual` | Int (0/1) | 1 se RTT ausente ou `perda_pct` = 100 |
| `n5_timeout` | Int (0 a 5) | Timeouts nas últimas 5 medições do fluxo, incluindo a atual |
| `n5_aumento80` | Int (0 a 5) | Quantas das últimas 5 têm `aumento_pct` > 80 |
| `n5_risco` | Int (0 a 5) | Quantas das últimas 5 cumprem o critério de risco da linha 5 |
| `criterio_risco_atual` | Int (0/1) | Auxiliar: 1 se, nesta medição, `2 ≤ z_robusto < 3,5` ou `30 ≤ aumento_pct ≤ 80` ou `jitter_relativo ≥ 3` |
| `classe` | String | **OK**, **RISCO** ou **FALHA** (alvo) |
| `regra_disparada` | String | Linha da tabela que decidiu a classe (`1_perda` … `6_ok`), para auditoria |

**Janela das últimas 5 medições:** conta apenas medições do próprio Período B. As 4 primeiras de cada fluxo têm janela menor. Assim nenhum dado do Período A entra no B.

### Casos de conta

| Situação | Tratamento |
| :--- | :--- |
| RTT ausente | Não calcula `z_robusto` nem `aumento_pct`; `timeout_atual` = 1; nunca usa 0 ms |
| `mad` = 0 e RTT = mediana | `z_robusto` = 0 |
| `mad` = 0 e RTT ≠ mediana | Denominador = `max(iqr / 1,349; 1 ms)` |
| Jitter atual vazio | O critério de jitter não dispara |
| `jitter_tipico` = 0 e jitter atual = 0 | `jitter_relativo` = 1 |
| `jitter_tipico` = 0 e jitter atual > 0 | `jitter_relativo` gravado como 3 (equivale a "≥ 3") |

### Tabela de rotulagem (primeira linha verdadeira vence)

| Ordem | Classe | Condição |
| :--- | :--- | :--- |
| 1 | FALHA | `perda_pct` ≥ 10 |
| 2 | FALHA | `n5_timeout` ≥ 3 |
| 3 | FALHA | `z_robusto` ≥ 3,5 com RTT presente |
| 4 | FALHA | `n5_aumento80` ≥ 2 |
| 5 | RISCO | `criterio_risco_atual` = 1 e `n5_risco` ≥ 2 |
| 6 | OK | nenhuma anterior |

Limiares em `config/config_rotulagem.json`. A classe não usa RTT absoluto, país nem nome da rota.

**Contagem no Período B:** OK 14.897 (74,0%), RISCO 2.447 (12,2%), FALHA 2.786 (13,8%).

---

## 5. Recorte temporal (`data/processed/corte_temporal.csv`)

Dentro do Período B, por fluxo, em ordem de tempo: treino (mais antigo), validação (meio) e teste (mais recente). Proporção de partida 50% / 20% / 30%, ajustada só se algum bloco ficar sem RISCO (não foi necessário). N total: treino 10.067, validação 4.029, teste 6.034.

| Coluna | Descrição |
| :--- | :--- |
| `fluxo_id` | Fluxo |
| `n_treino`, `n_validacao`, `n_teste` | Linhas de cada bloco |
| `inicio_*`, `fim_*` | Primeiro e último timestamp de cada bloco (`treino`, `validacao`, `teste`) |

Nenhum registro do Período A entra no treino.

---

## 6. Colunas para a árvore (`data/processed/colunas_arvore.json`)

**Entradas permitidas (8):** `z_robusto`, `aumento_pct`, `jitter_relativo`, `perda_pct`, `timeout_atual`, `n5_timeout`, `n5_aumento80`, `n5_risco`.  
**Alvo:** `classe`.

## 7. Colunas proibidas para o treino da árvore (Tarefas 3 a 5)

Para garantir a **independência de rota** e impedir vazamento (*data leakage*), estas colunas **não podem** ser passadas ao modelo:

- `fluxo_id`
- país, cidade e IP (`probe_pais`, `anchor_pais`, `probe_cidade`, `anchor_cidade`, `dst_addr`), `par_id` e qualquer `rota_id`
- `rtt_ms` e `jitter_ms` (valores absolutos; as métricas relativas os substituem)
- `timestamp` (só ordena e recorta)
- `split`, `regra_disparada` e `criterio_risco_atual` (derivadas do rótulo ou auxiliares)
- `classe` como entrada (é o alvo)

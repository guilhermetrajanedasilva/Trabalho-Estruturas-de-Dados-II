# Dicionário de Dados — Versão 0.2

**Projeto:** Preditor de degradação de rede com RTT normalizado  
**Última Atualização:** 30/09/2026  

---

## 1. Dados Brutos (`data/raw/`) — Ingestão Tarefa 1
* Herdados da Tarefa 1 e mantidos sem alteração.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `timestamp` | Datetime (UTC) | Instante exato da medição de rede |
| `fluxo_id` | String / Int | Identificador do fluxo de rede |
| `rtt` | Float | Round Trip Time em milissegundos (`NaN` para timeouts) |
| `jitter` | Float | Variação do tempo de resposta (ms) |
| `enviados` | Int | Quantidade de pacotes transmitidos na medição |
| `recebidos` | Int | Quantidade de pacotes recebidos na medição |
| `rota_id` | String | Identificador da rota utilizada |
| `ip_origem` / `ip_destino` | String | Endereços IP das extremidades |
| `pais_destino` | String | Código do país de destino |

---

## 2. Ficha de Baseline (`baseline_por_fluxo.csv`) — Período A
* Calculado exclusivamente com amostras válidas do **Período A** (mínimo 1.500 amostras).

| Coluna | Tipo | Descrição / Fórmula |
| :--- | :--- | :--- |
| `fluxo_id` | String / Int | Identificador do fluxo de rede |
| `mediana` | Float | Mediana dos RTTs válidos do Período A (ms) |
| `MAD` | Float | Mediana do desvio absoluto em relação à mediana no Período A |
| `jitter_tipico` | Float | Mediana do jitter nas medições válidas do Período A (ms) |
| `perda_tipica` | Float | Mediana da taxa de perda (%) no Período A |
| `prop_resposta` | Float | Razão entre medições com RTT válido e total de medições no Período A |

---

## 3. Dataset Rotulado do Período B (`data/interim/dataset_rotulado_B.parquet`)
* Métricas relativas e variáveis temporais calculadas em relação à ficha do fluxo.

| Coluna | Tipo | Descrição / Regra |
| :--- | :--- | :--- |
| `timestamp` | Datetime | Instante da medição |
| `z_robusto` | Float | `(RTT - mediana) / (1.4826 * MAD)` |
| `aumento_pct` | Float | `((RTT - mediana) / mediana) * 100` |
| `jitter_relativo` | Float | `jitter_atual / jitter_tipico` |
| `perda_pct` | Float | `((enviados - recebidos) / enviados) * 100` |
| `timeout_atual` | Int (0 ou 1) | `1` se RTT ausente ou `perda_pct == 100`; senão `0` |
| `n5_timeout` | Int (0 a 5) | Total de timeouts nas últimas 5 medições do fluxo |
| `n5_aumento80` | Int (0 a 5) | Quantidade de medições com `aumento_pct > 80` nas últimas 5 |
| `n5_risco` | Int (0 a 5) | Quantidade de medições nas últimas 5 com indício de risco |
| `classe` | String | Categorização da saúde da rede: **OK**, **RISCO** ou **FALHA** |

---

## 4. Colunas Proibidas para Treino da Árvore (Tarefas 3 a 5)
Para garantir a **independência de rota** e impedir vazamento de dados (*data leakage*), as seguintes colunas **NÃO PODEM** ser passadas para o modelo preditivo:

- `rtt` (RTT absoluto)
- `fluxo_id`
- `rota_id`
- `ip_origem` / `ip_destino`
- `pais_destino` / país de origem

# Dicionário de Dados v0.1 — Variáveis Brutas da Coleta

**Projeto:** Preditor de degradação de rede com RTT normalizado  
**Versão:** 0.1 (Somente variáveis brutas da medição ICMP)

> **Nota:** Este dicionário contém exclusivamente as colunas da coleta bruta do RIPE Atlas. Não inclui variáveis calculadas, baselines, escores ou rótulos de classe (OK, RISCO, FALHA).

| Coluna | Tipo | Unidade | Descrição / Regra |
|---|---|---|---|
| `timestamp` | Datetime / Int64 | UTC (Epoch) | Instante da realização da medição ICMP. |
| `measurement_id` | Int64 | — | Identificador numérico da medição no RIPE Atlas (ex: 1001). |
| `probe_id` | Int64 | — | Identificador único da sonda origem (Anchor) que disparou o ping. |
| `dst_addr` | String | IPv4 | Endereço IP do alvo/destino da medição. |
| `fluxo_id` | String | — | Chave primária do fluxo, formada por `probe_id\|dst_addr`. |
| `rtt_ms` (ou `avg`) | Float64 | ms | RTT médio da rajada de pings. Permanece vazio/NaN se não houver resposta. **Nunca 0**. |
| `enviados` | Int64 | contagem | Quantidade de pacotes ICMP enviados na rajada (tipicamente 3 no mesh). |
| `recebidos` | Int64 | contagem | Quantidade de pacotes ICMP que retornaram com sucesso. |
| `perda_pct` | Float64 | % | Percentual de perda calculada por `((enviados - recebidos) / enviados) * 100`. |
| `jitter_ms` | Float64 | ms | Desvio-padrão dos RTTs da rajada. Vazio se houver menos de 2 respostas. **Nunca 0**. |
| `timeout_atual` | Int64 | 0 ou 1 | Marcador de indisponibilidade: 1 se não houve resposta de RTT ou `perda_pct` == 100%; caso contrário 0. |
| `pais_origem` / `rota` | String | Texto | Informação geográfica do fluxo usada apenas para auditoria de diversidade. **Fora da matriz do modelo**. |

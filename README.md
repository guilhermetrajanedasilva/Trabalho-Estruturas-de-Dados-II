# NetVision — Preditor de degradação de rede com RTT normalizado

## Objetivo
O **NetVision** é um projeto integrador da disciplina de Estrutura de Dados II. Ele constrói um pipeline de dados que coleta medições de ping (ICMP) já existentes na rede pública do RIPE Atlas, estima o **normal de cada fluxo** e classifica cada medição em **OK**, **RISCO** ou **FALHA** em relação a esse normal.

A ideia central é que **RTT alto não é falha**. Um RTT de 370 ms pode ser o normal de um caminho Bolívia→Dubai, e um salto de 25 ms para 58 ms pode ser degradação num caminho curto. Por isso a classe nasce do afastamento do fluxo em relação ao próprio baseline, e não de um limiar global de RTT, nem de país, IP ou nome da rota.

O vetor de entrada do modelo é relativo ao fluxo:

X = [z_robusto, aumento_pct, jitter_relativo, perda_pct, timeout_atual, n5_timeout, n5_aumento80, n5_risco]

Detalhes do problema, da regra de rótulo e da avaliação estão no [RFC](docs/RFC_Preditor_Degradacao_Rede.md).

---

## Descrição do projeto
O projeto lê, somente com `GET`, as medições **mesh de ping IPv4** das Anchors do RIPE Atlas. Não cria medições próprias e não gasta créditos. O pipeline tem três etapas:

| Etapa | Script | O que produz |
|---|---|---|
| **Tarefa 1 — Coleta bruta** | `coleta_bruta.py` | JSON original da API, tabela bruta **sem rótulo**, relatório de qualidade |
| **Tarefa 2 — Baseline e rotulagem** | `baseline_rotulagem.py` | Ficha de baseline por fluxo, dataset do Período B rotulado, recorte temporal |
| **Tarefas 3 a 5 — Modelo** | (próximas etapas) | Árvore de decisão, avaliação e comparação com a persistência |

### Dados coletados
- **Fluxos:** 8 pares `probe → anchor`, com um caminho curto (Minsk → Klagenfurt, mediana de 26 ms) e sete longos (de 199 a 373 ms). A diversidade geográfica serve só para auditoria e não vira classe.
- **Períodos:** Período A, de 06/09/2026 04:32 UTC a 13/09/2026 04:32 UTC, usado só para o baseline. Período B, de 13/09/2026 04:32 UTC a 20/09/2026 04:32 UTC, que é rotulado. Os dois são contíguos e sem sobreposição.
- **Volume:** 39.677 registros brutos (19.547 no A e 20.130 no B), 88 timeouts preservados e nenhuma duplicata.
- **Rótulos no Período B:** 14.897 OK (74,0%), 2.447 RISCO (12,2%) e 2.786 FALHA (13,8%).
- **Recorte temporal (dentro de B, por fluxo):** treino 10.067, validação 4.029 e teste 6.034 linhas (50% / 20% / 30%).
- **Pares retirados:** dos 10 pares formados, dois (sonda 7457, Camaçari → 185.34.2.114, e sonda 7682, Mississauga → 92.60.13.86) vieram sem nenhum registro na medição mesh e foram retirados.

### Regras que o projeto respeita
- O JSON bruto é preservado e nunca sobrescrito. A Tarefa 2 confere o SHA-256 de cada arquivo.
- Timeout continua no arquivo. RTT ausente fica vazio, nunca 0.
- O jitter só existe com 2 ou mais respostas na rajada.
- O baseline usa só o Período A, exige pelo menos 1.500 RTT válidos e fica congelado.
- País, IP, rota e RTT absoluto ficam fora das colunas da árvore.
- Parâmetros (períodos, pares, limiares) ficam em `config/`, não no código.

---

## Estrutura do repositório

```
├── coleta_bruta.py              # Tarefa 1
├── baseline_rotulagem.py        # Tarefa 2
├── requirements.txt
├── config/
│   ├── config_coleta.json       # períodos A/B, 8 pares, measurement_id, parâmetros HTTP
│   └── config_rotulagem.json    # piso de 1.500, limiares do rótulo, proporção do recorte
├── data/
│   ├── raw/                     # saída da Tarefa 1 (json/ + ping_bruto.csv + metadados)
│   ├── interim/                 # tabela de trabalho e auditoria de fluxos
│   └── processed/               # baseline_por_fluxo.csv, dataset_rotulado_B.csv, corte_temporal.csv
├── reports/                     # relatório de qualidade, exemplos auditáveis, resumos
└── docs/                        # RFC e dicionários de dados
```

## Como executar

Requer Python 3.9 ou superior.

```bash
pip install -r requirements.txt

# Tarefa 1 — coleta bruta (acessa a API do RIPE Atlas, somente GET)
python coleta_bruta.py

# Tarefa 2 — baseline e rotulagem (usa só o bruto da Tarefa 1, sem rede)
python baseline_rotulagem.py
```

Opções úteis:

| Comando | Para que serve |
|---|---|
| `python coleta_bruta.py --base-dir /caminho` | Usar outra pasta como raiz (por exemplo, uma pasta do Google Drive) |
| `python coleta_bruta.py --so-tabela` | Refazer tabela e relatório a partir dos JSON, sem acessar a rede |
| `python coleta_bruta.py --forcar-recoleta` | Baixar os JSON de novo (só se for intencional) |
| `python baseline_rotulagem.py --recalcular-baseline` | Regravar o baseline congelado (só se o bruto foi versionado de propósito) |

A coleta é idempotente: se o JSON de um par e período já existe, ele não é baixado de novo. Rodar a Tarefa 1 duas vezes não duplica nem altera dados.

## Documentação
- [RFC — problema, regra de rótulo, avaliação e riscos](docs/RFC_Preditor_Degradacao_Rede.md)
- [Dicionário de dados v0.1 — variáveis brutas](docs/dicionario_v0.1.md)
- [Dicionário de dados v0.2 — ficha, métricas, classe e colunas proibidas](docs/dicionario_v0.2.md)

---

## Integrantes do grupo

- **Guilherme Trajane da Silva**
- **Leandro do Nascimento Lemes**
- **Mariana Moreira Barbosa**
- **Samara Fernandes Soares**
- **Vitor Julião Diogo dos Santos**

### Informações acadêmicas
- **Curso / Disciplina:** Ciência da Computação / Estrutura de Dados II (4º semestre, noturno)
- **Orientadora:** Profª. Andrea Ono Sakai

# NetVision — Preditor de degradação de rede com RTT normalizado

## Objetivo
O **NetVision** é um projeto integrador da disciplina de Estrutura de Dados II. Ele constrói um pipeline de dados que coleta medições de ping (ICMP) já existentes na rede pública do RIPE Atlas, estima o **normal de cada fluxo** e classifica cada medição em **OK**, **RISCO** ou **FALHA** em relação a esse normal.

A ideia central é que **RTT alto não é falha**. Um RTT de 370 ms pode ser o normal de um caminho Bolívia→Dubai, e um salto de 25 ms para 58 ms pode ser degradação num caminho curto. Por isso a classe nasce do afastamento do fluxo em relação ao próprio baseline, e não de um limiar global de RTT, nem de país, IP ou nome da rota.

O vetor de entrada do modelo é relativo ao fluxo:

X = [z_robusto, aumento_pct, jitter_relativo, perda_pct, timeout_atual, n5_timeout, n5_aumento80, n5_risco]

O problema, a regra de rótulo e a avaliação estão no [RFC](src/RFC_Preditor_Degradacao_Rede.md).

---

## Resultado em uma olhada
O modelo é uma **árvore de decisão** (CART, Gini, `max_depth` 5, `min_samples_leaf` 2, 12 folhas) treinada só com as 8 colunas relativas acima. O que foi entregue é um **detector** do estado atual da medição. O preditor de 12 minutos e a comparação com a persistência não foram feitos.

| Medida | Resultado |
|---|---|
| Teste temporal (6.034 linhas, medido uma vez) | F1 macro **0,9995**, recall de FALHA **1,0000**, recall de RISCO 0,9976 |
| Erros no teste | 2 (RISCO previsto como OK, a menos de 0,02 do limiar de `z_robusto`) |
| Fluxos não vistos (um a um) | Recall de OK de 0,9985 a 1,0000; fluxo curto com 100% de acerto |
| Pior caso em fluxo não visto | Feira de Santana → Dubai, recall de FALHA 0,4483 (perda parcial de pacotes) |

**Leitura honesta:** o rótulo foi construído com as mesmas métricas que a árvore recebe, então a árvore reaprende a tabela de rotulagem. O resultado mostra que a política é aprendível só com colunas relativas, sem rota e sem RTT absoluto. Não prova que a árvore descobriu falhas reais da rede.

---

## Dados coletados
O projeto lê, somente com `GET`, as medições **mesh de ping IPv4** das Anchors do RIPE Atlas. Não cria medições próprias e não gasta créditos.

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
- O teste temporal é medido uma vez (o `arvore_final.py` se recusa a repetir sem `--repetir`).
- Parâmetros (períodos, pares, limiares, árvore) ficam em `config/`, não no código.

---

## Estrutura do repositório

```
├── README.md
├── requirements.txt
├── config/
│   ├── config_coleta.json       # períodos A/B, 8 pares, measurement_id, parâmetros HTTP
│   ├── config_rotulagem.json    # piso de 1.500, limiares do rótulo, proporção do recorte
│   └── config_arvore.json       # semente, grades das Tarefas 3 e 4 e parâmetros finais
├── src/                         # código e documentos de apoio
│   ├── coleta_bruta.py          # Tarefa 1
│   ├── baseline_rotulagem.py    # Tarefa 2
│   ├── arvore_comum.py          # funções comuns das Tarefas 3 a 5 (não é executado)
│   ├── arvore_inicial.py        # Tarefa 3
│   ├── ajuste_arvore.py         # Tarefa 4
│   ├── arvore_final.py          # Tarefa 5
│   ├── drive_colab.py           # opção --drive: salvar no Google Drive (Colab)
│   ├── RFC_Preditor_Degradacao_Rede.md
│   ├── memorando_de_decisao_grupo15.md   # decisão da fonte de dados (API do RIPE Atlas)
│   └── dicionarios/             # dicionário de dados v0.1 a v0.4
├── data/
│   ├── raw/                     # saída da Tarefa 1 (json/ + ping_bruto.csv + metadados)
│   ├── interim/                 # tabela de trabalho e auditoria de fluxos
│   └── processed/               # baseline_por_fluxo.csv, dataset_rotulado_B.csv, corte_temporal.csv
├── reports/                     # qualidade da coleta, regras, erros e teste (t3_*, t4_*, t5_*)
└── Tarefas/                     # diários das Tarefas 1 a 5
    └── modelos_arvores/         # árvores salvas (.joblib) das Tarefas 3, 4 e 5
```

---

## Como executar

Requer Python 3.9 ou superior. Todos os comandos são dados **a partir da raiz do repositório**.

```bash
pip install -r requirements.txt

# Tarefa 1 — coleta bruta (acessa a API do RIPE Atlas, somente GET)
python src/coleta_bruta.py --base-dir .

# Tarefa 2 — baseline e rotulagem (usa só o bruto da Tarefa 1, sem rede)
python src/baseline_rotulagem.py --base-dir .

# Tarefa 3 — primeira árvore (usa só treino e validação)
python src/arvore_inicial.py --base-dir .

# Tarefa 4 — ajuste da árvore (validação; grava os parâmetros finais em config/config_arvore.json)
python src/ajuste_arvore.py --base-dir .

# Tarefa 5 — árvore final e teste único
python src/arvore_final.py --base-dir .
```

> **Por que `--base-dir .`?** Sem ele, cada script usa como raiz a própria pasta `src/` e não encontra `config/` e `data/`, que ficam na raiz do repositório.

Os scripts rodam em sequência: cada tarefa lê o que a anterior gravou. As árvores treinadas são gravadas em `models/` (criada na raiz ao rodar). No repositório, as árvores já geradas ficam em `Tarefas/modelos_arvores/`.

### Opções úteis

| Comando | Para que serve |
|---|---|
| `python src/coleta_bruta.py --base-dir . --so-tabela` | Refazer tabela e relatório a partir dos JSON, sem acessar a rede |
| `python src/coleta_bruta.py --base-dir . --forcar-recoleta` | Baixar os JSON de novo (só se for intencional) |
| `python src/baseline_rotulagem.py --base-dir . --recalcular-baseline` | Regravar o baseline congelado (só se o bruto foi versionado de propósito) |
| `python src/arvore_final.py --base-dir . --repetir` | Medir o teste de novo. Por padrão o script se recusa, e a medição fica registrada em `reports/t5_teste_unico.json` |
| `python src/<script>.py --base-dir /outra/pasta` | Usar outra pasta como raiz do projeto |

A coleta é idempotente: se o JSON de um par e período já existe, ele não é baixado de novo. Rodar a Tarefa 1 duas vezes não duplica nem altera dados.

### Salvar no Google Drive (Google Colab)
Com `--drive`, o script monta o Drive, **cria a pasta se ela não existir** (com `data/raw`, `data/interim`, `data/processed`, `reports` e `models`) e, se já existir, só grava nela. Sem nome, a pasta é `Meu Drive/netvision`.

```python
!python src/coleta_bruta.py --drive              # Meu Drive/netvision
!python src/coleta_bruta.py --drive projeto_g15  # Meu Drive/projeto_g15
```

Use a mesma pasta em todas as tarefas. Como a Tarefa 1 baixa da API se a pasta não tiver `data/raw/json`, copie essa pasta para o Drive antes se não quiser coletar de novo.

---

## Documentação
- [RFC — problema, regra de rótulo, avaliação e riscos](src/RFC_Preditor_Degradacao_Rede.md)
- [Memorando de decisão — fonte de dados](src/memorando_de_decisao_grupo15.md)
- Dicionários de dados: [v0.1 (variáveis brutas)](src/dicionarios/dicionario_v0.1.md), [v0.2 (ficha, métricas, classe, colunas proibidas)](src/dicionarios/dicionario_v0.2.md), [v0.3 (coluna testada na Tarefa 4)](src/dicionarios/dicionario_v0.3.md) e [v0.4 (árvore final)](src/dicionarios/dicionario_v0.4.md)
- Diários: [Tarefa 1](Tarefas/Tarefa1_Coleta_Bruta.md), [Tarefa 2](Tarefas/Tarefa2_Baseline_e_Rotulagem.md), [Tarefa 3](Tarefas/Tarefa3_Arvore_Inicial.md), [Tarefa 4](Tarefas/Tarefa4_Ajuste_da_Arvore.md) e [Tarefa 5](Tarefas/Tarefa5_Arvore_Final.md)

---

## Links para a Mostra

- **Link do artigo (página web):** https://netvisionpreditordefalhas.app/
- **Link do vídeo pitch do Youtube:** https://www.youtube.com/watch?v=_4TjYdOS5so

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

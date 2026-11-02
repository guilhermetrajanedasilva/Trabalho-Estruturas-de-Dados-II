# Diário da Tarefa 1 — Problema e coleta bruta (sem rótulo)

**Período:** 17/08/2026 a 17/09/2026  
**Projeto:** Preditor de degradação de rede com RTT normalizado (independente da rota)  
**Modelo desta disciplina:** árvore de decisão. Nesta tarefa não se treina árvore.

**Equipe:**  NetVision - Visualização e análise de dados de rede

**Integrantes:**  Mariana Moreira Barbosa, Samara Fernandes Soares, Leandro do Nascimento Lemes, Guilherme Trajane da Silva, Vitor Julião Diogo dos Santos

**Scrum Master da tarefa:**  Mariana Moreira Barbosa

**Repositório GitHub:**  https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II

> Esta tarefa entrega o problema e o **dado cru**. Não há classe OK, RISCO ou FALHA. Não há baseline, não há mediana e não há árvore. Quem rotular aqui mistura a coleta com a decisão da Tarefa 2.
>
> A rota entra na coleta só para haver caminhos curtos e longos no mesmo arquivo. RTT alto **não** é falha. País, IP e nome da rota **não** serão coluna da árvore.

### Contrato desta tarefa

| | Artefato | Quem usa depois |
|---|---|---|
| **Entra** | RFC do projeto | — |
| **Sai** | RFC preenchido pelo grupo (problema, horizonte, custo de errar FALHA, fora de escopo) | Tarefas 2 e 5 |
| **Sai** | Dicionário v0.1 só com colunas **brutas** da medição | Tarefa 2 |
| **Sai** | `data/raw/` + `config/` + `requirements.txt` | Tarefa 2 **é obrigada a usar este bruto** |
| **Sai** | Este diário | Tarefas seguintes |

**Não sai daqui:** baseline, rótulo, `z_robusto`, split, árvore, métrica de modelo.

---

## 1. Definição do problema

Responder no diário. A resposta tem de bater com o RFC.

| Pergunta | Resposta do grupo |
|---|---|
| Qual evento a árvore vai classificar? | Degradação do fluxo em relação ao **próprio** normal: OK, RISCO ou FALHA. Não é “rota longa” nem “RTT acima de 100 ms”. |
| O que é um fluxo? | `fluxo_id = probe_id \| dst_addr` (origem, destino e, se existir, `measurement_id`). |
| O que é cada linha do bruto? | Uma medição ICMP desse fluxo, com timestamp. Ainda **sem** classe. |
| Qual horizonte fica para depois? | Detector: estado da medição atual. Preditor: estado 12 minutos à frente. A árvore só entra na Tarefa 3. |
| Quem usa o alerta? | Quem opera o enlace: investigar (FALHA), observar (RISCO) ou não agir (OK). |
| O que está proibido como definição de falha? | Limiar global de RTT, país, continente ou nome da rota. |

- [x] RFC do grupo preenchido a partir desta tabela
- [x] Dicionário v0.1 só com variáveis brutas

## 2. O que coletar (e o que não criar)

Fonte: medições públicas já existentes de ping IPv4 (mesh de Anchors do RIPE Atlas, somente `GET`). Não criar medição própria e não gastar crédito.

Cada registro bruto guarda, quando a API trouxer:

| Campo | Unidade | Papel agora |
|---|---|---|
| `timestamp` | UTC | Ordenar o fluxo |
| `measurement_id` | — | Identidade da medição mesh de cada par (8 IDs, gravados em `config/config_coleta.json`) |
| `probe_id` | — | Origem(ID da sonda RIPE Atlas) |
| `dst_addr` | — | Destino (IPv4 da anchor do par; 8 destinos distintos) |
| `fluxo_id` | texto estável | `probe_id\|dst_addr` |
| RTT da rajada (médio; mín/máx se existirem) | ms | Medição. Vazio se não houver resposta. **Nunca 0** |
| enviados, recebidos | contagem | Quantidade de pacotes ICMP enviados e recebidos |
| `perda_pct` | % | `(enviados − recebidos) / enviados × 100` |
| `jitter_ms` | ms | Desvio-padrão dos RTT da rajada **somente** com 2 ou mais respostas. Senão, vazio. **Nunca 0 fingindo estabilidade** |
| `timeout_atual` | 0 ou 1 | 1 se não há RTT ou perda = 100% |
| país ou rota | texto | Só auditoria de diversidade. **Fora da futura árvore** |

Regras da coleta:

- [X] Vários fluxos, com pelo menos um caminho curto e um caminho longo no mesmo período
- [X] A diversidade geográfica está documentada e **não** virou classe
- [X] Dois blocos de tempo contíguos, sem amostra nos dois: Período A (só para o baseline da Tarefa 2) e Período B (medições que serão rotuladas). Referência do projeto: 7 dias + 7 dias a partir de 06/09/2026 04:32 UTC. Outro recorte só vale se os dois blocos continuarem sem sobreposição e o A tiver volume para o mínimo da Tarefa 2
- [X] Timeout permanece no arquivo
- [X] JSON bruto preservado; a tabela tratada não apaga o bruto
- [X] Parâmetros (período, probes, destinos) em `config/`, não espalhados no código
- [X] HTTP com timeout, releitura em erro transitório e coleta idempotente (rodar de novo não duplica)
- [X] `requirements.txt` da coleta

**Evidências (notebook, commit, trecho do config):**

- Script de coleta: `coleta_bruta.py` (repositório: https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II). Ele valida os pares, descobre o `measurement_id` de cada par pela API, baixa o JSON em blocos de 24 h e gera a tabela bruta e o relatório de qualidade.
- Pares: dos 10 pares formados, 8 ficaram na coleta. As sondas 7457 (Camaçari → 185.34.2.114) e 7682 (Mississauga → 92.60.13.86) vieram com JSON vazio na medição mesh, nos dois períodos, e foram retirados. Os pares foram renumerados de 1 a 8.
- Versão anterior (histórico): notebook `2_Coleta_de_dados.ipynb`, que usava a medição 1001 e foi substituído pelo script. Commits: https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/commits/principal/2_Coleta_de_dados.ipynb
- Trecho de `config/config_coleta.json` (períodos e um dos pares; os parâmetros não ficam no código):
  ```json
  {
    "api_base": "https://atlas.ripe.net/api/v2",
    "periodo_a": {"inicio_utc": "2026-09-06T04:32:00Z", "fim_utc": "2026-09-13T04:32:00Z"},
    "periodo_b": {"inicio_utc": "2026-09-13T04:32:00Z", "fim_utc": "2026-09-20T04:32:00Z"},
    "http": {"timeout_s": 60, "max_tentativas": 5, "espera_base_s": 2, "tamanho_bloco_horas": 24},
    "pares": [
      {"par_id": 1, "probe_id": 7586, "probe_cidade": "Cochabamba", "probe_pais": "BO",
        "anchor_id": 2825, "dst_addr": "80.77.4.60", "anchor_cidade": "Dubai", "anchor_pais": "AE",
        "measurement_id": 34466562}
    ]
  }
  ```
- Trecho da requisição (somente `GET`, com timeout e releitura em erro transitório; o filtro por sonda é `probe_ids`):
  ```python
  dados = http_get_json(cfg, f"{cfg['api_base']}/measurements/{par['measurement_id']}/results/",
                        {"start": t, "stop": stop, "probe_ids": par["probe_id"], "format": "json"})
  ```
- Coleta idempotente: se `data/raw/json/m{measurement_id}_probe{probe_id}_periodo{A|B}.json` já existe, o script não baixa de novo e nunca sobrescreve o JSON. Rodar duas vezes não duplica nem altera dados.

## 3. Relatório de qualidade — ainda sem classe

- [x] Registros por `fluxo_id`
- [x] Início e fim de cada fluxo
- [x] Campos ausentes (RTT vazio é ausência, não zero)
- [x] Duplicatas
- [x] Quantidade de timeouts
- [x] RTT e perda descritos (mínimo, mediana, máximo) **sem** dizer OK, RISCO ou FALHA

**N° bruto:** 39.677 registros (19.547 no Período A e 20.130 no Período B), sem duplicatas

**N° de fluxos:** 8 fluxos `probe → anchor` (de 10 pares formados; 2 retirados por não terem dado)

**Qualidade geral (sem classe):** 88 timeouts preservados no arquivo; RTT ausente em 88 medições (vazio, nunca 0); jitter ausente em 188 (rajadas com menos de 2 respostas); nenhuma linha fora da janela do próprio período; Período A e Período B sem sobreposição; SHA-256 de cada JSON bruto registrado em `data/raw/metadados_coleta.json`.

**Por fluxo (relatório de qualidade):**

| par | Fluxo | Rota | Registros | A | B | Início (UTC) | Fim (UTC) | RTT ausente | Timeouts | RTT mín / mediana / máx (ms) | Perda mín / mediana / máx (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 7586\|80.77.4.60 | Cochabamba (BO) → Dubai (AE) | 5.037 | 2.518 | 2.519 | 06/09 04:33 | 20/09 04:29 | 0 | 0 | 336,7 / 374,4 / 484,5 | 0 / 0 / 66,7 |
| 2 | 6891\|63.222.248.5 | Belo Horizonte (BR) → Dubai (AE) | 5.034 | 2.518 | 2.516 | 06/09 04:35 | 20/09 04:31 | 1 | 1 | 349,4 / 368,0 / 446,3 | 0 / 0 / 100 |
| 3 | 7307\|37.252.245.94 | Feira de Santana (BR) → Dubai (AE) | 4.990 | 2.475 | 2.515 | 06/09 04:34 | 20/09 04:30 | 66 | 66 | 306,1 / 346,0 / 709,8 | 0 / 0 / 100 |
| 4 | 7508\|94.199.170.201 | Osasco (BR) → Feldkirch (AT) | 5.019 | 2.506 | 2.513 | 06/09 04:32 | 20/09 04:28 | 7 | 7 | 198,7 / 199,3 / 279,3 | 0 / 0 / 100 |
| 5 | 6878\|143.205.170.32 | Minsk (BY) → Klagenfurt (AT) | 4.490 | 1.970 | 2.520 | 06/09 04:33 | 20/09 04:29 | 0 | 0 | 25,8 / 26,0 / 46,7 | 0 / 0 / 0 |
| 6 | 6719\|203.41.0.51 | Beauharnois (CA) → Melbourne (AU) | 5.036 | 2.520 | 2.516 | 06/09 04:34 | 20/09 04:31 | 2 | 2 | 225,8 / 228,6 / 666,7 | 0 / 0 / 100 |
| 7 | 7258\|202.87.175.244 | Richterswil (CH) → Perth (AU) | 5.036 | 2.520 | 2.516 | 06/09 04:34 | 20/09 04:30 | 8 | 8 | 268,8 / 342,0 / 462,9 | 0 / 0 / 100 |
| 8 | 7656\|103.153.238.101 | Satigny (CH) → Sydney (AU) | 5.035 | 2.520 | 2.515 | 06/09 04:34 | 20/09 04:30 | 4 | 4 | 292,5 / 299,7 / 838,0 | 0 / 0 / 100 |

O fluxo de Minsk tem menos registros no Período A (1.970) porque a medição tem lacunas nesse período; ele ainda passa do piso de 1.500 da Tarefa 2.

**Caminho curto e caminho longo presentes (quais):** Caminho curto: Minsk (BY) → Klagenfurt (AT), mediana de ~26 ms. Caminhos longos (mediana entre 199 e 374 ms): Osasco → Feldkirch (~199 ms), Beauharnois → Melbourne (~229 ms), Satigny → Sydney (~300 ms), Richterswil → Perth (~342 ms), Feira de Santana → Dubai (~346 ms), Belo Horizonte → Dubai (~368 ms) e Cochabamba → Dubai (~374 ms). A diversidade geográfica (BO→AE, BR→AE, BR→AT, BY→AT, CA→AU, CH→AU) está só na auditoria e não virou classe. Há um único caminho curto.

## 4. Scrum

- [x] Product Owner = docente; Scrum Master da tarefa; time de desenvolvimento
- [x] Board com To do / Doing / Done
- [x] Pelo menos 3 histórias: coletar fluxos diversos; preservar o bruto com timeout; separar Período A e Período B sem rotular

**Histórias:**  
1. Coletar fluxos diversos (com caminhos curtos e longos no mesmo período)
2. Preservar o dado bruto com tratamento correto de timeout 
3. Separar Período A e Período B sem rotular

**Link do board:** 
https://github.com/users/Leandro-Nas-Lemes/projects/1/views/1

## 5. Diário de bordo

| Integrante | O que fiz nesta tarefa | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| **Mariana Moreira Barbosa** | Realizou a documentação inicial da Tarefa 1, participou da definição do problema, dos critérios da coleta e dos ajustes e inclusão de evidências. | Ajustes na documentação e organização das evidências da coleta. | Manter a organização das evidências e ajustar a documentação conforme as próximas etapas. |
| **Samara Fernandes Soares** | Definiu e configurou parâmetros da coleta, participou da execução da consulta à API RIPE Atlas e documentou atividades e evidências. | Organização dos parâmetros e registro das evidências da coleta. | Manter os parâmetros documentados e as evidências associadas às atividades. |
| **Leandro do Nascimento Lemes** | Realizou a transformação dos dados JSON para DataFrame e registrou a atividade e suas evidências no notebook. | Inspeção e organização dos dados coletados para verificar sua estrutura. | Manter o registro das etapas de transformação e verificação dos dados. | 
| **Guilherme Trajane da Silva** | Realizou atualizações no notebook de coleta e participou do registro das informações do projeto. | Os commits analisados não permitem determinar com segurança uma história específica associada à sua atuação. | Manter o registro das alterações realizadas e melhorar a identificação das atividades nos próximos registros. | 
| **Vitor Julião Diogo dos Santos** | Atualizou parâmetros e critérios da coleta e participou do relatório de qualidade, incluindo métricas e detalhes dos dados coletados. | Organização e registro das métricas e critérios de qualidade. | Manter o acompanhamento das métricas e documentar os critérios de qualidade. |

## 6. Evidências gerais

- Link do RFC:  https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/blob/principal/doc/RFC_Preditor_Degradacao_Rede.md
- Link do dicionário v0.1: https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/blob/principal/doc/dicionario_v0.1.md
- Link dos commits: https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/commits/principal/Tarefas/Tarefa1_Coleta_Bruta.md  
- Link de `data/raw/` e do `config/`: https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/tree/principal/data/raw /  https://github.com/guilhermetrajanedasilva/Trabalho-Estruturas-de-Dados-II/tree/principal/config

---

## Rubrica — Tarefa 1 (0 a 4,0)

| Critério | Peso | Nota máxima | Nota | Observações |
|---|---|---|---|---|
| Problema | 0,5 | Fluxo, unidade de análise e proibição de RTT absoluto como falha estão explícitos | | |
| Coleta bruta | 1,5 | Vários fluxos (curto e longo), timeout preservado, RTT vazio ≠ 0, config externa, bruto intocável | | |
| Período A e Período B sem rótulo | 1,0 | Dois blocos sem sobreposição; relatório de qualidade **sem** classe | | |
| Scrum + diário | 1,0 | Papéis, board, histórias e diário de todos | | |
| **Total** | **4,0** | | **___ / 4,0** | |

# Memorando de Decisão — Fonte de Dados do Projeto


| Campo | Informação |
|---|---|
| Curso / Disciplina | `[Estrutura de Dados II]` |
| Projeto integrador | `[]` |
| Orientador(a) | `[Andrea Ono Sakai]` |
| Data de entrega desta etapa | `[08/09/2026]` |
| Integrantes do grupo | `[Mariana Moreira Barbosa]` `[Samara Fernandes Soares]` `[Leandro do Nascimento Lemes]` `[Guilherme Trajane da Silva]` `[Vitor Juliao Diogo dos Santos]`|

---

> Preencha cada seção com o que você encontrou na pesquisa. Não deixe nenhum campo com o texto entre colchetes — substitua pelo seu conteúdo. Toda informação levantada nas Opções A e B precisa indicar a fonte de onde veio.

## 1. Situação

<!-- Em uma frase: qual decisão precisa ser tomada e por quê. 
O pipeline do projeto já está definido: qualquer fonte de dados precisa produzir registros que se transformem em janelas e, por fim, em X = [latência, perda, jitter]. Falta decidir de onde virão esses dados na próxima fase. A equipe do projeto precisa recomendar, com base em pesquisa e não em preferência pessoal, se a próxima etapa deve usar um dataset real já publicado ou a API do RIPE Atlas. O grupo deve produzir um memorando de decisão com a recomendação da tomada de decisão. A recomendação só tem valor se for sustentada por pesquisa real — não existe resposta pronta para copiar; ela precisa ser construída a partir do que vocês encontraram.
-->

[Escreva aqui uma frase, qual decisão precisa ser tomada e por quê]

## 2. Opção A — Dataset real

<!-- O que foi encontrado sobre um dataset real de ICMP. Cite a fonte de cada informação. -->

- **Origem / link:** Dataset of RTT latency internet measurements in Europe, Disponibilizado no Zenodo, plataforma de compartilhamento e preservasação de dados científicos: - https://zenodo.org/records/15944458. - O dataset contém medições reais de Roud-Trin Time (RTT) obtidas por meio das requisições utilizadas como pontos de monitoramento distribuídos em diferentes regiões da Europa. Sendo assim, a origem dos dados é baseada em medições reais de rede e não dm dados simulados ou gerados artificialmente.

- **Formato:** O dataset disponibiliza os dados em arquivos para download no Zenodo. A página do dataset apresenta os arquivos e os dados das medições de RTT obtidas por ICMP.

- **Período coberto:** As medições foram realizadas de 27 de novembro de 2024 a 30 de janeiro de 2025.

- **Campos disponíveis:** Os dados são voltados para medições de RTT obtidas por ICMP, associadas aos nós de monitoramento e aos endereços IP de destino. O dataset foi organizado para representar medições de latência realizadas a partir de diferentes locallizações geográficas.

- **Licença de uso:** A licença deve ser consultada na seção de informações, licenciamento do regitro do Zenodo Antes de redistribuição dos dados. Para utilização acadêmica, deve-se também seguir a forma de citação indicada pelos autores na página do dataset.

**Resumo do que foi encontrado:**

Foi encontrado no Zenodo um dataset real que conteve medições de RTT realizadas por meio de requisições ICMP Echo. Essas medições foram coletadas entre 27/11/2024 e 30/01/2025, utilizado seis máquinas virtuais como pontos de monitoramento distribuídos nas cidades de Madrid, Dublin, Frankfurt,Varsóvia, Gävle e Milão. O objetivo do dataset é disponibilizar medições reais de latência de rede para análises, incluindo os estudos de desempenho e localição de endereços IP. Sendo assim, o dataset é relevante para o projeto porque fornece dados reais obtidos por ICMP e pode ser utilizado como fonte para analizar a latência da comunicação entre diferentes pontos da rede e apoiar estudos relacionados ao desempenho de redes.

## 3. Opção B — API do RIPE Atlas

<!-- O que foi encontrado sobre a API: autenticação, criação e consulta de medições. Cite a fonte de cada informação. -->

- **Documentação consultada (link):** [ ]
- **Autenticação exigida:** [ ]
- **Como se cria uma medição:** [ ]
- **Como se consultam os resultados:** [ ]

**Resumo do que foi encontrado:**

[Escreva aqui, citando a fonte consultada]

## 4. Comparação

<!-- Preencha a tabela com base no que você levantou nas seções 2 e 3. -->

| Critério | Opção A — Dataset real | Opção B — API RIPE Atlas |
|---|---|---|
| Controle sobre a coleta | | |
| Diversidade geográfica | | |
| Custo / complexidade de implementação | | |
| Tempo até os primeiros dados estarem disponíveis | | |

## 5. Recomendação

<!-- Uma frase direta: qual opção você recomenda. -->

[Escreva aqui]

## 6. Justificativa

<!-- Por que essa opção vence a outra, com base nas evidências das seções 2, 3 e 4 — não em preferência pessoal. -->

[Escreva aqui]

## 7. Riscos e limitações

<!-- O que pode dar errado com a opção escolhida, e como isso poderia ser mitigado. -->

[Escreva aqui]

## 8. Contribuição Individual dos Integrantes

<!-- cada integrante deve descrever, com suas próprias palavras, o que efetivamente fez nesta etapa. Contribuições genéricas como "ajudei em tudo" não serão aceitas. Use verbos de ação e seja específico (ex.: "pesquisei , analisei, testei, ... apresentei prós/contras ao grupo, ...").-->

### Integrante 1 — `[Escreva nome completo do aluno ]`
- **O que fez nesta etapa:** `[]`
- **Tempo dedicado (aprox.):** `[ex.: 3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
`[]` 
`[]`

### Integrante 2 — `Samara Fernandes Soares`
- **O que fez nesta etapa:** `[]`
- **Tempo dedicado (aprox.):** `[ex.: 3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
`[]` 
`[]`

### Integrante 3 — `[Escreva nome completo do aluno ]`
- **O que fez nesta etapa:** `[]`
- **Tempo dedicado (aprox.):** `[ex.: 3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[]` 
`[]`

### Integrante 4 — `[Escreva nome completo do aluno ]`
- **O que fez nesta etapa:** `[]`
- **Tempo dedicado (aprox.):** `[ex.: 3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[]` 
`[]`

### Integrante 5 — `[Escreva nome completo do aluno ]`
- **O que fez nesta etapa:** `[]`
- **Tempo dedicado (aprox.):** `[ex.: 3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[]` 
`[]`

### Integrante 6 — `[Escreva nome completo do aluno ]`
- **O que fez nesta etapa:** `[]`
- **Tempo dedicado (aprox.):** `[ex.: 3h30]`
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
`[]` 
`[]`

---

## Fontes consultadas

<!-- Mínimo de 3 fontes. Liste todas as páginas de documentação, artigos ou repositórios usados. -->

1. https://zenodo.org/records/15944458
2. [ ]
3. [ ]

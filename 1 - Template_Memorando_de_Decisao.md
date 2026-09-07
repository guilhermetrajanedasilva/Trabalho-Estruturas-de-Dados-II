# Memorando de Decisão — Fonte de Dados do Projeto


| Campo | Informação |
|---|---|
| Curso / Disciplina | `Estrutura de Dados II` |
| Projeto integrador | `` |
| Orientador(a) | `Andrea Ono Sakai` |
| Data de entrega desta etapa | `08/09/2026` |
| Integrantes do grupo | `Mariana Moreira Barbosa`, `Samara Fernandes Soares`, `Leandro do Nascimento Lemes`, `Guilherme Trajane da Silva`, `Vitor Juliao Diogo dos Santos`|

---

> Preencha cada seção com o que você encontrou na pesquisa. Não deixe nenhum campo com o texto entre colchetes — substitua pelo seu conteúdo. Toda informação levantada nas Opções A e B precisa indicar a fonte de onde veio.

## 1. Situação

<!-- Em uma frase: qual decisão precisa ser tomada e por quê. 
O pipeline do projeto já está definido: qualquer fonte de dados precisa produzir registros que se transformem em janelas e, por fim, em X = [latência, perda, jitter]. Falta decidir de onde virão esses dados na próxima fase. A equipe do projeto precisa recomendar, com base em pesquisa e não em preferência pessoal, se a próxima etapa deve usar um dataset real já publicado ou a API do RIPE Atlas. O grupo deve produzir um memorando de decisão com a recomendação da tomada de decisão. A recomendação só tem valor se for sustentada por pesquisa real — não existe resposta pronta para copiar; ela precisa ser construída a partir do que vocês encontraram.
-->

A equipe recomenda a utilização da API do RIPE Atlas como fonte de dados, pois seus resultados de medições podem fornecer informações necessárias para a geração dos registros que serão posteriormente transformados em métricas de latência, perda e jitter. Além disso, a API permite consultar resultados por período e por probe, facilitando a coleta e o processamento dos dados.

## 2. Opção A — Dataset real

<!-- O que foi encontrado sobre um dataset real de ICMP. Cite a fonte de cada informação. -->

- **Origem / link:** Dataset of RTT latency internet measurements in Europe, Disponibilizado no Zenodo, plataforma de compartilhamento e preservação de dados científicos, fonte: [Zenodo - Dataset of RTT latency internet measurements in Europe](https://zenodo.org/records/15944458). O dataset contém medições reais de Roud-Trip Time (RTT) obtidas por meio das requisições utilizadas como pontos de monitoramento distribuídos em diferentes regiões da Europa. Sendo assim, a origem dos dados é baseada em medições reais de rede e não de dados simulados ou gerados artificialmente.

- **Formato:** O dataset disponibiliza os dados em arquivos estruturados como CSV/JASON para download diretamente no Zenodo, podendo estar organizados em arquivos compactados. A página do registro apresenta os arquivos individuais, mostrando as medições de RTT e tempos de resposta das requisições ICMP. https://zenodo.org/records/15944458.
  
- **Período coberto:** As medições foram realizadas de 27 de novembro de 2024 a 30 de janeiro de 2025. https://zenodo.org/records/15944458.

- **Campos disponíveis:** Os dados são voltados para medições de RTT obtidas por ICMP, associadas aos nós de monitoramento e aos endereços IP de destino. O dataset foi organizado para representar medições de latência realizadas a partir de diferentes localizações geográficas. https://zenodo.org/records/15944458.
  
- **Licença de uso:** O dataset está disponibilizado sob licença Creative Commons Attribution 4.0 Internacional (CC BY 4.0).Essa licença vai permitir o uso, compartilhamento e adaptação dos dados, desde que seja dada a devida atribuição aos autores do dataset. Para utilização Acadêmica, deve-se realizar a citação da fonte conforme as informações disponibilizadas no registro do Zenodo. https://zenodo.org/records/15944458.
  
**Resumo do que foi encontrado:**
Foi encontrado no Zenodo um dataset real que conteve medições de RTT realizadas por meio de requisições ICMP Echo. Essas medições foram coletadas entre 27/11/2024 e 30/01/2025, utilizado seis máquinas virtuais como pontos de monitoramento distribuídos nas cidades de Madrid, Dublin, Frankfurt,Varsóvia, Gävle e Milão. O objetivo do dataset é disponibilizar medições reais de latência de rede para análises, incluindo os estudos de desempenho e localização de endereços IP. Sendo assim, o dataset é relevante para o projeto porque fornece dados reais obtidos por ICMP e pode ser utilizado como fonte para analisar a latência da comunicação entre diferentes pontos da rede e apoiar estudos relacionados ao desempenho de redes.

## 3. Opção B — API do RIPE Atlas

<!-- O que foi encontrado sobre a API: autenticação, criação e consulta de medições. Cite a fonte de cada informação. -->

- **Documentação consultada (link):** RIPE Atlas Docs - (https://atlas.ripe.net/docs/getting-started/what-is-ripe-atlas).`
- **Autenticação exigida:** `Uso de chave de API (API Key) gerada na plataforma RIPE Atlas. É necessária para criar e gerenciar medições customizadas, enviada via cabeçalho de requisição HTTP. (https://atlas.ripe.net/docs/apis/).
- **Como se cria uma medição:** Pode ser criada pela interface web do RIPE Atlas, escolhendo o tipo de teste (ex.: ICMP ping), o alvo e a quantidade de sondas (probes), ou enviando uma requisição HTTP POST para o endpoint /api/v2/measurements/ com um payload JSON contendo essas configurações e consumindo créditos da conta. (https://atlas.ripe.net/docs/apis/rest-api-manual/measurements/creating-measurements/#what-s-next)
- **Como se consultam os resultados:** Envio de uma requisição HTTP GET para o endpoint (https://atlas.ripe.net/api/v2/measurements/)(https://atlas.ripe.net/api/v2/measurements/)<id_da_medicao>/results/, retornando a lista de respostas e métricas de desempenho em formato JSON.

**Resumo do que foi encontrado:**

Conforme a documentação oficial da RIPE NCC, a API REST v2 do RIPE Atlas permite interagir programaticamente com uma rede global de milhares de sondas físicas e ancoras para realizar medições de rede em tempo real, incluindo testes com o protocolo ICMP (ping e traceroute). A criação de novas medições exige uma conta ativa na plataforma e o uso de uma chave de API autenticada via cabeçalho HTTP, consumindo créditos virtuais (credits) do usuário. A consulta dos resultados pode ser realizada por chamada REST direta em formato JSON utilizando o ID retornado na criação da medição, ou via integração com a biblioteca oficial em Python (ripe.atlas.courier / ripe.atlas.sagan).

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
- **O que fez nesta etapa:** : Pesquisei e analisei um dataset real de medições de RTT (o tempo necessário para que um pacote de dados vá da origem ao destino e retorne), obtidas por requisições ICMP, disponibilizado no Zenodo. Verifiquei informações sobre a origem dos dados, período de coleta, formato e campos disponíveis no dataset.
  
- **Tempo dedicado (aprox.):** 4h30
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
  
 print dos commits do desenvolvimento que fiz do projeto como evidência ⬇️
 
 <img width="1035" height="862" alt="image" src="https://github.com/user-attachments/assets/9ac0161c-9cc9-42dd-a6ca-650bb5e623b8" />


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
2. https://atlas.ripe.net/docs/getting-started/what-is-ripe-atlas
3. [ ]

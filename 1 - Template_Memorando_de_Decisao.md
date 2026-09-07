# Memorando de Decisão — Fonte de Dados do Projeto


| Campo | Informação |
|---|---|
| Curso / Disciplina | Estrutura de Dados II |
| Projeto integrador |  |
| Orientador(a) | Andrea Ono Sakai |
| Data de entrega desta etapa | 08/09/2026 |
| Integrantes do grupo | Mariana Moreira Barbosa, Samara Fernandes Soares, Leandro do Nascimento Lemes, Guilherme Trajane da Silva, Vitor Julião Diogo dos Santos|

---

> Preencha cada seção com o que você encontrou na pesquisa. Não deixe nenhum campo com o texto entre colchetes — substitua pelo seu conteúdo. Toda informação levantada nas Opções A e B precisa indicar a fonte de onde veio.

## 1. Situação

<!-- Em uma frase: qual decisão precisa ser tomada e por quê. 
O pipeline do projeto já está definido: qualquer fonte de dados precisa produzir registros que se transformem em janelas e, por fim, em X = [latência, perda, jitter]. Falta decidir de onde virão esses dados na próxima fase. A equipe do projeto precisa recomendar, com base em pesquisa e não em preferência pessoal, se a próxima etapa deve usar um dataset real já publicado ou a API do RIPE Atlas. O grupo deve produzir um memorando de decisão com a recomendação da tomada de decisão. A recomendação só tem valor se for sustentada por pesquisa real — não existe resposta pronta para copiar; ela precisa ser construída a partir do que vocês encontraram.
-->

A equipe recomenda a utilização da API do RIPE Atlas como fonte de dados, pois seus resultados de medições podem fornecer informações necessárias para a geração dos registros que serão posteriormente transformados em métricas de latência, perda e jitter. Além disso, a API permite consultar resultados por período e por probe, facilitando a coleta e o processamento dos dados.

## 2. Opção A — Dataset real

<!-- O que foi encontrado sobre um dataset real de ICMP. Cite a fonte de cada informação. -->

- **Origem / link:** Dataset of RTT latency internet measurements in Europe, Disponibilizado no Zenodo, plataforma de compartilhamento e preservação de dados científicos, fonte: [Zenodo - Dataset of RTT latency internet measurements in Europe](https://zenodo.org/records/15944458). O dataset contém medições reais de Round-Trip Time (RTT) obtidas por meio das requisições utilizadas como pontos de monitoramento distribuídos em diferentes regiões da Europa. Sendo assim, a origem dos dados é baseada em medições reais de rede e não de dados simulados ou gerados artificialmente.

- **Formato:** O dataset disponibiliza os dados em arquivos estruturados como CSV/JSON para download diretamente no Zenodo, podendo estar organizados em arquivos compactados. A página do registro apresenta os arquivos individuais, mostrando as medições de RTT e tempos de resposta das requisições ICMP. https://zenodo.org/records/15944458.
  
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
| Controle sobre a coleta |O controle é baixo pois os dados já foram coletados anteriormente, entre novembro de 2024 e Janeiro de 2025 limitando os dados a esse período apenas | O controle é alto pois permite criar medições personalizadas |
| Diversidade geográfica | Limitada pois um dataset  real ultiliza pontos de monitoramento, como no caso analisado em que utiliza apenas 6 pontos espalhados pela Europa | Alta, pois a API geradas pela plataforma RIPE Atlas cobrem uma área de rede mundial |
| Custo / complexidade de implementação | Baixo custo e complexidade, pois os dados já estão disponíveis para download | Maior complexidade, pois necessário utilizar a API, configurar autenticação com API Key, realizar requisições HTTP e, para criar medições próprias, utilizar créditos da plataforma. |
| Tempo até os primeiros dados estarem disponíveis | Imediato. Os dados já foram coletados e publicados no Zenodo, podendo ser baixados e utilizados imediatamente. | Variável. É necessário configurar ou localizar uma medição, realizar as requisições à API e, no caso de uma nova medição, aguardar a coleta dos resultados pelas probes. |

## 5. Recomendação

<!-- Uma frase direta: qual opção você recomenda. -->

Recomendamos a utilização da API do RIPE Atlas pois com ela é possível ter um controle maior em relação aos dados de coleta uma vez que você pode decidir o/os locais no qual você quer analisar os dados além de maior precisão nas datas também.

## 6. Justificativa

<!-- Por que essa opção vence a outra, com base nas evidências das seções 2, 3 e 4 — não em preferência pessoal. -->

RIPE Atlas se mostra mais adequada que o dataset analisado porque oferece maior controle sobre a coleta, maior diversidade e possibilidade de escolher periodos para as medições. Por outro lado, o dataset possui dados ja definidos e limitados a seis pontos de monitoramento, tornando a API uma opção mais flexível para as análises do projeto.

## 7. Riscos e limitações

<!-- O que pode dar errado com a opção escolhida, e como isso poderia ser mitigado. -->

A utilização da API do RIPE Atlas apresenta como um dos principais riscos e limitações a necessidade de autenticação por API Key e, para a criação de novas medições, o consumo de créditos da plataforma, o que pode limitar a quantidade de medições realizadas. Além disso, a utilização da API exige conhecimentos sobre requisições HTTP, formato JSON e processamento dos resultados.

Outro risco está relacionado à disponibilidade e à quantidade de probes utilizadas nas medições, pois a cobertura dos dados pode variar conforme a localização escolhida e a disponibilidade das sondas. Também pode haver dificuldades durante a coleta ou processamento dos dados, como respostas incompletas ou necessidade de tratamento dos resultados antes de gerar as métricas de latência, perda e jitter.

Para reduzir esses riscos, a equipe poderá consultar a documentação oficial da API, realizar testes iniciais com poucas medições, verificar a disponibilidade das probes antes da coleta e implementar validações nos dados recebidos. Dessa forma, será possível identificar problemas antecipadamente e garantir maior confiabilidade nos dados utilizados pelo projeto.


## 8. Contribuição Individual dos Integrantes

<!-- cada integrante deve descrever, com suas próprias palavras, o que efetivamente fez nesta etapa. Contribuições genéricas como "ajudei em tudo" não serão aceitas. Use verbos de ação e seja específico (ex.: "pesquisei , analisei, testei, ... apresentei prós/contras ao grupo, ...").-->

### Integrante 1 — `Mariana Moreira Barbosa`
- **O que fez nesta etapa:** Pesquisei sobre a API do RIPE Atlas, e junto com a equipe do projeto, incluí as informações da Situação, onde será o caminho que iremos seguir, pesquisei sobre o funcionamento dessa API e suas ferramentas para nos ajudar nas próximas etapas.
- **Tempo dedicado (aprox.):** 5h30
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:

Evidências da contribuição do desenvolvimento: 

<img width="1367" height="745" alt="image" src="https://github.com/user-attachments/assets/bf1df9a0-88eb-4ce5-ab29-582141a57ce7" />

<img width="1065" height="792" alt="image" src="https://github.com/user-attachments/assets/09b58ad0-ea46-4831-86d5-f4c68fd25983" />


### Integrante 2 — `Samara Fernandes Soares`
- **O que fez nesta etapa:** : Pesquisei e analisei um dataset real de medições de RTT (o tempo necessário para que um pacote de dados vá da origem ao destino e retorne), obtidas por requisições ICMP, disponibilizado no Zenodo. Verifiquei informações sobre a origem dos dados, período de coleta, formato e campos disponíveis no dataset.
  
- **Tempo dedicado (aprox.):** 4h30
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
  
 print dos commits do desenvolvimento que fiz do projeto como evidência ⬇️
 
 <img width="1035" height="862" alt="image" src="https://github.com/user-attachments/assets/9ac0161c-9cc9-42dd-a6ca-650bb5e623b8" />


### Integrante 3 — `Vitor Julião Diogo dos Santos`
- **O que fez nesta etapa:** Analisei os dados apurados, com os dados fiz uma comparação ente as opções levantando assim a nossa recomendação de qual recomendamos e uma breve justificativa do porque uma vence a outra
- **Tempo dedicado (aprox.):** 2h
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*: 
<img width="722" height="277" alt="Captura de tela 2026-09-06 234619" src="https://github.com/user-attachments/assets/652ad416-89a0-4b57-b9a8-4e26173c31a3" />
`[]`

### Integrante 4 — `Leandro do Nascimento Lemes`
- **O que fez nesta etapa:** contribuição na comparação entre o dataset e a API do RIPE Atlas, elaboração da justificativa da decisão e revisão do conteúdo do memorando. 
- **Tempo dedicado (aprox.):** 34min
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:
<img width="1788" height="979" alt="Captura de Tela 2026-09-07 às 09 17 36" src="https://github.com/user-attachments/assets/27a5087a-7ce4-4506-8d24-82b1d9b1df15" />
`[]`

### Integrante 5 — `Guilherme Trajane da Silva`
- **O que fez nesta etapa:** Pesquisei sobre os principais riscos e limitações relacionados à utilização da API do RIPE Atlas como fonte de dados para o projeto. Levantei informações sobre possíveis dificuldades na utilização da API, como a necessidade de autenticação, o uso de créditos para determinadas medições e a complexidade de configuração e coleta dos dados. As informações pesquisadas foram utilizadas como base para o preenchimento da seção de riscos e limitações do memorando.
- **Tempo dedicado (aprox.):** 2h
- **Evidência da contribuição** *(print de conversa, rascunho, e-mail, documento compartilhado etc.)*:

- Pesquisa sobre os riscos e limitações da API do RIPE Atlas:

- <img width="953" height="240" alt="Screenshot 2026-09-07 17 00 37" src="https://github.com/user-attachments/assets/ceb227a9-edf0-4884-bc2f-3b039ab82133" />

- Contribuição para a seção “Riscos e limitações” do memorando:

- <img width="953" height="325" alt="Screenshot 2026-09-07 17 08 23" src="https://github.com/user-attachments/assets/cbafc2f2-78a5-4090-bbde-b9c0729eca40" />

## Fontes consultadas

<!-- Mínimo de 3 fontes. Liste todas as páginas de documentação, artigos ou repositórios usados. -->

1. https://zenodo.org/records/15944458
2. https://atlas.ripe.net/docs/getting-started/what-is-ripe-atlas
3. https://atlas.ripe.net/docs/apis/rest-api-manual/introduction
4. https://www.ripe.net/ripe/mail/archives/ripe-atlas/2023-January/005378.html
5. https://atlas.ripe.net/docs/apis/rest-api-manual/core-concepts/rate-limiting

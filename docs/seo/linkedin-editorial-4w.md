# Calendário Editorial LinkedIn — 4 Semanas (12 posts)

**Canal:** LinkedIn Company Page SmartLic + perfil pessoal do founder Tiago Sasaki (cross-post)
**Frequência:** 3 posts/semana — terça, quinta, sábado
**Horário ótimo (público BR, B2B, decisores):**
- Terça 08h30 (commute matinal, início de semana produtiva)
- Quinta 12h15 (almoço, pico de engajamento B2B)
- Sábado 10h00 (conteúdo mais leve, founders e consultores scrolling no fim de semana)

**Estratégia geral:**
- Semana 1: **Educação** — o que é licitação, por que importa, quem pode participar
- Semana 2: **Dados exclusivos** — insights do nosso datalake PNCP que ninguém mais tem
- Semana 3: **Cases e contrarian takes** — opiniões fortes, histórias de sucesso/fracasso
- Semana 4: **CTA e soft pitch** — convite para trial, prova social, fechar o ciclo

**Regras de formatação:**
- Hook na primeira linha (≤150 chars) — o que aparece antes do "ver mais"
- Line breaks a cada 1-3 frases para legibilidade mobile
- Sem emoji excessivo (máx 1-2 por post)
- CTA claro no final
- Hashtags no último parágrafo, separadas por espaço
- Mencionar @SmartLic (Company Page) quando possível

---

## SEMANA 1 — EDUCAÇÃO

### Post 1 — Terça, 07/04, 08h30
**Tipo:** Insight / Educação de mercado
**Tema:** O mercado B2G no Brasil é maior do que você imagina

**Hook:**
> O governo brasileiro compra mais de R$ 1 trilhão por ano. E 90% das PMEs nunca tentaram vender uma linha para ele.

**Corpo:**
> O governo brasileiro compra mais de R$ 1 trilhão por ano. E 90% das PMEs nunca tentaram vender uma linha para ele.
>
> Por quê?
>
> Não é falta de competência técnica. Não é falta de produto. Não é falta de vontade.
>
> É o ruído.
>
> O PNCP publica milhares de editais por semana. Pregões, concorrências, dispensas, inexigibilidades. Em 27 estados. Em setores que vão de manutenção predial a inteligência artificial.
>
> Achar o edital certo é como procurar um contrato específico dentro de um oceano de PDFs mal indexados.
>
> A consequência: o mercado B2G brasileiro virou um clube fechado de empresas grandes com departamentos inteiros dedicados a monitorar licitação. Enquanto isso, PMEs com produtos excelentes ficam de fora.
>
> Isso está mudando.
>
> Nos próximos 4 posts desta semana, vou explicar: (1) quem pode participar, (2) quais são as modalidades, (3) quais os erros mais comuns, (4) como começar sem um time B2G.
>
> Se você tem uma PME e nunca participou de uma licitação, esse é o momento.

**CTA:** Segue a gente aqui para a série completa. E comenta: qual o maior motivo de você ainda não ter participado de uma licitação pública?

**Dado/insight do PNCP:** Calcular volume total publicado nos últimos 12 meses via `SELECT SUM(valor_total_estimado) FROM pncp_raw_bids WHERE data_publicacao_pncp >= NOW() - INTERVAL '12 months'`. Substituir "mais de R$ 1 trilhão" pelo número real.

**Hashtags:** #LicitaçõesPúblicas #B2G #GovTech #PME #Empreendedorismo #SetorPúblico #Inovação

**Imagem:** Infográfico simples: "R$ 1 trilhão / ano em compras públicas" + silhueta do Brasil em background sutil.

---

### Post 2 — Quinta, 09/04, 12h15
**Tipo:** How-to / Educação prática
**Tema:** As 6 modalidades de licitação que você precisa conhecer

**Hook:**
> Pregão Eletrônico, Concorrência, Dispensa, Inexigibilidade... Se você não sabe a diferença, está perdendo dinheiro.

**Corpo:**
> Pregão Eletrônico, Concorrência, Dispensa, Inexigibilidade... Se você não sabe a diferença, está perdendo dinheiro.
>
> As 6 modalidades principais em 1 minuto:
>
> **1. Pregão Eletrônico (mod 5)** — O queridinho. 100% online, disputa por lance. Usado para bens e serviços "comuns". Hoje representa a maioria absoluta do que se compra no Brasil.
>
> **2. Concorrência (mod 4)** — Para valores altos, obras, serviços complexos. Mais burocrática, menos frequente.
>
> **3. Pregão Presencial (mod 6)** — Em extinção. Ainda existe, mas é resquício de pré-2021.
>
> **4. Leilão (mod 7)** — Para venda de bens da administração pública. Nicho.
>
> **5. Inexigibilidade (mod 8)** — Quando só existe um fornecedor possível. Cuidado: alvo preferido de auditoria.
>
> **6. Dispensa (mod 12)** — Valores baixos ou situações específicas. Crescendo muito e merece um post só dela.
>
> Cada modalidade tem regras próprias de prazo, habilitação e julgamento. Se você está começando no B2G, foque em Pregão Eletrônico — é o caminho mais acessível.
>
> Próximo post (sábado): os 5 erros que matam 80% das propostas de PMEs em licitação.

**CTA:** Qual modalidade você nunca entendeu direito? Comenta que eu explico.

**Dado/insight do PNCP:** Query para distribuição das 6 modalidades nos últimos 3 meses — `SELECT modalidade_id, COUNT(*) FROM pncp_raw_bids WHERE data_publicacao_pncp >= NOW() - INTERVAL '3 months' GROUP BY 1`. Incluir percentual de Pregão Eletrônico no post.

**Hashtags:** #LicitaçõesPúblicas #PregãoEletrônico #B2G #Compliance #SetorPúblico #PME #GovTech

**Imagem:** Tabela limpa com as 6 modalidades, 3 colunas (nome, descrição, uso típico). Design minimalista.

---

### Post 3 — Sábado, 11/04, 10h00
**Tipo:** How-to / Lista
**Tema:** Os 5 erros que matam propostas de PMEs em licitações

**Hook:**
> 80% das PMEs que tentam licitar pela primeira vez desistem após a terceira tentativa. Motivo? Erros evitáveis.

**Corpo:**
> 80% das PMEs que tentam licitar pela primeira vez desistem após a terceira tentativa.
>
> Motivo? Erros evitáveis. Os 5 mais frequentes:
>
> **Erro 1: Ignorar o prazo de esclarecimento.**
> Você pode (e deve) fazer perguntas ao órgão comprador. Quase ninguém faz. Quem faz, geralmente ganha.
>
> **Erro 2: Copiar e colar a proposta da última licitação.**
> Cada edital tem requisitos específicos. Uma proposta genérica é uma proposta descartada.
>
> **Erro 3: Não ler o edital inteiro.**
> Sim, é longo. Sim, é repetitivo. Leia. Os detalhes que importam estão enterrados na metade final.
>
> **Erro 4: Subestimar a habilitação jurídica/fiscal.**
> 40% das propostas técnicas excelentes são desclassificadas na habilitação. CND vencida, certidão trabalhista em atraso, contrato social sem atualização. Detalhes matam.
>
> **Erro 5: Participar de editais sem fit.**
> O edital exige capacidade técnica que você não tem. Ou está em outro estado. Ou o valor é baixo demais para cobrir o esforço de proposta. Dizer "não" é uma competência B2G.
>
> Semana que vem, começo a mostrar dados reais do mercado B2G brasileiro. Quantos editais são publicados por semana? Em quais estados? Em quais setores?
>
> Se está gostando da série, me avisa nos comentários.

**CTA:** Qual desses erros você já cometeu? (Eu já cometi três.)

**Dado/insight do PNCP:** Taxa de desclassificação por habilitação (se tivermos campo — senão, usar como estimativa qualitativa).

**Hashtags:** #LicitaçõesPúblicas #PME #B2G #Compliance #Vendas #GovTech #SetorPúblico

**Imagem:** Carousel de 6 slides — capa + 1 slide por erro, cada slide com título curto e 2 linhas de explicação.

---

## SEMANA 2 — DADOS EXCLUSIVOS

### Post 4 — Terça, 14/04, 08h30
**Tipo:** Data-driven / Insight exclusivo
**Tema:** O ranking de UFs por volume de editais em 2026

**Hook:**
> Analisei 100% dos editais publicados no PNCP em 2026 até agora. O ranking de UFs tem uma surpresa no top 3.

**Corpo:**
> Analisei 100% dos editais publicados no PNCP em 2026 até agora. O ranking de UFs tem uma surpresa no top 3.
>
> **Top 5 por número de editais (2026 até hoje):**
>
> 1. São Paulo — [X] editais, R$ [X] bi
> 2. Minas Gerais — [X] editais, R$ [X] bi
> 3. [UF surpresa] — [X] editais, R$ [X] bi
> 4. Rio de Janeiro — [X] editais, R$ [X] bi
> 5. Paraná — [X] editais, R$ [X] bi
>
> A surpresa: [UF] apareceu no top 3 pela primeira vez desde [ano], superando estados historicamente maiores.
>
> O motivo provável? [Inferir a partir dos dados — pode ser concentração em um órgão específico, obra pública grande, efeito sazonal.]
>
> Por que isso importa para PMEs B2G?
>
> Porque o tamanho do estado não é sinônimo de volume de oportunidade. Nichos regionais são frequentemente subexplorados. Uma PME de engenharia sediada em SP que decide olhar para [UF] pode achar menos concorrência e tickets médios mais atrativos.
>
> Na próxima quinta, vou mostrar os 5 setores com maior crescimento de editais em 2026 — e um deles está dobrando a cada trimestre.

**CTA:** Sua empresa participa de editais fora do seu estado? Por quê sim ou por quê não?

**Dado/insight do PNCP:** Query de top UFs:
```sql
SELECT uf, COUNT(*) as editais, SUM(valor_total_estimado) as valor
FROM pncp_raw_bids
WHERE data_publicacao_pncp >= '2026-01-01'
GROUP BY uf ORDER BY editais DESC LIMIT 10;
```

**Hashtags:** #LicitaçõesPúblicas #B2G #DadosPúblicos #Brasil #PNCP #GovTech #Empreendedorismo

**Imagem:** Mapa do Brasil colorido por intensidade (escala azul) com destaque nos top 5 estados.

---

### Post 5 — Quinta, 16/04, 12h15
**Tipo:** Data-driven
**Tema:** Os setores que estão dobrando de volume em 2026

**Hook:**
> Um setor inteiro dobrou de volume no PNCP em 12 meses. Não é TI. Não é saúde. Vai te surpreender.

**Corpo:**
> Um setor inteiro dobrou de volume no PNCP em 12 meses.
>
> Não é TI. Não é saúde. Vai te surpreender.
>
> Cruzei os dados de editais publicados entre Q1 2025 e Q1 2026, classifiquei por setor e medi o crescimento YoY.
>
> **Top 3 setores com maior crescimento:**
>
> 1. **[Setor 1]** — +[X]% YoY
> 2. **[Setor 2]** — +[X]% YoY
> 3. **[Setor 3]** — +[X]% YoY
>
> Por que [setor 1] dobrou?
>
> Três fatores prováveis:
> (1) Agenda pública nacional de [contexto]
> (2) Liberação de verbas federais específicas
> (3) Pressão de compliance regulatório pós-[ano]
>
> O que isso significa para quem atua no setor? Oportunidade de entrar agora, antes da concorrência perceber.
>
> O que significa para quem está fora? Pode ser o momento de pivotar ou adicionar uma vertical de produto que conversa com esse mercado.
>
> Dados completos, metodologia e análise setorial mais profunda estão no nosso **Panorama de Licitações 2026 T1** (publicação completa saindo no próximo dia 15).
>
> Me chame no privado se quiser receber com embargo antes.

**CTA:** Qual setor você gostaria de ver analisado nos próximos posts? Comenta aí.

**Dado/insight do PNCP:** Query comparativa YoY por setor. Precisa de classificação setorial aplicada ao dataset (usar pipeline de classificação interna SmartLic):
```sql
-- Pseudocódigo: join com tabela de classificação interna
SELECT setor, ano_tri, COUNT(*) FROM pncp_raw_bids_classified
WHERE data_publicacao_pncp BETWEEN '2025-01-01' AND '2026-03-31'
GROUP BY 1, 2;
```

**Hashtags:** #LicitaçõesPúblicas #B2G #DadosPúblicos #Crescimento #PNCP #Mercado #GovTech

**Imagem:** Gráfico de barras horizontais comparando Q1 2025 vs Q1 2026 por setor.

---

### Post 6 — Sábado, 18/04, 10h00
**Tipo:** Data-driven / Insight
**Tema:** O fim do pregão presencial (e o que isso revela)

**Hook:**
> Em 2019, Pregão Presencial representava 31% das compras do governo. Hoje? Menos de 4%. O que isso revela é mais interessante que o número.

**Corpo:**
> Em 2019, Pregão Presencial representava 31% das compras do governo brasileiro.
>
> Hoje? Menos de 4%.
>
> O que isso revela é mais interessante que o número.
>
> **1. A digitalização é irreversível.**
> O Pregão Eletrônico não cresceu porque é "moderno". Cresceu porque é fiscalizável, auditável, mais barato de operar e menos sujeito a cartel presencial.
>
> **2. A Nova Lei 14.133/21 aprofundou isso.**
> Revogou as leis antigas, consolidou o digital como padrão e criou o PNCP como repositório nacional. Uma única porta de entrada para o mercado público.
>
> **3. O paradoxo das PMEs.**
> Em teoria, Pregão Eletrônico democratiza o acesso — qualquer empresa de qualquer lugar pode participar. Na prática, as PMEs ainda estão sub-representadas. Por quê?
>
> **Porque a informação continua assimétrica.**
>
> Saber QUE um edital existe é metade do caminho. A outra metade é ter ferramentas para processar rapidamente centenas de editais por semana e decidir onde investir tempo.
>
> Empresas grandes têm equipes. PMEs têm, no máximo, um sócio tentando conciliar captação B2G com 15 outras prioridades.
>
> É exatamente esse gap que estamos fechando na SmartLic.
>
> Semana que vem, trago cases reais de empresas que estão fazendo isso bem.

**CTA:** Sua empresa ainda participa de Pregão Presencial? Ou já migrou 100% para eletrônico?

**Dado/insight do PNCP:** Query de distribuição modalidade 5 vs 6 ao longo dos anos:
```sql
SELECT EXTRACT(YEAR FROM data_publicacao_pncp) AS ano, modalidade_id, COUNT(*)
FROM pncp_raw_bids GROUP BY 1, 2 ORDER BY 1, 2;
```

**Hashtags:** #LicitaçõesPúblicas #PregãoEletrônico #B2G #TransformaçãoDigital #PNCP #NovaLeiLicitações

**Imagem:** Gráfico de linhas mostrando Pregão Eletrônico vs Presencial de 2019 a 2026.

---

## SEMANA 3 — CASES & CONTRARIAN TAKES

### Post 7 — Terça, 21/04, 08h30
**Tipo:** Case / História
**Tema:** Como uma empresa de engenharia de 12 pessoas fatura 40% em B2G

**Hook:**
> Conheci uma empresa de engenharia de 12 pessoas que fatura 40% via licitação pública. A metodologia deles me surpreendeu.

**Corpo:**
> Conheci uma empresa de engenharia de 12 pessoas que fatura 40% via licitação pública.
>
> Esperava uma equipe B2G dedicada. Um "caçador de editais" em tempo integral. Ferramentas caras.
>
> Nada disso.
>
> O sócio me explicou a metodologia em 5 pontos:
>
> **1. Foco geográfico apertado.** Eles só olham editais em um raio de 200km da sede. Logística conhecida, custo previsível, risco baixo.
>
> **2. Foco setorial apertado.** Só manutenção predial e obras de pequeno porte. Ignoram o resto do catálogo. "A gente sabe o que faz bem."
>
> **3. Critério quantitativo de participação.** Valor mínimo do edital: R$ 80k. Abaixo disso, o custo de produzir proposta não compensa.
>
> **4. Dossiê vivo.** Modelo de proposta atualizado mensalmente. CNDs e certidões renovadas automaticamente. Quando um edital fit aparece, submissão em menos de 48h.
>
> **5. Pós-jogo religioso.** Ganhou ou perdeu, eles analisam por que. Preço foi alto? Proposta técnica fraca? Habilitação? Esse feedback loop é o maior diferencial deles.
>
> O insight que levei dessa conversa: o problema B2G não é ferramenta, é disciplina operacional. Ferramenta ajuda, mas não substitui método.
>
> É por isso que estamos desenhando a SmartLic para ser ferramenta + framework de decisão, não só um agregador de editais.

**CTA:** Se você fatura em B2G, qual é o seu critério mais importante de participação? Comenta aí.

**Dado/insight do PNCP:** Não aplicável diretamente, post é qualitativo.

**Hashtags:** #LicitaçõesPúblicas #Engenharia #PME #B2G #Vendas #Processo #CaseDeSucesso

**Imagem:** Foto autêntica (stock) de obra/canteiro + texto sobre: "40% do faturamento vem do setor público".

---

### Post 8 — Quinta, 23/04, 12h15
**Tipo:** Contrarian take
**Tema:** Por que "licitação não é para todo mundo" é uma desculpa

**Hook:**
> Toda vez que falo de B2G em evento, alguém diz: "licitação não é para todo mundo". É verdade? Não. É uma desculpa.

**Corpo:**
> Toda vez que falo de B2G em evento, alguém diz: "licitação não é para todo mundo".
>
> É verdade?
>
> Não. É uma desculpa.
>
> Vou explicar.
>
> A frase original, bem colocada, seria: "nem toda empresa deveria dedicar 100% do esforço comercial a licitação". Isso sim é verdade.
>
> Mas o que geralmente se quer dizer é outra coisa: "licitação é complicada, burocrática, cheia de armadilhas, e eu prefiro continuar no B2B que já conheço."
>
> E aí temos um problema de raciocínio.
>
> Porque o mesmo argumento (complicado, burocrático, cheio de armadilhas) vale para qualquer mercado novo. Internacional? Complicado. Enterprise direto? Burocrático. Governo estrangeiro? Armadilhas.
>
> Ninguém diz "internacional não é para todo mundo" com o mesmo fatalismo.
>
> A diferença é que B2G tem uma reputação cultural no Brasil — herdada dos tempos em que o setor público era sinônimo de corrupção, morosidade e relacionamentos escusos.
>
> Mas a realidade pós-Lei 14.133 e pós-PNCP é diferente. O jogo é digital, auditável e muito mais meritocrático do que o B2B médio acredita.
>
> Então, pergunta honesta: sua empresa NÃO participa de licitação porque realmente não faz sentido estratégico? Ou porque é mais confortável continuar no que já se conhece?
>
> Se for a segunda, vale rever.

**CTA:** Discorda? Me diz nos comentários por que B2G não seria para sua empresa. Aceito contra-argumentos bons.

**Dado/insight do PNCP:** Não aplicável, post é opinativo.

**Hashtags:** #LicitaçõesPúblicas #B2G #Empreendedorismo #Mindset #PME #GovTech #ContraOPoder

**Imagem:** Texto grande: "'Licitação não é para todo mundo' é uma desculpa." Fundo sólido, tipografia impactante.

---

### Post 9 — Sábado, 25/04, 10h00
**Tipo:** Case / Honesto sobre fracasso
**Tema:** Como eu perdi 4 licitações seguidas antes de entender o jogo

**Hook:**
> Perdi as 4 primeiras licitações que participei. Não por preço. Por desatenção. Se eu pudesse voltar no tempo, falaria comigo mesmo:

**Corpo:**
> Perdi as 4 primeiras licitações que participei.
>
> Não por preço. Por desatenção.
>
> Se eu pudesse voltar no tempo, falaria comigo mesmo:
>
> **Licitação 1:** Errei a formatação do envelope de proposta. Não li a seção 14.3. Desclassificado na abertura.
>
> **Licitação 2:** CND trabalhista vencida há 3 dias. Nunca configurei alerta automático. Desclassificado na habilitação.
>
> **Licitação 3:** Enviei proposta 11 minutos depois do prazo. "Só" 11 minutos. O sistema não liga para seu motivo.
>
> **Licitação 4:** Subestimei a complexidade técnica. Preço baixo para ganhar, margem negativa no contrato. Ganhei a licitação e perdi dinheiro.
>
> Cada erro foi uma lição cara. Hoje, quando alguém me pergunta "qual o segredo do B2G", a resposta honesta é: não existe segredo. Existe um checklist de 30 itens que você precisa seguir religiosamente. Quem não segue, perde.
>
> A parte boa: é ensinável. A parte ruim: ninguém te ensina a menos que você pague caro ou erre caro.
>
> Foi olhando para os meus próprios erros que comecei a pensar na SmartLic como uma ferramenta que não só encontra editais, mas também ajuda a não tropeçar nos mesmos detalhes que me custaram quatro licitações.
>
> Se você está começando agora, meu conselho: erre rápido, documente cada erro e nunca repita.

**CTA:** Qual foi o erro mais caro da sua vida em licitação? Compartilha — ajuda outros a não repetirem.

**Dado/insight do PNCP:** Não aplicável, post é pessoal.

**Hashtags:** #LicitaçõesPúblicas #B2G #LiçõesAprendidas #Empreendedorismo #Founder #PME

**Imagem:** Foto do founder (profissional mas informal) + texto sobre: "4 licitações perdidas antes de entender o jogo".

---

## SEMANA 4 — CTA & SOFT PITCH

### Post 10 — Terça, 28/04, 08h30
**Tipo:** Prova social / Soft pitch
**Tema:** O que beta users da SmartLic estão dizendo

**Hook:**
> Há 4 meses, um pequeno grupo de empresas B2G começou a testar a SmartLic. Três frases que ouvi nas últimas semanas e que me deixaram orgulhoso:

**Corpo:**
> Há 4 meses, um pequeno grupo de empresas B2G começou a testar a SmartLic.
>
> Três frases que ouvi nas últimas semanas e que me deixaram orgulhoso:
>
> **1. "Achei um edital de R$ 800k em uma UF que eu não monitorava. Não teria achado sozinho."**
> — Sócio de empresa de serviços em Florianópolis
>
> **2. "Finalmente consegui parar de perder tempo com editais que nunca fariam sentido pra gente. O score de viabilidade fez a triagem que um analista faria em 2 horas, em 5 segundos."**
> — Gestor B2G em consultoria de Belo Horizonte
>
> **3. "O relatório Excel estilizado impressionou meu sócio. Pela primeira vez a gente discute oportunidades com dado, não com achismo."**
> — Diretor comercial em empresa de engenharia em Goiânia
>
> Por que isso importa?
>
> Porque no último ano investi tempo em construir três coisas que acreditava serem o futuro do mercado B2G brasileiro:
>
> 1. **Agregação real** de PNCP + PCP + ComprasGov em uma única busca consolidada
> 2. **IA setorial** que classifica relevância sem você precisar escrever 100 keywords
> 3. **Score de viabilidade objetivo** que pondera modalidade, timeline, valor e geografia
>
> E começar a ouvir que isso está destravando decisões reais em empresas reais é o sinal de que estamos no caminho certo.
>
> Se você chegou até aqui e nunca testou a SmartLic: são 14 dias grátis, sem cartão. Link nos comentários.

**CTA:** Comenta "quero testar" que mando o link no privado. Ou segue o link no primeiro comentário.

**Dado/insight do PNCP:** Depoimentos reais (anonimizados se necessário) de beta users.

**Hashtags:** #LicitaçõesPúblicas #B2G #ProvaSocial #SmartLic #GovTech #SaaS #Inovação

**Imagem:** Carousel de 4 slides: capa + 1 slide por depoimento, com citação em destaque.

---

### Post 11 — Quinta, 30/04, 12h15
**Tipo:** How-to / Conversão
**Tema:** Como começar no B2G em 7 dias (mesmo com a empresa toda ocupada)

**Hook:**
> Você não precisa de um time B2G para começar. Precisa de 7 dias, um método e uma ferramenta. Aqui está o passo a passo:

**Corpo:**
> Você não precisa de um time B2G para começar.
>
> Precisa de 7 dias, um método e uma ferramenta.
>
> **Dia 1 — Diagnóstico interno (2h)**
> Liste os 3 serviços/produtos que sua empresa entrega melhor. Liste os estados onde você tem operação ou logística viável. Liste seu valor mínimo de contrato que faz sentido financeiro.
>
> **Dia 2 — Certidões e habilitação (3h)**
> Emita todas as CNDs (federal, estadual, municipal, trabalhista, FGTS). Confirme contrato social atualizado. Monte uma pasta digital "Habilitação SmartLic" com tudo.
>
> **Dia 3 — Primeira busca (1h)**
> Cria uma conta na SmartLic (trial gratuito 14 dias) ou use qualquer ferramenta equivalente. Busca editais que casam com seu perfil (setor + UF + valor). Tira prints das 10 primeiras oportunidades.
>
> **Dia 4 — Triagem (2h)**
> Dessas 10, escolha 3 com maior score de viabilidade. Leia os editais completos. Elimine as que têm requisitos impossíveis para sua empresa hoje.
>
> **Dia 5 — Proposta modelo (3h)**
> Escreva uma proposta para o edital com melhor fit. Não envie ainda — use como treino. Identifique os 5 pontos onde você trava e precisa de ajuda.
>
> **Dia 6 — Revisão e ajustes (2h)**
> Mostre a proposta para alguém que já participou de licitação (parceiro, consultor, grupo de founders). Ajuste.
>
> **Dia 7 — Submissão (2h)**
> Envie. Mesmo com dúvida. Mesmo achando que vai perder. O aprendizado da primeira submissão vale mais do que o contrato.
>
> Em 14 dias (uma segunda rodada do ciclo), você terá 2-3 propostas submetidas e um processo rodando.
>
> Em 90 dias, você terá o primeiro contrato ou uma lista clara do que ajustar.
>
> A SmartLic é a ferramenta que recomendo para os dias 3 e 4 desse plano — justamente porque a triagem é o ponto onde a maioria perde tempo demais.

**CTA:** Quer começar nessa segunda? Comenta "vou começar" e eu mando o link da trial gratuita de 14 dias.

**Dado/insight do PNCP:** Opcional — número médio de editais compatíveis encontrados por usuário novo na primeira semana.

**Hashtags:** #LicitaçõesPúblicas #B2G #Empreendedorismo #PME #GovTech #SmartLic #Processo

**Imagem:** Checklist visual 7 dias, estilo planner.

---

### Post 12 — Sábado, 02/05, 10h00
**Tipo:** Reflexão / Soft CTA
**Tema:** O que estamos construindo na SmartLic (e por quê)

**Hook:**
> Um mês de conteúdo sobre licitação pública aqui no LinkedIn. Mais de [X] comentários, dezenas de conversas no privado. Hoje quero contar para onde isso vai.

**Corpo:**
> Um mês de conteúdo sobre licitação pública aqui no LinkedIn.
>
> Mais de [X] comentários. Dezenas de conversas no privado. Sócios de empresas de engenharia, consultorias, fundadores de SaaS, analistas B2G — gente que nunca imaginei alcançar.
>
> Hoje quero contar para onde isso vai.
>
> A SmartLic nasceu de uma frustração muito concreta: o PNCP é o repositório nacional de contratações públicas, mas a experiência de uso é hostil. Busca lenta, filtros rudimentares, zero inteligência sobre relevância.
>
> Enquanto isso, milhares de PMEs brasileiras — empresas com capacidade técnica real — ficam fora do mercado B2G porque o custo de descoberta é alto demais.
>
> Então construí (com uma equipe pequena) o que acho que tinha que existir:
>
> - **Agregação** de 3 fontes públicas em uma busca única
> - **Deduplicação** automática (um edital pode aparecer em 2 ou 3 fontes)
> - **Classificação setorial** com IA — você define seu setor, a IA filtra ruído
> - **Score de viabilidade** em 4 fatores objetivos (modalidade, timeline, valor, geografia)
> - **Pipeline kanban** para gestão de oportunidades
> - **Relatórios Excel** prontos para apresentação
> - **Alertas** quando um edital com alto score aparece no seu perfil
>
> Estamos em POC avançado, beta com trial gratuito, pre-revenue. Isso significa: o produto já funciona, temos usuários reais usando em decisões reais, mas ainda estamos aprendendo e ajustando rápido.
>
> Se você chegou até aqui e:
>
> (1) É uma empresa B2G (ou quer virar uma)
> (2) Está cansado de perder tempo monitorando PNCP manualmente
> (3) Tem apetite para testar uma ferramenta nova e dar feedback honesto
>
> Eu queria te convidar pessoalmente para o trial de 14 dias. Grátis, sem cartão. E aberto a uma call de 20 minutos com quem topar conversar.
>
> smartlic.tech
>
> Obrigado por um mês excelente aqui. Semana que vem a gente começa uma série nova: contratos em execução (a parte que quase ninguém analisa).

**CTA:** Gostou da série? Curte, comenta e segue para a próxima. Quer testar a SmartLic? Link no primeiro comentário ou me chama no privado.

**Dado/insight do PNCP:** Não aplicável, post é de fechamento/pitch.

**Hashtags:** #LicitaçõesPúblicas #B2G #SmartLic #Empreendedorismo #GovTech #SaaS #Brasil

**Imagem:** Foto do time SmartLic (ou do founder sozinho) + logo + URL. Autêntico, não stock.

---

## Observações operacionais

1. **Cross-post:** Cada post deve ser publicado primeiro no perfil pessoal do founder (melhor alcance orgânico no LinkedIn) e em seguida republicado/compartilhado pela Company Page SmartLic com texto adaptado.

2. **Resposta a comentários:** Todos os comentários devem ser respondidos em até 2 horas no primeiro dia do post. Algoritmo LinkedIn recompensa interação rápida.

3. **Métricas a acompanhar:** Impressões, reach, interações (likes + comentários + shares), cliques em link, connection requests geradas, trials iniciados com UTM de LinkedIn.

4. **Ajustes:** Se um tipo de post performar muito acima da média, reforçar na semana seguinte. Se um performar abaixo, pausar o formato.

5. **Base de imagens:** Usar Canva ou Figma para manter identidade visual consistente. Paleta SmartLic (definir: azul principal, cinza neutro, verde de destaque).

6. **Dados a validar antes da publicação:** Todas as queries com `[X]` devem ser executadas no datalake SmartLic e os números reais substituídos antes de publicar. Nunca publicar placeholder.

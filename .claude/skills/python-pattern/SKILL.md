---
name: python-pattern
description: Refatora código Python que já existe (um arquivo, um fluxo como checkout ou importação, ou uma pasta inteira) para seguir os princípios SOLID e os design patterns documentados no DevMap (pages/clean-code). Use sempre que o usuário pedir para refatorar, reestruturar, reorganizar, "limpar", desacoplar ou deixar mais robusto e duradouro um código Python, ou para aplicar SOLID, Strategy, Adapter, Factory, Observer, State, Facade e outros patterns em código existente. Também vale para God class, função gigante, if/elif por tipo espalhado, SDK ou banco chamados dentro da regra de negócio e código difícil de testar, mesmo que o usuário não diga "skill", "SOLID" nem "python-pattern". Não use para escrever código novo do zero nem para documentar um pattern no site (isso é a explain-pattern).
argument-hint: <arquivo, pasta ou fluxo>
---

# python-pattern

Refatora código Python existente para os princípios SOLID e os design patterns do DevMap. São quatro fases, e cada uma deixa um artefato:

| Fase | Saída | Muda código? |
|---|---|---|
| 1. Análise | `analise.md` | Não |
| 2. Plano | `plano.md` | Não |
| 3. Execução | código refatorado + `plano.md` atualizado | Sim, um passo por vez |
| 4. Verificação | seção "Resultado" do `plano.md` + mensagem final | Não |

A regra que atravessa as quatro fases vem da própria documentação: *"Abstração criada antes da segunda mudança costuma ser a abstração errada."* A skill não sai procurando lugar para encaixar pattern. Ela procura o que dói no código e só aplica um pattern quando o sinal dele aparece no código e o custo compensa. Três patterns bem escolhidos, com o resto deixado como está, valem mais que dez aplicados por reflexo.

## A base de conhecimento

`references/` tem as páginas de `pages/clean-code` convertidas para Markdown, com o mesmo texto e a mesma árvore de pastas:

| Arquivo | Para quê |
|---|---|
| `references/sinais.md` | **Comece por aqui.** O índice de diagnóstico. Para cada princípio, a tabela "Como reconhecer a violação". Para cada pattern, a regra, a tabela "Quando usar" (com a coluna "Como reconhecer no código"), o "Teste rápido" e a frequência de uso. |
| `references/introducao.md` e `references/<principio>.md` | SOLID. Cada princípio traz o problema, a ideia, como fica, como reconhecer, quando não aplicar e a relação com os patterns. |
| `references/<grupo>/<pattern>/explicacao.md` | O pattern. Traz problema, papéis, implementação em Python, quando usar, teste rápido, quando não usar, sinais de abuso e parecidos. |
| `references/<grupo>/<pattern>/uso.md` | Situações reais, cada uma com o código sem o pattern e com ele. É onde se acha o caso mais parecido com o código em análise. |
| `references/patterns-introducao.md`, `references/patterns-frequencia.md` | Os três grupos de patterns e a frequência de uso de cada um. |

Os grupos são `criacionais`, `estruturais` e `comportamentais`. Os princípios são `single-responsibility`, `open-closed`, `liskov-substitution`, `interface-segregation` e `dependency-inversion`.

Os arquivos de `references/` são gerados das páginas do DevMap, o repositório em que esta skill está instalada. Não edite nenhum deles à mão. Se esse repositório tiver `pages/clean-code` e alguma página for mais nova que a pasta `references/`, atualize antes de começar. Use `python` no lugar de `py` onde for o caso. O script só reescreve `references/` e não toca no projeto que você vai refatorar:

```
py .claude/skills/python-pattern/scripts/sync_references.py
```

Se a skill estiver instalada num projeto sem `pages/clean-code`, use as referências como estão.

Os modelos dos documentos estão em `templates/analise.md` e `templates/plano.md`.

## Entrada

- **Arquivos ou pasta.** O escopo é o que veio.
- **Um fluxo** ("o checkout", "a importação de notas"). Ache o ponto de entrada (rota, comando, `main`, task) e siga as chamadas até o fim. O escopo é tudo o que o fluxo percorre dentro do projeto. Se não achar o ponto de entrada, pergunte.

Se o escopo for grande demais para uma refatoração só (dezenas de módulos), proponha fatiar e comece pela fatia que mais dói.

Os documentos ficam em `docs/refatoracao/<slug>/`, na raiz do projeto que contém o código, a não ser que o usuário peça outro lugar. O `<slug>` é o nome do fluxo ou da pasta, em minúsculas e com hífen (`checkout`, `importacao-de-notas`).

Pode já existir um `docs/refatoracao/<slug>/relatorio.json`, gerado pela skill `python-pattern-analyse`. Nesse caso, use-o como ponto de partida da Fase 1. Primeiro confira se o código ainda é o mesmo, vendo se as evidências batem com as linhas citadas. Depois aproveite as etapas, o contrato, os achados e os vereditos, e confirme cada um no código antes de escrever a `analise.md`.

## Fase 1: Análise

Nesta fase nenhuma linha de código muda. O objetivo é entender o fluxo bem o bastante para que o plano saia do código, e não do catálogo.

1. **Leia o escopo inteiro.** Leia cada arquivo do começo ao fim. Depois procure quem chama o escopo de fora (busque os nomes públicos). Esses chamadores definem o contrato que a refatoração não pode quebrar.
2. **Rode o que existe.** Rode os testes, se houver, e anote o resultado. Se não houver, anote também: o plano vai começar por eles. Não rode o ponto de entrada se ele tiver efeito real, como cobrar um cartão, enviar e-mail ou escrever num banco de produção.
3. **Mapeie o fluxo em etapas.** Numere as etapas na ordem em que acontecem. Para cada uma, anote o que ela faz, onde está (`arquivo:linha`), o que entra e o que sai, e os efeitos colaterais (banco, rede, disco, e-mail, relógio, aleatoriedade, variável de ambiente, `print`).
4. **Inventarie os elementos.** Para cada classe, módulo ou função de peso, liste as responsabilidades e faça a pergunta do Single Responsibility: *quem me pede para mexer aqui, e por quê?*
5. **Escreva o contrato a preservar.** Inclua as assinaturas públicas, o formato dos retornos, as exceções e mensagens de que alguém depende, a ordem dos efeitos colaterais, o esquema do banco e os formatos de payload e arquivo.
6. **Diagnostique.** Percorra o código com `references/sinais.md` aberto, procurando os sinais da coluna "Como reconhecer". Cada sinal encontrado vira uma **hipótese**, registrada com a evidência (`arquivo:linha` e o trecho) e a dor concreta (o que fica difícil de mudar ou de testar).
7. **Valide cada hipótese na página dela.** Abra o `explicacao.md` do pattern, ou a página do princípio, e então:
   - responda o **Teste rápido** em ordem e anote as respostas: a primeira que manda parar decide;
   - confira cada linha de **Quando não usar** (ou **Quando não aplicar**) contra o código;
   - se dois patterns servem, leia **Parecidos** e decida pela **Regra prática**;
   - ache no `uso.md` o exemplo mais parecido com o código.

   Princípios não têm Teste rápido. Para eles, faça a pergunta central abaixo, tirada de "A ideia" de cada página, e depois cada linha de "Quando não aplicar":

   | Princípio | Pergunta central |
   |---|---|
   | Single Responsibility | Quem vai me pedir para mexer aqui, e por quê? Mais de um nome é mais de uma responsabilidade. |
   | Open/Closed | Qual é o eixo que varia? O próximo caso entra como código novo, ou editando o que já funciona? |
   | Liskov Substitution | A subclasse cumpre tudo o que o código promete a quem usa a classe base? |
   | Interface Segregation | Quem usa esta interface usa todos os métodos dela? |
   | Dependency Inversion | Quem define a interface, a regra ou o detalhe? E a dependência muda, é lenta ou é difícil de testar? |

   **Adapter ou Dependency Inversion.** O Adapter é o Dependency Inversion aplicado quando a interface de fora não é a sua. Para um serviço de infraestrutura com um fornecedor, chamado num lugar só, o passo é de Dependency Inversion: a implementação concreta traduz, sem virar uma camada à parte, como manda o "Quando não usar" do Adapter. O Adapter entra como pattern quando há mais de um fornecedor para a mesma operação, ou quando a tradução (nomes, unidades, erros do fornecedor) já está espalhada pela regra.

   O veredito é um de três: **aplicar**; **não aplicar**, dizendo qual linha de "Quando não usar" pesou; ou **adiar**, quando o sinal existe mas ainda é fraco, anotando o gatilho que faria valer ("quando entrar o segundo gateway").

   Uma hipótese que para na pergunta 1 do Teste rápido ("existe mais de um jeito?", "só uma parte reage?") ganha uma linha na tabela "Descartadas de cara", sem seção própria. A validação completa fica para as hipóteses que passaram da pergunta 1. Assim a análise cresce com o problema, e não com o catálogo.
8. **Escreva `analise.md`** a partir de `templates/analise.md`.

Uma hipótese que não passa no Teste rápido não é aplicada, mesmo que o código "fique mais elegante" com ela. Elegância não está entre as perguntas do teste.

## Fase 2: Plano

1. **Escolha as intervenções** entre os vereditos "aplicar". Só entra no plano o que tiver uma linha do diagnóstico para justificar.
2. **Ordene os passos** pela ordem de retorno da `introducao.md`:
   1. **Passo 0, rede de segurança.** Se o contrato não está coberto, escreva testes de caracterização. Eles fixam o comportamento atual, inclusive o que parece estranho. Esses testes precisam passar no código **original**, antes de qualquer refatoração. O código original não tem onde injetar nada, então os falsos entram por `unittest.mock.patch` na fronteira: biblioteca padrão (`smtplib.SMTP`, `urllib.request.urlopen`), SDK, variável de módulo, banco SQLite em arquivo temporário e data fixada. Esse `patch` é andaime, e não design. Enquanto esses testes existirem, preserve as costuras que eles usam (por exemplo, continue chamando `urllib.request.urlopen` pelo módulo) e anote-as em Riscos. O arquivo de caracterização não muda durante a refatoração: confira com `git diff` ou com o hash do arquivo.
   2. **Separar responsabilidades** (Single Responsibility). Cada responsabilidade com um ator diferente sai da classe ou função que concentra tudo.
   3. **Inverter as dependências de I/O** (Dependency Inversion). A regra passa a receber o que hoje importa ou instancia, e um ponto de montagem único cria as peças concretas. Os Adapters de infraestrutura (banco, e-mail, gateway) entram aqui, ou logo depois, um fornecedor por passo: eles são o Dependency Inversion aplicado quando a interface de fora não é a sua. Os testes novos usam injeção, e não `patch`.
   4. **Os patterns de variação** (Strategy, State, Observer, Chain of Responsibility…) que se apoiam nessa base, um por passo.
   5. **Os ajustes de Open/Closed, Liskov e Interface Segregation** que ainda faltarem.

   Cada passo precisa ser pequeno, verificável sozinho e terminar com os testes verdes.
3. **Detalhe cada passo.** Diga o objetivo, o princípio ou pattern (com o caminho da referência), o sinal do diagnóstico que justifica o passo, os arquivos e classes que nascem ou mudam, o que fica igual e como verificar.
4. **Desenhe o resultado.** Mostre a árvore de módulos depois da refatoração e o ponto de montagem, onde as implementações concretas são criadas e injetadas.
5. **Escreva `plano.md`** a partir de `templates/plano.md`, com a tabela de considerados e descartados vinda da análise.
6. **Pare e mostre o plano.** Resuma a análise e os passos em poucas linhas e peça aprovação antes de mexer no código. Se o usuário já disse que pode aplicar direto, sem perguntar, siga para a Fase 3 e avise que seguiu. "Aplicar direto" autoriza executar os passos de refatoração. Não autoriza corrigir bug: a correção só entra no plano com pedido explícito.

## Fase 3: Execução

Faça um passo por vez, na ordem do plano. Em cada passo:

1. **Releia a referência.** Para um pattern, leia `#implementacao` e `#sinais-de-abuso` no `explicacao.md` e o exemplo mais parecido no `uso.md`. Para um princípio, leia `#depois` ("Como fica") e o callout **Perigo** de `#quando-nao-aplicar`. Siga a forma de lá (papéis, `ABC` ou `Protocol`, função ou classe) com os nomes do domínio do código.
2. **Faça a mudança.**
3. **Rode os testes.** Se passarem, marque o passo como feito no `plano.md`. Se falharem, conserte antes de seguir. Um teste de caracterização só muda se a mudança de comportamento estiver prevista no plano.
4. **Registre os desvios.** Se o código mostrar algo que a análise não viu, anote no "Registro de execução" o que mudou no plano e por quê. Se o desvio mexe no escopo ou no contrato, pare e pergunte.

Convenções que valem em todos os passos:

- **Função antes de classe.** Uma variante que é só uma função sem estado é passada como função (`Callable`), como diz o "Quando não usar" do Strategy.
- **Dados com forma.** Os dados que circulam entre as etapas viram `@dataclass` quando isso deixa o fluxo mais claro. Um `dict` que chega de fora pela API pública continua sendo aceito na entrada. Cuidado: converter tudo logo na entrada pode antecipar um erro. Um campo ausente que hoje só falha depois da cobrança passaria a falhar antes dela, e isso é mudança de comportamento. Converta no ponto em que o original lia o campo, ou só quando o contrato permitir.
- **Domínio sem infraestrutura.** Os módulos de regra não importam `sqlite3`, `smtplib`, `urllib`, `requests` nem SDKs. Esses imports moram nos adaptadores e repositórios, e só o ponto de montagem conhece as classes concretas.
- **API pública intacta.** Se alguém de fora chama `GerenciadorDePedidos().processar(dados)`, essa chamada continua funcionando. A forma mais simples é a classe original receber as dependências por argumentos nomeados opcionais e, sem eles, montar as versões padrão (lendo o ambiente como antes). Não crie uma fachada que só repete os métodos de outra classe: é o sinal de abuso "a fachada espelha o subsistema" do Facade. A outra saída é atualizar todos os chamadores no mesmo passo.
- **Mesma língua.** Os nomes novos ficam na língua do código original.
- **Bug não se corrige de carona.** Um bug encontrado vai para a seção 8 da análise. Ele só é corrigido num passo próprio do plano, com o teste de caracterização ajustado e o motivo anotado.

## Fase 4: Verificação

1. Rode todos os testes e, se der, o ponto de entrada com falsos no lugar do I/O.
2. Revise cada pattern aplicado contra a seção **Sinais de que o \<pattern\> saiu do lugar** da página dele, e cada princípio contra o callout **Perigo** da página dele.
3. Confira quatro coisas: todo sinal do diagnóstico foi tratado ou tem veredito com motivo; nenhum pattern entrou sem sinal; nenhum módulo de domínio importa infraestrutura; nenhum comportamento do contrato mudou fora do que o plano previa.
4. Preencha a seção **Resultado** do `plano.md` com o antes e depois de cada diagnóstico, os testes, os desvios e o que ficou para depois (com o gatilho).
5. Responda ao usuário com uma mensagem curta. Inclua onde estão os documentos, uma tabela dos passos (problema → princípio ou pattern → onde), o que foi descartado e por quê, o resultado dos testes, as mudanças de comportamento (o ideal é nenhuma) e os bugs encontrados. Não faça commit sem pedido.

## Erros comuns

| Erro | Por que é um problema | Faça isto |
|---|---|---|
| Refatorar sem teste de caracterização | Não há como provar que o comportamento ficou igual; "funciona" vira opinião | Passo 0, verde no código original |
| Aplicar pattern porque o catálogo tem um que "cabe" | A abstração nasce antes da segunda mudança e costuma ser a errada | Só com sinal no código, Teste rápido e "Quando não usar" conferidos |
| Uma interface `IAlgumaCoisa` para cada classe, com uma implementação só | É o sinal de exagero do Dependency Inversion: a abstração copia a classe | Inverter só o que muda, é lento ou é difícil de testar |
| Uma classe por verbo (`CalculadorDeTotal`, `SomadorDeItens`) | É o exagero do Single Responsibility: para entender o fluxo, abre-se doze arquivos | Uma classe por **motivo de mudança** |
| Strategy em classe para variantes que são uma conta de uma linha | A classe é cerimônia em volta de um método | Uma função, ou um `dict` de funções |
| State com uma classe por fase quando as fases só dizem quais transições valem | São classes vazias para o que um `enum` com dicionário de transições resolve | Leia o "Quando não usar" do State antes |
| Corrigir bug, renomear mensagem de erro ou mudar retorno "de carona" | O contrato muda sem ninguém ver, e os chamadores de fora quebram | Registrar na análise e corrigir em passo próprio |
| Trocar `Exception` por exceções próprias "porque a mensagem é a mesma" | O tipo da exceção faz parte do contrato: quem testa `type(e)` ou captura outra classe quebra | Tipos novos só como passo do plano, com o contrato revisto |
| Criar ponto de extensão para variação que não existe (um `Protocol` de frete com uma regra só, um registro de plugins para dois casos) | É abstração antes da segunda mudança | Função direta; o gatilho para extrair vai em "Para depois" |
| Mexer no que está fora do escopo ou no que já está bom | Aumenta o diff e o risco sem resolver dor nenhuma | Seção 9 da análise: "o que fica como está" |
| Pular a análise porque "o código é pequeno" | O plano passa a sair do catálogo, e não do código | As quatro fases, mesmo que a análise seja curta |

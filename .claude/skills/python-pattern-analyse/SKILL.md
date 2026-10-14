---
name: python-pattern-analyse
description: Analisa código Python que já existe (um arquivo, um fluxo como checkout ou importação, ou uma pasta) sem alterar nada e gera um relatório HTML de revisão sênior, com o que precisa mudar, por quê, qual princípio SOLID ou design pattern aplicar, onde, em que ordem e com que custo, com base na documentação do DevMap (pages/clean-code). Use quando o usuário pedir análise, diagnóstico, avaliação, revisão de arquitetura, code review estrutural, auditoria, parecer, proposta ou relatório de refatoração de código Python, ou quiser saber o que mudar e quais patterns cabem antes de mexer no código, mesmo que não diga "skill" nem "python-pattern-analyse". Para aplicar a refatoração no código, a skill é a python-pattern.
argument-hint: <arquivo, pasta ou fluxo>
---

# python-pattern-analyse

Lê um fluxo Python e entrega o relatório que um engenheiro sênior escreveria depois de revisar o código: o que dói, a evidência no código, o princípio ou pattern que resolve, onde aplicar, o custo, o que **não** fazer e a ordem do trabalho.

**Esta skill não altera nada no projeto analisado.** Não edita código, não cria testes e não formata arquivos. O que ela escreve fica só em `docs/refatoracao/<slug>/`:

| Arquivo | O que é |
|---|---|
| `relatorio.json` | O conteúdo da análise, escrito por você |
| `relatorio.html` | O relatório, gerado do JSON pelo script, num arquivo só e no visual do DevMap |

O `<slug>` é o nome do fluxo ou da pasta, em minúsculas e com hífen. Se o usuário pedir outro lugar, use o lugar pedido.

## A base de conhecimento

O diagnóstico usa a mesma base da skill `python-pattern`, em `.claude/skills/python-pattern/references/`:

- `sinais.md`: o índice de diagnóstico, com os sinais de cada princípio e pattern, o Teste rápido e a frequência de uso;
- `<principio>.md`: os cinco princípios SOLID;
- `<grupo>/<pattern>/explicacao.md` e `uso.md`: cada pattern e os exemplos de uso.

Se essa pasta não existir, pare e avise. Sem ela a análise sai do conhecimento geral, e não da documentação.

Os arquivos desta skill são:

- `references/formato.md`: o formato do `relatorio.json`, campo por campo;
- `exemplo/relatorio.json`: uma análise completa do código em `exemplo/loja/`, que é a régua de qualidade;
- `exemplo/relatorio.html`: o HTML que o exemplo gera.

Leia `references/formato.md` e `exemplo/relatorio.json` antes de escrever o seu.

## O que faz o relatório ser sênior

O relatório é julgado por estes critérios, que valem para todo campo de texto:

- **Toda afirmação aponta para o código.** Cada achado traz `arquivo:linha` e o trecho. "O código está acoplado" sem evidência não entra.
- **A dor é concreta.** O texto diz o que fica difícil: "um gateway novo exige editar a regra de preço", e não "viola o OCP". O princípio aparece como rótulo, e a consequência como explicação.
- **Recomenda pouco e bem.** Cada recomendação resolve achados reais e passou pelo Teste rápido da página do pattern. O que não passou vai para "Considerados e descartados", com o motivo e o gatilho que o traria de volta. Um relatório que recomenda o catálogo inteiro não ajuda ninguém a decidir.
- **Diz o custo.** Todo pattern tem custo (classes, indireção, leitura), e cada recomendação diz qual é.
- **Respeita a forma mais simples.** Se a página do pattern indica função em vez de classe, ou `enum` com dicionário em vez de State, a recomendação segue a página.
- **Separa bug de refatoração.** Um bug encontrado vai para a seção de bugs, e não para as recomendações.
- **Reconhece o que está bom.** O que deve ficar como está entra em `fica_como_esta`, com o motivo.

## Passo a passo

### 1. Ler e mapear

1. **Defina o escopo.** Para arquivos ou pasta, o escopo é o que veio. Para um fluxo, ache o ponto de entrada (rota, comando, `main`, task) e siga as chamadas até o fim. Se não achar o ponto de entrada, pergunte.
2. **Leia o escopo inteiro**, cada arquivo do começo ao fim. Depois procure quem chama o escopo de fora, porque esses chamadores definem o contrato.
3. **Rode só o que é seguro.** Pode rodar os testes existentes e anotar o resultado. Não rode o ponto de entrada se ele tem efeito real (cobrança, e-mail, escrita em banco de produção). Para confirmar um bug ou um comportamento sem testes, pode escrever um script descartável, mas **fora** da pasta do projeto (no scratchpad ou num diretório temporário), com falsos no lugar de rede, e-mail e banco, e apagá-lo no fim. Rode Python com `-B` (ou `PYTHONDONTWRITEBYTECODE=1`): importar o projeto cria `__pycache__` dentro dele, e isso já é alterar o projeto.
4. **Mapeie as etapas** na ordem em que acontecem: o que cada uma faz, onde está, o que entra e sai, e os efeitos colaterais.
5. **Liste os elementos** com as responsabilidades de cada um e, para cada responsabilidade, quem pede mudança (o ator).
6. **Escreva o contrato**: assinaturas públicas, retornos, exceções e mensagens, ordem dos efeitos, esquema e formatos.

### 2. Diagnosticar

1. Percorra o código com `sinais.md` aberto, procurando os sinais da coluna "Como reconhecer". Cada sinal encontrado vira uma hipótese. O arquivo é longo, então leia em duas passadas. Primeiro o SOLID e os patterns de uso muito alto e alto, que cobrem a maior parte do código de aplicação. Depois os de uso médio, baixo e raro, procurando só o formato de problema de cada um (árvore, desfazer, fases, linguagem de regras, milhares de objetos iguais).
2. Para cada hipótese, abra a página do pattern e:
   - responda o **Teste rápido** em ordem: a primeira resposta que manda parar decide;
   - confira cada linha de **Quando não usar**;
   - se dois patterns servem, use **Parecidos** e a **Regra prática**;
   - ache no `uso.md` o exemplo mais parecido.
3. Princípios não têm Teste rápido. Para eles, faça a pergunta central abaixo, tirada de "A ideia" de cada página, e depois cada linha de "Quando não aplicar":

   | Princípio | Pergunta central |
   |---|---|
   | Single Responsibility | Quem vai me pedir para mexer aqui, e por quê? Mais de um nome é mais de uma responsabilidade. |
   | Open/Closed | Qual é o eixo que varia? O próximo caso entra como código novo, ou editando o que já funciona? |
   | Liskov Substitution | A subclasse cumpre tudo o que o código promete a quem usa a classe base? |
   | Interface Segregation | Quem usa esta interface usa todos os métodos dela? |
   | Dependency Inversion | Quem define a interface, a regra ou o detalhe? E a dependência muda, é lenta ou é difícil de testar? |

4. **Adapter ou Dependency Inversion.** O Adapter é o Dependency Inversion aplicado quando a interface de fora não é a sua, por isso os dois se sobrepõem. Para um serviço de infraestrutura com um fornecedor, chamado num lugar só, recomende **Dependency Inversion**: a implementação concreta traduz, mas não precisa de recomendação própria, e o "Quando não usar" do Adapter diz para não criar a camada. Recomende **Adapter** quando houver mais de um fornecedor para a mesma operação, ou quando a tradução (nomes, unidades, erros do fornecedor) já estiver espalhada pela regra.
5. Agrupe as hipóteses em **achados**. Junte sinais num achado só quando a dor e a severidade são as mesmas, e a mesma mudança resolve. Separe quando a dor é diferente, mesmo que a recomendação seja a mesma. Por exemplo, um banco acoplado que impede o teste e uma API chamada dentro de um laço, sem timeout, são dois achados, ainda que os dois se resolvam invertendo a dependência. Dê a cada achado uma severidade:

   | Severidade | Quando |
   |---|---|
   | `alta` | A mudança que o negócio já pede, ou vai pedir em breve, se espalha por vários lugares; o núcleo não pode ser testado; ou há risco para dinheiro ou dados |
   | `media` | O custo é real, mas localizado: vai doer na próxima mudança daquela área |
   | `baixa` | Incomoda a leitura, ou é uma força que ainda é pequena. Vale tratar quando passar por perto |

6. Vai para `descartados` toda hipótese que alguém revisando este código provavelmente sugeriria, porque o sinal está à vista, mesmo que ela pare na primeira pergunta do Teste rápido. É exatamente essa sugestão que o relatório precisa responder. A hipótese que só aparece por varrer o catálogo, sem sinal visível, fica de fora. Essa seção mostra o critério do analista, e não um inventário do catálogo.

### 3. Propor

1. **Recomendações.** Escreva uma por aplicação de princípio ou pattern, com os campos de `formato.md`. O `codigo_proposto` é um esboço do "depois" com os nomes reais do código, seguindo a forma da seção Implementação (ou "Como fica", no caso dos princípios) da página. Mostre a forma, sem implementar tudo.
2. **Impacto e esforço** posicionam cada recomendação na matriz:
   - impacto `alto` destrava mudanças frequentes ou o teste do núcleo; `medio` melhora uma área; `baixo` é conforto;
   - esforço é medido pelo tempo, incluindo os testes, e não pelo número de arquivos: `P` vai até meio dia, `M` leva de meio dia a dois dias, e `G` passa de dois dias ou muda o contrato.
3. **Roteiro.** O passo 0 é a rede de segurança (testes de caracterização), se não houver testes. Depois vêm, nesta ordem, separar responsabilidades, inverter as dependências de I/O (os Adapters de infraestrutura entram aqui), os patterns de variação e os ajustes de O, L e I. Toda recomendação aparece em algum passo.
4. **Arquitetura.** Mostre a árvore de módulos antes e depois, e o ponto de montagem: onde as peças concretas são criadas e como a API pública continua funcionando.
5. **Riscos, bugs e o que fica.** Liste o que pode quebrar e como se proteger, e o que não deve mudar. Os bugs encontrados ganham id (`B1`…) e severidade, ficam fora das recomendações e, se valer, entram num último passo do roteiro, "decidido à parte", porque corrigir muda o contrato. Num pedido de "mais robusto", os bugs costumam ser a parte mais valiosa: não economize neles.
6. **Resumo executivo, por último.** O veredito vem numa frase. O texto tem um ou dois parágrafos para quem só lê o topo. Os destaques são de três a cinco conclusões, e cada uma cita com `[[A1]]`, `[[R1]]` ou `[[B1]]` o que estiver por trás dela.

### 4. Gerar e validar

A partir da raiz do projeto analisado (use `python` no lugar de `py` onde for o caso):

```
py .claude/skills/python-pattern-analyse/scripts/gerar_relatorio.py docs/refatoracao/<slug>/relatorio.json
```

Se a skill estiver instalada fora do projeto, passe o caminho completo do script e `--raiz <pasta do projeto>`.

O script lê as evidências dos arquivos reais e confere ids, referências, intervalos de linha e campos obrigatórios. Enquanto houver erro, o HTML não é gerado. Corrija e rode de novo. Avisos não bloqueiam, mas cada um merece uma olhada.

### 5. Revisar como quem recebe

Releia o JSON como a pessoa que vai receber o relatório e decidir:

- O resumo, sozinho, diz o que fazer e por quê?
- Cada achado mostra no trecho exatamente o que o texto afirma? As linhas destacadas são as que importam?
- Alguma recomendação não tem achado forte por trás? Se tiver, ela sai.
- O Teste rápido foi respondido para **este** código, e não de forma genérica?
- O roteiro dá para executar na ordem, com cada passo verificável?

### 6. Entregar

Responda com uma mensagem curta:

- o caminho do `relatorio.html` (abre direto no navegador);
- o veredito;
- uma tabela com as recomendações (pattern, onde, impacto e esforço);
- os descartados, numa linha;
- os bugs, se houver.

Diga que, para aplicar, a skill é a `python-pattern`, que pode partir deste relatório. Não faça commit sem pedido.

## Escrita

Português do Brasil, frases curtas, uma ideia por parágrafo, sem enchimento ("é importante notar que") e sem emoji. Use o nome do pattern como na documentação (em inglês, como no catálogo GoF) e os nomes do código como estão. Negrito só na palavra que carrega a frase.

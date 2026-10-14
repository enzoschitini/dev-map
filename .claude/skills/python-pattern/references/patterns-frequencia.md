<!-- Gerado de pages/clean-code/patterns-frequencia.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Frequência de uso

*Clean Code / Design Pattern*

Quais padrões aparecem com mais frequência no código do dia a dia, e por onde começar a estudar.

<a id="como-ler"></a>
## Como ler esta página

Os 23 padrões não pesam o mesmo. Uns você usa toda semana; outros, uma vez na carreira. Esta página ordena por quanto cada um aparece em código de aplicação comum: sistemas web, APIs, aplicativos, bibliotecas.

> **Cuidado.** A classificação é uma **estimativa qualitativa**, baseada no que costuma aparecer em frameworks e projetos de aplicação. Não é fruto de uma medição. Ela muda com a linguagem: onde há função de primeira classe, o Strategy e o Command viram uma função; onde há contêiner de injeção, o Singleton deixa de ser uma classe escrita à mão.

<a id="por-nivel"></a>
## Por nível

<a id="muito-alta"></a>
### Muito alta

Aparece em quase todo projeto, muitas vezes sem que ninguém o chame pelo nome.

[Strategy](comportamentais/strategy/explicacao.md), [Observer](comportamentais/observer/explicacao.md), [Factory Method](criacionais/factory-method/explicacao.md), [Adapter](estruturais/adapter/explicacao.md), [Facade](estruturais/facade/explicacao.md), [Iterator](comportamentais/iterator/explicacao.md).

<a id="alta"></a>
### Alta

Aparece em boa parte dos projetos, quase sempre num ponto específico.

[Builder](criacionais/builder/explicacao.md), [Decorator](estruturais/decorator/explicacao.md), [Singleton](criacionais/singleton/explicacao.md), [Command](comportamentais/command/explicacao.md), [Template Method](comportamentais/template-method/explicacao.md), [Proxy](estruturais/proxy/explicacao.md).

<a id="media"></a>
### Média

Aparece quando o problema é daquele formato, o que não acontece em todo sistema.

[State](comportamentais/state/explicacao.md), [Composite](estruturais/composite/explicacao.md), [Chain of Responsibility](comportamentais/chain-of-responsibility/explicacao.md), [Abstract Factory](criacionais/abstract-factory/explicacao.md), [Mediator](comportamentais/mediator/explicacao.md).

<a id="baixa"></a>
### Baixa

Útil em casos conhecidos e bem delimitados. Se você não está num deles, não procure um.

[Prototype](criacionais/prototype/explicacao.md), [Memento](comportamentais/memento/explicacao.md), [Bridge](estruturais/bridge/explicacao.md), [Visitor](comportamentais/visitor/explicacao.md).

<a id="rara"></a>
### Rara

Pertence a domínios específicos. Vale conhecer a ideia; é raro precisar escrever.

[Flyweight](estruturais/flyweight/explicacao.md), [Interpreter](comportamentais/interpreter/explicacao.md).

<a id="tabela"></a>
## Tabela completa

Do mais frequente ao menos frequente, com o lugar em que cada padrão costuma aparecer.

| Frequência | Pattern | Grupo | Onde aparece |
|---|---|---|---|
| **Muito alta** | [Strategy](comportamentais/strategy/explicacao.md) | Comportamental | Troca de regra de cálculo, de ordenação, de pagamento; em linguagens com função de primeira classe, é só passar uma função. |
| **Muito alta** | [Observer](comportamentais/observer/explicacao.md) | Comportamental | Eventos de interface, filas, webhooks, `addEventListener`, stores reativos. |
| **Muito alta** | [Factory Method](criacionais/factory-method/explicacao.md) | Criacional | Construtores nomeados, `createX()`, métodos estáticos que escolhem a classe devolvida. |
| **Muito alta** | [Adapter](estruturais/adapter/explicacao.md) | Estrutural | Integração com API de terceiros, biblioteca antiga, SDK com interface que não é a sua. |
| **Muito alta** | [Facade](estruturais/facade/explicacao.md) | Estrutural | Um serviço de aplicação que esconde três chamadas na ordem certa; um SDK com um cliente simples na frente. |
| **Muito alta** | [Iterator](comportamentais/iterator/explicacao.md) | Comportamental | Já vem pronto: `for…of`, geradores, streams. Você o usa todo dia e o escreve raramente. |
| **Alta** | [Builder](criacionais/builder/explicacao.md) | Criacional | Objeto com muitos campos opcionais: consultas, requisições HTTP, configurações, objetos de teste. |
| **Alta** | [Decorator](estruturais/decorator/explicacao.md) | Estrutural | Middlewares, logging, cache e autenticação em volta de um serviço; decorators da linguagem. |
| **Alta** | [Singleton](criacionais/singleton/explicacao.md) | Criacional | Configuração, pool de conexões, logger. Hoje costuma vir do contêiner de injeção, como escopo, e não escrito à mão. |
| **Alta** | [Command](comportamentais/command/explicacao.md) | Comportamental | Desfazer e refazer, filas de tarefas, botões e atalhos que disparam a mesma ação. |
| **Alta** | [Template Method](comportamentais/template-method/explicacao.md) | Comportamental | Classe base de framework com ganchos para sobrescrever: testes, jobs, importadores. |
| **Alta** | [Proxy](estruturais/proxy/explicacao.md) | Estrutural | Carregamento sob demanda, cache transparente, controle de acesso; o ORM usa muito. |
| **Média** | [State](comportamentais/state/explicacao.md) | Comportamental | Fluxos com fases bem definidas: pedido, pagamento, documento em revisão, conexão. |
| **Média** | [Composite](estruturais/composite/explicacao.md) | Estrutural | Árvores: menus, pastas, componentes de interface, organogramas. |
| **Média** | [Chain of Responsibility](comportamentais/chain-of-responsibility/explicacao.md) | Comportamental | Cadeia de validações, pipeline de middlewares, tratamento de pedido em níveis. |
| **Média** | [Abstract Factory](criacionais/abstract-factory/explicacao.md) | Criacional | Suporte a vários temas, bancos ou plataformas em que as peças precisam combinar entre si. |
| **Média** | [Mediator](comportamentais/mediator/explicacao.md) | Comportamental | Telas com muitos campos que dependem uns dos outros; chat; coordenação entre módulos. |
| **Baixa** | [Prototype](criacionais/prototype/explicacao.md) | Criacional | Clonar um objeto caro de montar: modelos de documento, estado inicial de jogo. |
| **Baixa** | [Memento](comportamentais/memento/explicacao.md) | Comportamental | Snapshots para desfazer em editores, formulários com rascunho, pontos de restauração. |
| **Baixa** | [Bridge](estruturais/bridge/explicacao.md) | Estrutural | Duas dimensões que crescem separadas: formas e renderizadores, controle e dispositivo. |
| **Baixa** | [Visitor](comportamentais/visitor/explicacao.md) | Comportamental | Operações novas sobre uma estrutura estável de tipos: compiladores, analisadores de árvore. |
| **Rara** | [Flyweight](estruturais/flyweight/explicacao.md) | Estrutural | Milhares de objetos quase iguais em memória: jogos, editores de texto, mapas. |
| **Rara** | [Interpreter](comportamentais/interpreter/explicacao.md) | Comportamental | Linguagem de regras ou de consulta própria. Na prática, costuma-se usar um parser pronto. |

<a id="por-onde-comecar"></a>
## Por onde começar

Estude na ordem da tabela, de cima para baixo. Os de frequência muito alta e alta cobrem a maior parte do que você vai ler em código de outras pessoas, e vários deles você já usa sem o nome.

Os de frequência baixa e rara servem para reconhecer. Quando um deles aparecer, você identifica a forma e sabe onde voltar para ver os detalhes.

A visão geral dos três grupos está na [Introdução](patterns-introducao.md).

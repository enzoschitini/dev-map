<!-- Gerado de pages/clean-code/patterns-introducao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Introdução

*Clean Code / Design Pattern*

O que são os padrões de projeto, como eles se dividem em três grupos e onde achar cada um.

<a id="o-que-sao"></a>
## O que são padrões de projeto

Soluções que se repetem para problemas que se repetem. Ninguém inventou os 23 padrões deste mapa: eles foram catalogados no livro *Design Patterns* (a "Gang of Four", 1994) depois de aparecerem, com formas parecidas, em projetos muito diferentes.

Um padrão não é uma biblioteca nem um trecho para copiar. É um **formato de solução**: ele diz como as classes se organizam e por quê, e o código você escreve de acordo com a sua linguagem.

O catálogo se divide pela pergunta que cada padrão responde. São três pastas, e cada uma tem o seu lugar no menu lateral.

<a id="criacionais"></a>
## Criacionais

Respondem a **como um objeto nasce**. Tratam da criação: quem decide a classe, quantas instâncias existem, em que passos o objeto é montado.

O problema que resolvem é o `new` espalhado pelo código. Quando toda classe cria as suas dependências diretamente, trocar uma implementação obriga a editar todos os lugares que a criam.

Cinco padrões: Singleton, Factory Method, Abstract Factory, Builder e Prototype.

<a id="estruturais"></a>
## Estruturais

Respondem a **como as peças se encaixam**. Tratam da forma: como compor classes e objetos em estruturas maiores sem que uma peça precise conhecer os detalhes das outras.

O problema que resolvem é o acoplamento entre estruturas que não combinam: uma interface de fora que não é a que você espera, uma classe para cada combinação de duas variações, um subsistema com dez passos na ordem certa.

Sete padrões: Adapter, Bridge, Composite, Decorator, Facade, Flyweight e Proxy.

<a id="comportamentais"></a>
## Comportamentais

Respondem a **como os objetos conversam e dividem o trabalho**. Tratam da responsabilidade: quem faz o quê, quem avisa quem, de que jeito um algoritmo pode ser trocado.

O problema que resolvem é o `if` e o `switch` que crescem a cada caso novo, e as classes que sabem demais umas das outras para conseguir se comunicar.

Onze padrões: Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento, Observer, State, Strategy, Template Method e Visitor.

> **Nota.** A fronteira entre os grupos não é rígida. O Decorator é estrutural, mas o efeito dele é mudar comportamento. A pergunta do grupo diz o foco principal do padrão, não tudo o que ele faz.

<a id="tabela"></a>
## Os padrões

Os 23 padrões do mapa, agrupados como no menu. O nome de cada um leva para a página de explicação.

| Grupo | Pattern | Em uma linha |
|---|---|---|
| Criacional | [Singleton](criacionais/singleton/explicacao.md) | Como garantir que um objeto existe uma vez só e que todo mundo chega nele |
| Criacional | [Factory Method](criacionais/factory-method/explicacao.md) | Como criar um objeto sem saber a classe exata, entregando a escolha às subclasses |
| Criacional | [Abstract Factory](criacionais/abstract-factory/explicacao.md) | Como criar um conjunto de objetos que combinam entre si, sem misturar peças de famílias diferentes |
| Criacional | [Builder](criacionais/builder/explicacao.md) | Como montar um objeto complexo por partes e só entregá-lo quando estiver completo e válido |
| Criacional | [Prototype](criacionais/prototype/explicacao.md) | Como criar um objeto copiando outro que já existe, sem conhecer a classe nem os campos |
| Estrutural | [Adapter](estruturais/adapter/explicacao.md) | Como encaixar uma interface que você não controla na que o seu código espera |
| Estrutural | [Bridge](estruturais/bridge/explicacao.md) | Como deixar duas coisas que variam por motivos diferentes crescerem separadas, sem uma subclasse para cada combinação |
| Estrutural | [Composite](estruturais/composite/explicacao.md) | Como tratar um item e um grupo de itens do mesmo jeito, em qualquer profundidade |
| Estrutural | [Decorator](estruturais/decorator/explicacao.md) | Como acrescentar comportamento a um objeto sem mexer nele e sem uma subclasse para cada combinação |
| Estrutural | [Facade](estruturais/facade/explicacao.md) | Como dar uma porta de entrada simples para um conjunto de peças que só funcionam na ordem certa |
| Estrutural | [Flyweight](estruturais/flyweight/explicacao.md) | Como manter centenas de milhares de objetos sem repetir em cada um o que é igual para todos do mesmo tipo |
| Estrutural | [Proxy](estruturais/proxy/explicacao.md) | Como pôr um representante no lugar de um objeto, para controlar se, quando ou onde o real é usado |
| Comportamental | [Chain of Responsibility](comportamentais/chain-of-responsibility/explicacao.md) | Como passar um pedido por uma sequência de tratadores, sem quem pede saber qual deles responde |
| Comportamental | [Command](comportamentais/command/explicacao.md) | Como transformar um pedido de ação em um objeto, para guardar, desfazer, enfileirar ou repetir |
| Comportamental | [Interpreter](comportamentais/interpreter/explicacao.md) | Como representar regras que mudam como uma árvore de objetos que se avalia sozinha |
| Comportamental | [Iterator](comportamentais/iterator/explicacao.md) | Como percorrer uma coleção, ou uma fonte de dados, sem depender de como ela guarda os elementos |
| Comportamental | [Mediator](comportamentais/mediator/explicacao.md) | Como deixar um grupo de objetos trabalhar junto sem que cada um conheça todos os outros |
| Comportamental | [Memento](comportamentais/memento/explicacao.md) | Como guardar o estado de um objeto para voltar a ele depois, sem expor o que tem dentro |
| Comportamental | [Observer](comportamentais/observer/explicacao.md) | Como avisar várias partes do sistema de que algo aconteceu, sem quem avisa saber quem são elas |
| Comportamental | [State](comportamentais/state/explicacao.md) | Como fazer um objeto se comportar de um jeito em cada fase da vida, sem um if sobre a fase em cada método |
| Comportamental | [Strategy](comportamentais/strategy/explicacao.md) | Como trocar o jeito de fazer uma coisa sem mexer em quem a pede, e sem um if novo a cada jeito |
| Comportamental | [Template Method](comportamentais/template-method/explicacao.md) | Como escrever uma vez a ordem dos passos de um processo, deixando cada variação preencher só o passo que é diferente |
| Comportamental | [Visitor](comportamentais/visitor/explicacao.md) | Como acrescentar operações a uma estrutura de objetos de tipos diferentes sem abrir cada classe |

Para saber quais valem estudar primeiro, veja [Frequência de uso](patterns-frequencia.md).

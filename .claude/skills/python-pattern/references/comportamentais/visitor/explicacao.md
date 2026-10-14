<!-- Gerado de pages/clean-code/comportamentais/visitor/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Visitor — Explicação

*Clean Code / Design Pattern / Visitor*

Como acrescentar operações novas a uma estrutura de objetos de tipos diferentes, sem abrir cada classe e sem repetir uma escada de `isinstance` em cada operação.

<a id="o-problema"></a>
## O problema

Um pedido guarda itens de tipos diferentes: `Livro`, `Eletronico` e `Kit`, que agrupa outros itens. A equipe precisa de operações sobre eles: calcular o imposto, somar o peso para o frete, e logo virão a nota fiscal, a etiqueta e o relatório de estoque.

Como as classes são só dados, a saída preguiçosa é escrever cada operação como uma função com a escada de `isinstance`:

**antes — a mesma escada de tipos em cada operação**

```python
def calcular_imposto(item):
    if isinstance(item, Livro):
        return 0.0
    if isinstance(item, Eletronico):
        return item.preco * 0.18
    if isinstance(item, Kit):
        return sum(calcular_imposto(i) for i in item.itens)
    raise TypeError(type(item))

def peso_para_frete(item):
    if isinstance(item, Livro):
        return 0.4
    if isinstance(item, Eletronico):
        return item.peso_kg
    if isinstance(item, Kit):
        return sum(peso_para_frete(i) for i in item.itens) + 0.2   # a caixa
    raise TypeError(type(item))
```

A alternativa óbvia, um método por operação dentro de cada classe, também cobra um preço: o `Livro` passa a saber de imposto, frete, nota fiscal e etiqueta, e cada operação nova é uma edição em *todas* as classes. Com as escadas, o esqueleto se repete em cada operação, e um tipo esquecido só aparece como `TypeError` quando ele chega em produção. Em ambos os casos, o Single Responsibility sofre: as classes ou as funções passam a ter um motivo a mais para mudar a cada operação.

<a id="a-solucao"></a>
## A solução

Tire a operação de dentro dos elementos e dê a ela uma classe própria, o visitante, com um método por tipo. Cada elemento ganha um único método, `aceitar`, que diz ao visitante "eu sou um `Livro`". São cinco papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Elemento | A interface das peças: aceita um visitante | `aceitar(visitante)` |
| Elementos concretos | Os tipos da estrutura, que só entregam a si mesmos | `Livro`, `Eletronico`, `Kit` |
| Visitante | A interface da operação: um método por tipo de elemento | `visitar_livro`, `visitar_eletronico`, `visitar_kit` |
| Visitantes concretos | Uma operação inteira, para todos os tipos, em um lugar | `Imposto`, `PesoParaFrete` |
| Cliente | Escolhe o visitante e o entrega aos elementos | O checkout |

O ponto é o **duplo despacho**. A escolha do código a executar depende de dois tipos: o do elemento e o do visitante. O elemento resolve o primeiro ao chamar `visitar_livro(self)`, e o visitante resolve o segundo por ser quem é. Em troca, a ordem dos custos se inverte: uma operação nova é uma classe nova, sem tocar em elemento nenhum; um *tipo* novo obriga a mexer em todos os visitantes.

<a id="implementacao"></a>
## Implementação

```python
from dataclasses import dataclass

# 1. os elementos: só dados, e um método que entrega o tipo ao visitante
@dataclass
class Livro:
    titulo: str
    preco: float

    def aceitar(self, visitante):
        return visitante.visitar_livro(self)

@dataclass
class Eletronico:
    nome: str
    preco: float
    peso_kg: float

    def aceitar(self, visitante):
        return visitante.visitar_eletronico(self)

@dataclass
class Kit:
    itens: list

    def aceitar(self, visitante):
        return visitante.visitar_kit(self)

# 2. um visitante: uma operação inteira, para todos os tipos, em um lugar
class Imposto:
    def visitar_livro(self, livro):
        return 0.0

    def visitar_eletronico(self, e):
        return e.preco * 0.18

    def visitar_kit(self, kit):
        return sum(i.aceitar(self) for i in kit.itens)

# 3. outra operação: uma classe nova, nenhum elemento tocado
class PesoParaFrete:
    def visitar_livro(self, livro):
        return 0.4

    def visitar_eletronico(self, e):
        return e.peso_kg

    def visitar_kit(self, kit):
        return sum(i.aceitar(self) for i in kit.itens) + 0.2   # a caixa

# 4. o cliente: escolhe a operação, sem perguntar o tipo de nada
imposto = sum(item.aceitar(Imposto()) for item in pedido.itens)
peso = sum(item.aceitar(PesoParaFrete()) for item in pedido.itens)
```

> **Dica.** Cada operação se testa inteira, com uma instância de cada tipo: um livro, um eletrônico, um kit com os dois. E quando um tipo novo chega (`Alimento`), o checador de tipos aponta cada visitante que ainda não sabe lidar com ele, em vez de a falha aparecer só quando o item entra em um pedido.

<a id="quando-usar"></a>
## Quando usar

O Visitor vale quando três coisas acontecem ao mesmo tempo: existe uma estrutura de objetos de **tipos diferentes**, em geral uma árvore; as **operações** sobre ela são várias e crescem, ou não pertencem aos objetos; e o conjunto de **tipos muda pouco**. A terceira condição é a que mais se esquece.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| A mesma escada de tipos em cada operação | `if isinstance(item, Livro)` … `if isinstance(item, Kit)` repetido em `calcular_imposto`, `peso_para_frete` e na próxima | O exemplo desta página |
| Classes de domínio com métodos que não são do domínio | `para_pdf()`, `para_csv()` e `validar_fiscal()` no mesmo objeto que representa um livro | O exemplo desta página |
| A operação precisa de antes e depois, ou de estado acumulado | Contadores e níveis passados como argumento extra por uma recursão, `acc=None`, `nivel=0` | [Uso #1](uso.md#relatorio-de-arquivos) |
| A estrutura é de uma biblioteca, e você não pode mudá-la | Uma análise sobre nós de AST, de XML ou do DOM, em que não há onde pôr um método novo | [Uso #2](uso.md#ast-nodevisitor) |
| Uma transformação reescreve a árvore | Uma função recursiva que reconstrói cada nó com os filhos já transformados, e se repete para cada regra de reescrita | [Uso #3](uso.md#simplificar-regras) |

> **Dica.** O que os sinais têm em comum: a operação cresce mais depressa que os tipos. Se você consegue listar os tipos de cabeça e não consegue listar as operações que vão chegar, o Visitor está no lado certo do compromisso.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **A estrutura tem tipos diferentes?** Se todos os elementos são do mesmo tipo, um `for` resolve.
2. **Há mais de uma operação, ou ela está crescendo?** Se é uma só, um método polimórfico na própria classe é o mais simples.
3. **O conjunto de tipos é estável?** Se tipos novos aparecem toda hora, cada um obriga a mudar todos os visitantes. Use polimorfismo comum.
4. **A operação pertence ao domínio, e você controla as classes?** Se sim, ela é um método do elemento. O Visitor vale quando a operação não pertence às classes, ou quando as classes não são suas.

<a id="quando-nao-usar"></a>
## Quando não usar

O Visitor **inverte** o compromisso do polimorfismo comum. Com métodos nas classes, é fácil acrescentar um tipo e difícil acrescentar uma operação; com o Visitor, é o contrário. Soma-se o custo de leitura: o duplo despacho obriga a seguir `aceitar` e depois `visitar_…` para saber o que roda, e cada classe ganha um método de ligação. Em linguagens com `match` exaustivo ou uniões discriminadas, o compilador já entrega boa parte do que o Visitor oferece.

| Situação | Por que não | Faça isto |
|---|---|---|
| Os tipos mudam com frequência | Cada tipo novo obriga a abrir todos os visitantes | Um método em cada classe (polimorfismo comum) |
| Só existe uma operação | O Visitor é cerimônia para algo que um método resolve | O método na própria classe |
| Python 3.10+ ou TypeScript com uniões discriminadas | O `match` ou o `switch` exaustivo já separa por tipo, em um lugar, com checagem | `match` / `switch`, ou `functools.singledispatch` |
| Uma estrutura plana, com poucos tipos | Uma escada de `isinstance` em um lugar é mais curta | Um `for` com `isinstance` |
| A operação precisa de dados privados do elemento | O Visitor obriga a expô-los, e o encapsulamento se perde | Um método no elemento, que expõe só o resultado |

<a id="sinais-de-abuso"></a>
### Sinais de que o Visitor saiu do lugar

- **Um visitante só.** Uma interface, cinco `aceitar` e uma única implementação é um método polimórfico com trabalho extra.
- **Os elementos expõem tudo.** Todos os campos viraram públicos só para os visitantes poderem lê-los, e o encapsulamento foi embora.
- **O `isinstance` voltou para dentro do visitante.** Se o método `visitar_kit` testa o tipo dos filhos, o despacho foi feito duas vezes e o ganho sumiu.
- **Os visitantes dependem uns dos outros.** Um que só funciona depois que outro rodou acopla o que deveria ser independente.
- **O visitante guarda estado global.** Um visitante reaproveitado entre execuções, com acumuladores que ninguém zera, dá resultados que dependem do histórico.

> **Perigo.** O sinal mais comum: um tipo novo chega e há quatorze visitantes para atualizar. Os tipos mudam mais do que se supunha, e o compromisso do Visitor está do lado errado. Volte para métodos nas classes.

> **Nota.** Na dúvida, comece com `match` ou `isinstance` em uma função. Extraia o Visitor quando a terceira operação chegar e o mesmo `match` estiver em três lugares, e quando você puder dizer, com certeza, que os tipos não vão mudar na mesma velocidade.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Iterator](../iterator/explicacao.md) | Entrega os elementos um a um, sem se importar com o tipo. O Visitor trata cada tipo de um jeito. Os dois se combinam: o Iterator percorre e o Visitor age |
| [Composite](../../estruturais/composite/explicacao.md) | É a estrutura em árvore; o Visitor é uma operação sobre ela. É a dupla mais comum do catálogo |
| [Interpreter](../interpreter/explicacao.md) | Cada nó da árvore sabe se avaliar: a operação está *dentro* do nó. O Visitor leva a operação para fora, e permite somar leituras sem abrir as classes |
| [Strategy](../strategy/explicacao.md) | Troca o algoritmo de uma tarefa. O Visitor carrega um algoritmo por *tipo* de elemento, e é a combinação dos dois que escolhe o código |

Regra prática: se o que varia é a operação e os tipos são estáveis, é Visitor. Se são os tipos que variam, o polimorfismo comum é melhor.

<!-- Gerado de pages/clean-code/estruturais/composite/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Composite — Explicação

*Clean Code / Design Pattern / Composite*

Como tratar um item e um grupo de itens do mesmo jeito, para que o código que usa a estrutura não precise saber em que profundidade está.

<a id="o-problema"></a>
## O problema

A loja vende produtos soltos e **kits**: o "Combo Home Office" tem teclado, mouse e um segundo kit, o "Brinde", com mais dois produtos. Cada kit tem um desconto próprio. O carrinho precisa saber o preço total e o peso para o frete.

A primeira versão resolve com o que existe: um laço, um `isinstance` e outro laço por dentro.

**antes — uma escada de if e for, com o número de degraus fixado**

```python
def preco_do_carrinho(itens):
    total = 0
    for item in itens:
        if isinstance(item, Kit):
            parcial = 0
            for sub in item.itens:
                if isinstance(sub, Kit):
                    # kit dentro de kit: vale só até aqui
                    parcial += sum(p.preco for p in sub.itens) * (1 - sub.desconto)
                else:
                    parcial += sub.preco
            total += parcial * (1 - item.desconto)
        else:
            total += item.preco
    return total

def peso_do_carrinho(itens):
    # a mesma escada, de novo, com outro campo
    ...
```

Funciona até alguém montar um kit dentro de um kit dentro de um kit: aí `p.preco` cai em um `Kit` e dá `AttributeError`, ou pior, passa sem erro e soma errado. Cada operação nova (peso, lista de itens para a nota, estoque a reservar) reescreve a escada inteira, e o desconto do kit precisa ser lembrado em todas. A regra do "o que é um kit" está espalhada por todos os chamadores.

<a id="a-solucao"></a>
## A solução

Faça produto e kit responderem às mesmas perguntas. O kit guarda uma lista de itens *do mesmo tipo comum*, e responde pedindo a cada um deles. Os papéis são quatro:

| Papel | Quem é | No exemplo |
|---|---|---|
| Componente | A interface comum a folhas e grupos | `Item`, com `preco()` e `peso_kg()` |
| Folha | Um nó que não contém outros; faz o trabalho de verdade | `Produto` |
| Composto | Um nó que guarda componentes e responde combinando as respostas deles | `Kit` |
| Cliente | Quem usa o componente sem perguntar o que ele é | `Carrinho` |

O ponto é o **tipo dos filhos**: o kit guarda `Item`, não `Produto`. Por isso um filho pode ser outro kit, e a recursão acontece sozinha, em qualquer profundidade. O cliente nunca pergunta "é um kit?": o kit é quem sabe o que fazer com os filhos.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

# 1. o componente: o que qualquer item do carrinho sabe responder
class Item(ABC):
    @abstractmethod
    def preco(self) -> Decimal: ...

    @abstractmethod
    def peso_kg(self) -> float: ...

# 2. a folha: responde sozinha
@dataclass(frozen=True)
class Produto(Item):
    nome: str
    valor: Decimal
    peso: float

    def preco(self):
        return self.valor

    def peso_kg(self):
        return self.peso

# 3. o composto: guarda Item, e por isso aceita outro Kit
class Kit(Item):
    def __init__(self, nome: str, itens: list[Item], desconto: Decimal = Decimal("0")):
        self.nome, self._itens, self._desconto = nome, itens, desconto

    def preco(self):
        soma = sum((i.preco() for i in self._itens), Decimal(0))
        return soma * (1 - self._desconto)

    def peso_kg(self):
        return sum(i.peso_kg() for i in self._itens)

# 4. o cliente: não pergunta o que é cada item
class Carrinho:
    def __init__(self, itens: list[Item]):
        self._itens = itens

    def total(self):
        return sum((i.preco() for i in self._itens), Decimal(0))

combo = Kit("Combo Home Office", [
    Produto("Teclado", Decimal("250"), 0.9),
    Kit("Brinde", [Produto("Mousepad", Decimal("30"), 0.2)], Decimal("0.5")),
], Decimal("0.1"))
```

> **Dica.** O teste de `Kit` não precisa de catálogo nem de banco: uma árvore de três níveis cabe em quatro linhas, e dá para usar um `Item` falso que devolve valores fixos. Um kit com profundidade arbitrária é testado pelo mesmo caminho que um kit simples.

<a id="quando-usar"></a>
## Quando usar

O Composite vale quando três coisas acontecem ao mesmo tempo: os dados formam uma **árvore** (um todo que contém partes), os grupos podem conter outros grupos em uma **profundidade que você não controla**, e quem usa a estrutura quer **tratar um nó e um grupo da mesma forma**.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Quem usa a estrutura pergunta o tipo antes de agir | `isinstance(no, Pasta)` ou `instanceof` no começo de cada função que percorre a árvore | [Uso #1](uso.md#pastas-e-arquivos) |
| Várias operações percorrem a mesma árvore | A mesma escada de `for` + `if` reescrita para tamanho, busca, contagem | [Uso #1](uso.md#pastas-e-arquivos) |
| Condições que se combinam com E, OU e NÃO | Tipos como `"primeira_compra_e_valor_minimo"`; um `if` novo por combinação pedida | [Uso #2](uso.md#regras-combinaveis) |
| Uma função que atende "uma pessoa ou várias" | `if isinstance(destino, list)`; pares `enviar_para_um` e `enviar_para_varios` | [Uso #3](uso.md#um-ou-varios-destinatarios) |
| Filtrar uma árvore e depois limpar os pais vazios | Uma segunda passada para remover "grupos sem nada dentro" | [Uso #4](uso.md#menu-com-permissoes) |

> **Dica.** O que os sinais têm em comum: o cliente faz uma pergunta de tipo ("isto é um grupo?") antes de poder agir. O Composite move essa pergunta para dentro dos nós, onde cada um responde com o que sabe.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Um item contém outros itens do mesmo tipo?** Se é uma lista simples de coisas diferentes (um carrinho com produtos), não é parte-todo. Pare.
2. **A profundidade pode variar?** Se são sempre dois níveis (categoria e produto), duas classes com tipos diferentes dizem mais que uma interface comum.
3. **Folha e grupo respondem à mesma operação?** Se a pergunta só faz sentido em um deles, não há interface comum honesta.
4. **Mais de uma operação percorre a árvore, ou ela vem de dados?** Se é uma única função em um único lugar, uma recursão com `isinstance` é mais simples. Se são várias, ou a árvore é montada em tempo de execução, é Composite.

<a id="quando-nao-usar"></a>
## Quando não usar

O Composite tem um custo que não aparece de início: folha e grupo passam a compartilhar uma interface, e essa interface tende a engordar para caber nos dois. O tipo "tudo é um `Item`" também afrouxa o sistema de tipos: o compilador deixa de ajudar a separar o que é grupo do que é folha. E a recursão esconde o custo: um `preco()` na raiz percorre a árvore toda, e se for chamado em um laço, percorre de novo a cada volta.

| Situação | Por que não | Faça isto |
|---|---|---|
| Dois níveis fixos (categoria → produto) | Uma interface comum esconde uma diferença que o domínio tem de verdade | Duas classes e um laço dentro de outro |
| Uma única operação, em um único lugar | Uma função recursiva curta é mais fácil de ler que três classes | Recursão com `isinstance`. Extraia quando a segunda operação aparecer |
| Folha e grupo são muito diferentes | A interface comum vira uma lista de métodos que lançam `NotImplementedError` em um dos lados | Tipos separados; um Visitor, se as operações são muitas e a estrutura é estável |
| Os dados são um grafo (nó com dois pais, ciclos) | O Composite pressupõe árvore; a recursão conta duas vezes ou não termina | Modele o grafo, com um conjunto de visitados na travessia |
| Só precisa percorrer, sem operação nos nós | Não há comportamento para distribuir pelos nós | Um gerador (`yield from`) que devolve os nós em ordem |

<a id="sinais-de-abuso"></a>
### Sinais de que o Composite saiu do lugar

- **A interface base ganhou `adicionar` e `remover`.** A folha agora tem métodos que lançam erro. Quem monta a árvore trabalha com `Kit`; quem a usa vê só `Item`.
- **O cliente pergunta o tipo mesmo assim.** Um `isinstance(item, Kit)` depois do pattern mostra que a interface não cobre o que o cliente precisa.
- **Todo nó aponta para o pai.** O ponteiro "por garantia" cria ciclos, impede de compartilhar nós entre árvores e obriga a manter dois lados consistentes.
- **Uma operação cara na raiz, chamada em laço.** Calcular `preco()` do carrinho inteiro a cada renderização, sem guardar o resultado.
- **O composto tem regra de negócio que depende de qual filho está dentro.** Se o kit precisa saber que um filho é um produto específico, a abstração não está segurando.

> **Perigo.** O sinal mais comum: `Produto.adicionar()` existindo só para lançar uma exceção. A interface comum foi ampliada para que o código "fique uniforme", e a folha passou a mentir sobre o que sabe fazer.

> **Nota.** Na dúvida, comece com uma função recursiva. Ela é pequena, e promovê-la a Composite é uma refatoração mecânica quando a segunda operação precisar percorrer a mesma árvore.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Decorator | Tem a mesma estrutura (um objeto que guarda outro da mesma interface), mas embrulha *um só*, para acrescentar comportamento. O Composite guarda vários e combina as respostas deles |
| Iterator | Percorre a estrutura sem expor como ela é feita. O Composite é a própria estrutura, e os dois costumam andar juntos |
| Visitor | Tira as operações de dentro dos nós e as põe em um objeto separado. Serve ao Composite quando as operações mudam mais que os tipos de nó |
| [Chain of Responsibility](../../comportamentais/chain-of-responsibility/explicacao.md) | Passa o pedido adiante até alguém tratar. No Composite o pedido vai para *todos* os filhos, e o resultado é a combinação das respostas |

Regra prática: se o grupo guarda vários do mesmo tipo que ele e a resposta é a combinação das respostas dos filhos, é Composite; se o objeto embrulha um só para mudar o que ele faz, é Decorator.

<!-- Gerado de pages/clean-code/comportamentais/memento/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Memento — Explicação

*Clean Code / Design Pattern / Memento*

Como guardar o estado de um objeto para voltar a ele depois, sem deixar quem guarda saber o que tem dentro nem mexer nisso.

<a id="o-problema"></a>
## O problema

Você tem um orçamento com itens, desconto, cupom e frete. A pessoa mexe, não gosta do resultado e quer voltar ao que estava dois passos atrás. Para isso, alguém precisa lembrar **como o orçamento era**.

A saída preguiçosa é a tela copiar os campos que ela conhece, antes de cada alteração, e devolvê-los na hora de desfazer:

**antes — a tela copia e devolve campo por campo**

```python
class EditorDeOrcamento:
    def __init__(self, orcamento):
        self.orcamento = orcamento
        self._pilha = []

    def alterar(self, **campos):
        # copia "o que parece importar" antes de mexer
        self._pilha.append({
            "itens": list(self.orcamento.itens),
            "desconto": self.orcamento.desconto,
            "frete": self.orcamento.frete,
        })
        for nome, valor in campos.items():
            setattr(self.orcamento, nome, valor)

    def desfazer(self):
        antes = self._pilha.pop()
        self.orcamento.itens = antes["itens"]
        self.orcamento.desconto = antes["desconto"]
        self.orcamento.frete = antes["frete"]
        # e o cupom? e o total, que foi recalculado no meio?
```

Três coisas quebram daqui a pouco. Quando o `Orcamento` ganha um campo (o cupom, por exemplo), a tela não sabe, e o "desfazer" devolve um orçamento pela metade. Toda mudança interna do orçamento passa a exigir mexer na tela, porque o estado deixou de ser privado. E `list(itens)` é uma cópia rasa: a lista volta, mas os itens são os mesmos objetos, já alterados.

<a id="a-solucao"></a>
## A solução

Quem sabe o que compõe o estado é o próprio objeto, então é ele que tira a foto e é ele que a usa. Quem guarda a foto só a segura. São três papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Originador | O objeto cujo estado se guarda; só ele cria e lê a foto | `Orcamento` |
| Memento | A foto: um valor fechado, que não se edita depois de tirado | `_Foto` |
| Zelador | Guarda as fotos e decide quando voltar; nunca abre uma | `Historico` |

O ponto é a fronteira: a foto atravessa o zelador sem ser aberta. Quem a produz e quem a consome é a mesma classe, e é por isso que o orçamento pode ganhar um campo sem que a tela, o histórico ou o teste percebam.

<a id="implementacao"></a>
## Implementação

```python
from collections import deque
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Item:
    produto: str
    quantidade: int
    preco: Decimal

# 1. o memento: uma foto fechada; frozen, ninguém edita depois de tirada
@dataclass(frozen=True)
class _Foto:
    itens: tuple[Item, ...]
    desconto: Decimal
    cupom: str | None
    frete: Decimal

# 2. o originador: só ele sabe tirar a foto, e só ele sabe usá-la
class Orcamento:
    def __init__(self):
        self._itens: list[Item] = []
        self._desconto = Decimal("0")
        self._cupom: str | None = None
        self._frete = Decimal("0")

    def salvar(self) -> _Foto:
        return _Foto(tuple(self._itens), self._desconto, self._cupom, self._frete)

    def restaurar(self, foto: _Foto) -> None:
        self._itens = list(foto.itens)
        self._desconto = foto.desconto
        self._cupom = foto.cupom
        self._frete = foto.frete

# 3. o zelador: guarda as fotos e decide quando voltar; nunca abre uma
class Historico:
    def __init__(self, orcamento: Orcamento, limite: int = 50):
        self._orcamento = orcamento
        self._passado: deque = deque(maxlen=limite)
        self._futuro: list = []

    def antes_de_alterar(self):
        self._passado.append(self._orcamento.salvar())
        self._futuro.clear()

    def desfazer(self):
        if self._passado:
            self._futuro.append(self._orcamento.salvar())
            self._orcamento.restaurar(self._passado.pop())

    def refazer(self):
        if self._futuro:
            self._passado.append(self._orcamento.salvar())
            self._orcamento.restaurar(self._futuro.pop())
```

> **Dica.** O teste do histórico não precisa conhecer um campo sequer: `antes = orcamento.salvar()`, uma alteração qualquer, `orcamento.restaurar(antes)` e a comparação do que o orçamento mostra por fora. Se alguém esquecer um campo em `salvar`, é **este** teste, em um lugar só, que acusa.

<a id="quando-usar"></a>
## Quando usar

O Memento vale quando três coisas acontecem ao mesmo tempo: alguém precisa **voltar** a um estado em que o objeto já esteve; o estado é **interno** do objeto, então quem guarda não deveria conhecê-lo; e guardar a foto inteira é **mais simples** do que escrever o inverso de cada operação.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Desfazer e refazer em um objeto com muito estado | Um `_anterior = {…}` na tela, copiando campo a campo; um `desfazer` que reatribui cada campo; um campo novo que ninguém lembrou de copiar | [Uso #1](uso.md#historico-do-editor) |
| Calcular "e se…" sem alterar de verdade | Um `simular_x()` que repete as regras de `aplicar_x()`; `deepcopy(obj)` espalhado antes de "tentar" | [Uso #2](uso.md#simular-e-decidir) |
| Retomar depois de fechar a tela ou o programa | Uma série de `localStorage.setItem` com um campo por chave; `json.dumps(obj.__dict__)` com os campos listados à mão | [Uso #3](uso.md#rascunho-que-sobrevive) |
| Tentar um caminho e voltar se não der | `pos_salva = self.pos` … `self.pos = pos_salva`, repetido em cada alternativa, e cada vez com um campo a mais | [Uso #4](uso.md#tentar-e-voltar) |
| Código de fora que restaura mexendo no que é privado | `obj._campo = valor` fora da classe; `setattr` em laço sobre o `__dict__` | [Uso #1](uso.md#historico-do-editor) |

> **Dica.** O que os sinais têm em comum: alguém de fora do objeto está copiando ou devolvendo os campos dele. O Memento muda essa tarefa para dentro do objeto, e deixa para fora só o ato de guardar e de pedir de volta.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Alguém vai mesmo voltar a esse estado?** Se o que se quer é saber o que aconteceu (auditoria, quem mudou o quê), registre o evento, não o estado.
2. **O estado é um valor pequeno e imutável?** Se o objeto inteiro é uma tupla, um número ou um `dataclass(frozen=True)`, a referência antiga já é a foto. Guarde-a.
3. **O inverso de cada operação é curto e simples de escrever?** Se são três ações e cada uma tem uma volta óbvia, um Command com `desfazer` custa menos que manter fotos.
4. **Quem guarda precisaria conhecer ou editar os campos?** Se sim, é Memento: a foto sai do objeto fechada e volta fechada.

<a id="quando-nao-usar"></a>
## Quando não usar

O Memento tem um custo fixo e um custo que cresce. O fixo: `salvar` e `restaurar` precisam acompanhar o objeto, e um campo esquecido não dá erro, só não volta. O que cresce: cada foto ocupa memória, e o histórico pode crescer sem ninguém ver.

| Situação | Por que não | Faça isto |
|---|---|---|
| O estado é um valor imutável e pequeno | A variável antiga já é a foto; a classe a mais só repassa | Guarde a referência, em uma lista |
| Desfazer precisa reverter efeitos de fora (e-mail enviado, cobrança, estoque reservado) | A foto restaura a memória; o mundo continua do jeito que ficou | Command com uma ação de compensação, ou uma transação do banco |
| O objeto é enorme e muda um pedacinho por vez | Uma cópia inteira por passo estoura a memória | Command guardando só a diferença; ou fotos de tempos em tempos |
| Você quer saber quem mudou o quê e quando | Uma foto não conta a história, só o resultado | Um log de eventos (Event Sourcing) |
| A persistência já é um banco com transações | O rollback já existe, e é mais correto que o seu | Use a transação |

<a id="sinais-de-abuso"></a>
### Sinais de que o Memento saiu do lugar

- **A foto tem getters públicos e o zelador os usa.** Se o `Historico` lê `foto.desconto` para decidir algo, a foto virou um DTO e o encapsulamento que justificava o pattern foi embora.
- **A foto é mutável, ou a cópia é rasa.** Itens compartilhados entre a foto e o objeto vivo mudam por baixo. O "desfazer" devolve a lista que já foi alterada.
- **O histórico não tem limite.** Uma foto por tecla digitada, guardada para sempre, é um vazamento de memória com nome de funcionalidade.
- **A foto guarda o que dá para recalcular.** Totais, caches e índices pertencem ao `restaurar`, que os recalcula. Guardá-los na foto é deixá-los envelhecer.
- **Restaura sem avisar quem depende do objeto.** Se a tela, um listener ou um cache ficaram olhando para o estado velho, o objeto volta e eles não.

> **Perigo.** O sinal mais comum: a cópia rasa. A foto guarda a *mesma* lista que o objeto vivo continua usando, então o "desfazer" restaura um estado que já foi mexido. Em um teste com um item só, parece funcionar.

> **Nota.** Na dúvida, comece com um valor imutável e uma lista dele. O Memento aparece quando o estado tem campos privados que não deveriam sair de lá. Nesse ponto a refatoração é pequena: o que você já copiava vira `salvar` e `restaurar`.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Command](../command/explicacao.md) | Guarda a *operação* e como revertê-la; o Memento guarda o *estado* e volta a ele. Aparecem juntos quando o comando guarda uma foto para saber como desfazer |
| Prototype | Copia um objeto para criar *outro*, independente; o Memento copia para devolver o *mesmo* objeto a um estado antigo |
| State | Troca o comportamento de acordo com o estado atual; o Memento não decide nada, só guarda e devolve |
| Event Sourcing | Guarda a sequência de mudanças e reconstrói o estado a partir delas; o Memento guarda o resultado e esquece o caminho |

Regra prática: se o objeto que volta é o mesmo que saiu, e quem guardou nunca olhou dentro, é Memento.

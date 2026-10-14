<!-- Gerado de pages/clean-code/comportamentais/state/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# State — Explicação

*Clean Code / Design Pattern / State*

Como fazer um objeto que se comporta de um jeito em cada fase da vida dele sem encher todos os métodos de `if` sobre em qual fase ele está.

<a id="o-problema"></a>
## O problema

Um pedido passa por fases: nasce como rascunho, é pago, é enviado, é entregue. Também pode ser cancelado, mas cancelar um rascunho não custa nada, cancelar um pedido pago exige estorno, e cancelar um pedido que já foi enviado nem é permitido.

A saída preguiçosa é guardar a fase em um texto e conferi-la dentro de cada método:

**antes — a mesma escada de if em cada operação**

```python
class Pedido:
    def __init__(self):
        self.status = "rascunho"

    def pagar(self):
        if self.status == "rascunho":
            self.status = "pago"
        else:
            raise ValueError(f"não dá para pagar um pedido {self.status}")

    def enviar(self):
        if self.status == "pago":
            self.status = "enviado"
        else:
            raise ValueError(f"não dá para enviar um pedido {self.status}")

    def cancelar(self):
        if self.status == "rascunho":
            self.status = "cancelado"
        elif self.status == "pago":
            self._estornar()
            self.status = "cancelado"
        elif self.status in ("enviado", "entregue"):
            raise ValueError("o pedido já saiu; abra uma devolução")
        # e "cancelado"? cancelar de novo cai aqui sem fazer nada, e sem avisar
```

Três coisas quebram daqui a pouco. Uma fase nova, como "em separação", obriga a abrir todos os métodos e achar o lugar certo em cada escada. As regras de transição não estão em lugar nenhum: para saber de onde se chega a `cancelado`, é preciso ler o arquivo inteiro. E um erro de digitação em `"enviado"` não falha; só faz um `if` nunca ser verdadeiro.

<a id="a-solucao"></a>
## A solução

Faça cada fase virar um objeto. O pedido guarda o objeto da fase atual e **delega** a ele o que fazer. Cada fase sabe o que permite, o que recusa e para qual fase o pedido vai depois. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Contexto | O objeto que muda de comportamento; guarda o estado atual e delega | `Pedido` |
| Estado | A interface: todas as operações que dependem da fase | `Estado` |
| Estados concretos | Uma fase: o que ela permite, recusa e qual é a próxima | `Rascunho`, `Pago`, `Enviado`… |
| Cliente | Usa o contexto, sem saber em que fase ele está | O checkout, a API |

O ponto é para onde foi o `if`. Em vez de uma escada em cada método ("em qual fase estou?"), há uma escolha, feita uma vez, de qual objeto está ativo. O polimorfismo faz o resto. Uma operação que a fase não permite simplesmente não está implementada nela, e a recusa fica no padrão da interface.

<a id="implementacao"></a>
## Implementação

```python
class TransicaoInvalida(Exception): ...

# 1. o estado: toda operação do pedido, recusada por padrão
class Estado:
    def pagar(self, pedido):    self._recusar("pagar")
    def enviar(self, pedido):   self._recusar("enviar")
    def entregar(self, pedido): self._recusar("entregar")
    def cancelar(self, pedido): self._recusar("cancelar")

    def _recusar(self, operacao):
        raise TransicaoInvalida(f"{operacao}, em {type(self).__name__}")

# 2. os estados concretos: cada um só escreve o que permite
class Rascunho(Estado):
    def pagar(self, pedido):    pedido.ir_para(Pago())
    def cancelar(self, pedido): pedido.ir_para(Cancelado())

class Pago(Estado):
    def enviar(self, pedido):   pedido.ir_para(Enviado())

    def cancelar(self, pedido):
        pedido.estornar()
        pedido.ir_para(Cancelado())

class Enviado(Estado):
    def entregar(self, pedido): pedido.ir_para(Entregue())

class Entregue(Estado): ...
class Cancelado(Estado): ...

# 3. o contexto: guarda o estado atual e delega
class Pedido:
    def __init__(self):
        self._estado = Rascunho()

    def ir_para(self, estado):
        self._estado = estado

    def estornar(self): ...

    def pagar(self):    self._estado.pagar(self)
    def enviar(self):   self._estado.enviar(self)
    def entregar(self): self._estado.entregar(self)
    def cancelar(self): self._estado.cancelar(self)

    @property
    def status(self):
        return type(self._estado).__name__.lower()

# 4. o cliente: pede a operação, sem perguntar em que fase está
pedido = Pedido()
pedido.pagar()
pedido.cancelar()      # estorna, porque está em Pago
```

> **Dica.** O teste de uma fase é uma classe e uma chamada: `Pago().enviar(pedido)` e confira para onde o pedido foi. Uma fase nova, como "em separação", é uma classe nova e uma linha em `Pago` que aponta para ela; nenhuma outra fase é aberta.

<a id="quando-usar"></a>
## Quando usar

O State vale quando três coisas acontecem ao mesmo tempo: o comportamento do objeto **depende de uma fase** que muda ao longo da vida dele; há **várias fases**, cada uma com comportamento próprio; e a pergunta "em que fase estou?" aparece em **mais de um método**.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| A mesma escada de `if` sobre a fase em vários métodos | `if self.status == …` / `elif` repetido no começo de cada operação, como o `pagar` e o `cancelar` acima | O exemplo desta página |
| O mesmo gesto faz coisas diferentes conforme o modo | `switch (ferramenta)` dentro de cada um dos handlers de mouse ou de teclado | [Uso #1](uso.md#ferramenta-ativa) |
| Flags booleanas que juntas descrevem a fase | `self.aberto`, `self.meio_aberto` e `self.falhas`, em que algumas combinações não deveriam existir | [Uso #2](uso.md#disjuntor) |
| Algo precisa acontecer toda vez que se entra ou se sai de uma fase | Um `timer.cancel()` ou uma limpeza copiada em cada método que muda `status`, e esquecida em um | [Uso #3](uso.md#reserva-com-prazo) |
| As transições não estão escritas em lugar nenhum | Para descobrir de onde se chega a `cancelado`, é preciso ler todos os métodos | O exemplo desta página |

> **Dica.** O que os sinais têm em comum: a pergunta "em que fase estou?" é feita por quem não deveria precisar fazê-la. O State é o lugar para onde a resposta se muda, para os métodos só pedirem a operação.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **O objeto muda de comportamento ao longo da vida?** Se ele se comporta sempre do mesmo jeito, não há fase para modelar.
2. **Há mais de duas ou três fases?** Com duas, um booleano e um `if` resolvem, e as classes não se pagam.
3. **A diferença aparece em mais de uma operação, ou há algo a fazer ao entrar e sair?** Se só uma decisão depende da fase, um `if` naquele ponto basta.
4. **Cada fase tem um *comportamento* próprio, e não só "pode" ou "não pode"?** Se a fase só decide quais transições valem, uma tabela de transições é mais curta. O State vale quando há o que fazer.

<a id="quando-nao-usar"></a>
## Quando não usar

O custo do State é uma classe por fase, e o fluxo inteiro deixa de caber em uma tela. As transições ficam espalhadas, cada uma dentro da fase de onde sai, então ver o "diagrama" de estados exige abrir várias classes. Com muitas fases pequenas, o objeto se pulveriza em arquivos de três linhas, e o ganho de clareza some.

| Situação | Por que não | Faça isto |
|---|---|---|
| Duas fases (ligado e desligado, aberto e fechado) | Duas classes para um booleano | Um `bool` e um `if` |
| As fases só definem quais transições são válidas | Não há comportamento por fase, só permissão | Um `enum` e um dicionário de transições |
| A fase é só um rótulo para exibir | Nada muda no comportamento em função dela | Um campo `status` |
| O comportamento é escolhido de fora, e não muda por transições | O que varia é o algoritmo, não a fase de vida | Strategy |
| Fluxo longo, com muitas transições, ou vindo de configuração | As classes viram uma máquina de estados escrita à mão | Uma biblioteca de máquina de estados ou de workflow |

<a id="sinais-de-abuso"></a>
### Sinais de que o State saiu do lugar

- **O cliente pergunta a fase.** Um `if pedido.status == "pago"` antes de chamar `cancelar()` traz a escada de volta, agora fora do objeto, e as duas regras divergem.
- **Os estados vazios.** Classes com `pass` em tudo, diferentes só pelo nome, mostram que um `enum` bastava.
- **As fases se conhecem em malha.** Cada estado cria os outros estados concretos, e acrescentar uma fase obriga a abrir várias. Se isso dói, centralize as transições.
- **O estado copia dados do contexto.** Campos duplicados entre o estado e o pedido saem de sincronia. O estado deve guardar só o que é dele.
- **Transições sem evento.** Um estado que decide sozinho, sem que ninguém peça, para onde ir é uma máquina que roda por conta própria e ninguém sabe quando.

> **Perigo.** O sinal mais comum: o `if pedido.status == …` reaparece na tela e na API, para decidir o que oferecer. O estado deixou de ser a única fonte de verdade, e a regra de "o que vale agora" passa a existir em três versões.

> **Nota.** Na dúvida, comece com um `enum` e um `if`. Extraia os estados quando a segunda ou a terceira operação precisar da mesma escada: nesse ponto as fases já existem no código, e é só dar a cada uma um nome e um lugar.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Strategy | Tem a mesma forma (um contexto delega a um objeto trocável), mas quem troca é o cliente, de fora, e as opções não se conhecem. No State, o próprio objeto troca de fase, e cada fase sabe qual é a próxima |
| [Observer](../observer/explicacao.md) | Avisa quem estiver interessado de que a fase mudou. O State é quem decide o que fazer em cada fase, e os dois aparecem juntos |
| [Memento](../memento/explicacao.md) | Guarda os dados de um objeto para voltar a eles depois. O State guarda *comportamento*; não guarda uma foto |
| Máquina de estados em tabela | Não é do catálogo GoF: um `enum` e um dicionário de transições. Serve quando as fases só definem o que é permitido, sem comportamento próprio |

Regra prática: se o objeto troca sozinho de objeto de comportamento, conforme a vida dele avança, é State. Se alguém de fora escolhe qual objeto usar, é Strategy.

<!-- Gerado de pages/clean-code/interface-segregation.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Interface Segregation

*Clean Code / SOLID / Interface Segregation*

Como evitar que uma classe seja obrigada a implementar, e quem a usa a conhecer, métodos que não têm nada a ver com o que ela faz.

<a id="o-problema"></a>
## O problema

Uma empresa tem uma interface `Multifuncional` com `imprimir`, `escanear` e `enviar_fax`. Faz sentido para a máquina grande do escritório. Aí compram uma impressora simples, que só imprime, e ela precisa "implementar" a interface inteira.

**antes — uma interface larga demais para quem implementa**

```python
class Multifuncional(ABC):
    @abstractmethod
    def imprimir(self, doc): ...
    @abstractmethod
    def escanear(self) -> bytes: ...
    @abstractmethod
    def enviar_fax(self, doc, numero): ...

class ImpressoraSimples(Multifuncional):
    def imprimir(self, doc):
        ...                                    # esse faz
    def escanear(self):
        raise NotImplementedError             # esses dois ela nunca vai fazer
    def enviar_fax(self, doc, numero):
        raise NotImplementedError

def imprimir_relatorio(maquina: Multifuncional):   # só usa imprimir()
    maquina.imprimir(relatorio)
```

Dois males andam juntos. Do lado de quem implementa: métodos que lançam erro ou ficam vazios, o que já é uma violação de [Liskov](liskov-substitution.md). Do lado de quem usa: `imprimir_relatorio` declara que precisa de uma máquina completa, e para testá-la você monta um falso com três métodos, dois deles sem uso.

<a id="a-ideia"></a>
## A ideia

Ninguém deve ser forçado a depender de métodos que não usa. Em vez de uma interface grande para todos, **várias pequenas**, cada uma desenhada pelo que quem *usa* precisa, não pelo que quem implementa consegue.

| Quem | Precisa de | Interface |
|---|---|---|
| Rotina de relatório | Só imprimir | `Impressora` |
| Rotina de digitalização | Só escanear | `Scanner` |
| Máquina grande | Os dois, e o fax | Implementa as três |

O ponto é de que lado se desenha. Quem implementa pode juntar quantas interfaces quiser; quem usa pede só a fatia que precisa.

<a id="depois"></a>
## Como fica

```python
from typing import Protocol

# 1. uma interface por capacidade
class Impressora(Protocol):
    def imprimir(self, doc) -> None: ...

class Scanner(Protocol):
    def escanear(self) -> bytes: ...

# 2. cada classe faz só o que sabe fazer
class ImpressoraSimples:
    def imprimir(self, doc): ...

class MaquinaDoEscritorio:
    def imprimir(self, doc): ...
    def escanear(self): ...

# 3. quem usa pede só a fatia de que precisa
def imprimir_relatorio(impressora: Impressora):
    impressora.imprimir(relatorio)
```

> **Dica.** O teste de `imprimir_relatorio` agora recebe um falso de uma linha: qualquer objeto com `imprimir`. Um bom sinal de que a interface está do tamanho certo é o falso do teste caber em uma tela.

> **Nota.** Em Python, com *duck typing*, o `Protocol` não obriga ninguém a nada em tempo de execução; ele serve para a leitura e para o verificador de tipos. O princípio vale igual: a assinatura de `imprimir_relatorio` diz, a quem a lê, do que ela depende de verdade.

<a id="como-reconhecer"></a>
## Como reconhecer a violação

| Sintoma | O que está acontecendo |
|---|---|
| Implementações com métodos que só lançam `NotImplementedError` ou ficam vazios | A interface pede mais do que a classe consegue honrar |
| Interface com 8 ou 10 métodos, e cada cliente usa dois | Vários papéis foram colados em um nome só |
| Falso de teste enorme, quase todo `pass` | O teste precisa fingir o que não usa |
| Mudança num método que ninguém chama quebra o build de quem implementa | Dependência por conveniência, não por necessidade |
| Parâmetro tipado como o serviço inteiro, usado para um único método | Quem chama depende do mundo para usar um pedaço |

<a id="quando-nao-aplicar"></a>
## Quando não aplicar

Segregar demais cria o problema oposto: dezenas de interfaces de um método, nomes difíceis de achar e um construtor que recebe seis delas. O custo é o de navegação.

| Situação | Por que não | Faça isto |
|---|---|---|
| Todos os clientes usam todos os métodos juntos | A interface já é coesa; dividir só obriga a pedir três coisas em vez de uma | Mantenha uma interface |
| Uma única implementação e um único cliente | Nada está sendo forçado a depender do que não usa | Espere o segundo cliente com necessidades diferentes |
| A interface é de uma biblioteca que você não controla | Não dá para dividir o que não é seu | Declare, do seu lado, a fatia que usa; é o [Adapter](estruturais/adapter/explicacao.md) |

> **Perigo.** Sinal de exagero: uma interface por método, com nome de verbo (`Imprimivel`, `Escaneavel`, `Faxavel`) e classes que implementam cinco delas sempre em conjunto. Se elas andam sempre juntas, são uma interface só.

<a id="relacao"></a>
## Relação com os outros

Interface Segregation é a prevenção natural do [Liskov](liskov-substitution.md): se ninguém é obrigado a assinar o que não cumpre, ninguém lança `NotImplementedError`. Ela também alimenta o [Dependency Inversion](dependency-inversion.md), porque abstrações pequenas e orientadas a quem usa são as mais fáceis de inverter. E o [Facade](estruturais/facade/explicacao.md) faz o movimento contrário, de propósito: junta uma interface grande em uma porta simples para quem não quer ver o detalhe.

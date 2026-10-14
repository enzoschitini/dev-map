<!-- Gerado de pages/clean-code/open-closed.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Open/Closed

*Clean Code / SOLID / Open/Closed*

Como acrescentar um caso novo escrevendo código novo, sem reabrir e retestar o código que já funcionava.

<a id="o-problema"></a>
## O problema

Um e-commerce calcula o frete por transportadora. No começo são duas, e um `if` resolve. A cada transportadora nova alguém abre a mesma função, acrescenta um `elif` e reza para não ter quebrado as outras.

**antes — cada transportadora nova reabre a função**

```python
def calcular_frete(pedido, transportadora):
    if transportadora == "correios":
        return 12 + pedido.peso * 2.5
    elif transportadora == "jadlog":
        return 9 + pedido.peso * 3
    elif transportadora == "retirada":
        return 0
    # e a próxima? mais um elif, na mesma função, testada junto com as outras
    raise ValueError(transportadora)
```

Adicionar um caso exige **editar** código que já está em produção e já foi testado. Todo teste das outras transportadoras volta a ser candidato a quebrar. E o mesmo `if transportadora ==` costuma aparecer copiado em outros lugares (prazo, rastreio, etiqueta), então "adicionar uma" vira "achar todos os ifs".

<a id="a-ideia"></a>
## A ideia

O código deve ser **aberto para extensão** e **fechado para modificação**: o comportamento novo entra como código novo, e o que já existia continua intocado. Para isso, o que varia vira uma abstração, e cada variação, uma implementação separada.

| Peça | Papel | No exemplo |
|---|---|---|
| Ponto de extensão | A abstração que diz o que cada variação faz | `Frete` |
| Variações | Uma implementação por caso | `FreteCorreios`, `FreteJadlog`, `Retirada` |
| Código fechado | Quem usa a abstração, sem conhecer os casos | `calcular_frete` |

O ponto é identificar *o eixo que varia*. Aqui é "como cada transportadora calcula". O que não varia (receber pedido, devolver número) fica fechado; o que varia fica atrás da abstração.

<a id="depois"></a>
## Como fica

```python
from abc import ABC, abstractmethod

# 1. o ponto de extensão
class Frete(ABC):
    @abstractmethod
    def calcular(self, pedido) -> float: ...

# 2. uma classe por variação — cada nova é um arquivo novo
class FreteCorreios(Frete):
    def calcular(self, pedido):
        return 12 + pedido.peso * 2.5

class FreteJadlog(Frete):
    def calcular(self, pedido):
        return 9 + pedido.peso * 3

class Retirada(Frete):
    def calcular(self, pedido):
        return 0

# 3. o código fechado: não muda quando surge a quarta opção
def cobrar_frete(pedido, frete: Frete):
    return frete.calcular(pedido)
```

> **Nota.** Em algum lugar ainda existe a escolha de qual classe usar. Ela só **muda de endereço**: sai de dentro da regra e vai para a borda do sistema (configuração, um mapa de nome para classe, o container de dependências). Aí o `if` tem um lugar só, e ele não é regra de negócio.

<a id="como-reconhecer"></a>
## Como reconhecer a violação

| Sintoma | O que está acontecendo |
|---|---|
| `if tipo == …` / `switch (tipo)` repetido em mais de um lugar | O mesmo eixo de variação está espalhado; cada caso novo toca todos os pontos |
| Histórico do `git` mostrando "adiciona X" sempre editando a mesma função | A função é o ponto de extensão, mas sem abstração nenhuma |
| Enum que cresce junto com cada `switch` que o usa | O enum virou uma lista de casos que ninguém pode esquecer |
| Medo de mexer: "se eu tocar aqui, quebra o outro cliente" | Casos diferentes compartilham código que não deveriam |

<a id="quando-nao-aplicar"></a>
## Quando não aplicar

A abstração custa: uma interface a mais e uma indireção para ler. Só compensa depois que você **viu a variação acontecer**. Antes disso, você está chutando o eixo certo, e uma abstração no eixo errado é pior que um `if`.

| Situação | Por que não | Faça isto |
|---|---|---|
| Há dois casos e nada indica um terceiro | Duas classes e uma interface para substituir um `if` de três linhas | Mantenha o `if`; extraia no terceiro caso |
| A variação é uma regra de negócio que muda junto, não um caso novo | Não é extensão, é correção; abrir o código é o certo | Edite a regra e atualize os testes |
| Você não sabe ainda qual é o eixo | A abstração nasce no lugar errado e vira peso | Espere a segunda mudança e deixe o padrão aparecer |

> **Perigo.** O exagero comum: interface com uma implementação só, "para estender no futuro". Se o futuro não chegou depois de seis meses, a interface é só um arquivo a mais para abrir antes de chegar ao código.

<a id="relacao"></a>
## Relação com os outros

Open/Closed é o princípio por trás de vários padrões. O exemplo acima é o [Strategy](comportamentais/strategy/explicacao.md) quase sem disfarce. O [Decorator](estruturais/decorator/explicacao.md) acrescenta comportamento por embrulho, sem mexer no objeto. O [Template Method](comportamentais/template-method/explicacao.md) fecha a ordem dos passos e abre cada passo. Para que as variações sejam trocáveis de verdade, elas precisam respeitar o [Liskov](liskov-substitution.md).

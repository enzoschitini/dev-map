<!-- Gerado de pages/clean-code/comportamentais/strategy/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Strategy — Explicação

*Clean Code / Design Pattern / Strategy*

Como trocar o jeito de fazer uma coisa sem mexer em quem a pede, e sem um `if` novo a cada jeito que aparece.

<a id="o-problema"></a>
## O problema

O fechamento do mês calcula a comissão de cada venda. Só que a regra muda: no primeiro trimestre vale um percentual fixo, no segundo uma tabela por faixa de valor, e para uma campanha especial entra um bônus por meta batida. O fechamento é sempre o mesmo; o **jeito de calcular** é que varia.

A saída preguiçosa é um `if` que escolhe a regra dentro do próprio cálculo:

**antes — toda regra nova abre o mesmo método**

```python
class Fechamento:
    def comissao_de(self, venda, regra):
        if regra == "percentual":
            return venda.total * Decimal("0.05")
        elif regra == "escalonada":
            if venda.total <= 1000:
                return venda.total * Decimal("0.03")
            elif venda.total <= 5000:
                return venda.total * Decimal("0.05")
            return venda.total * Decimal("0.07")
        elif regra == "meta":
            base = venda.total * Decimal("0.04")
            if venda.total >= venda.meta_do_mes:
                base += Decimal("500")
            return base
        raise ValueError(f"regra desconhecida: {regra}")
```

Três coisas quebram daqui a pouco. Cada campanha nova exige abrir um método que também calcula todas as outras, o que fere o Open/Closed: para *acrescentar* um jeito, você *modifica* o código. Uma taxa que muda é uma edição no meio de um `if` aninhado, ao lado de regras que nada têm a ver com ela. E testar uma regra passa pelo método inteiro, com um texto no meio que alguém vai digitar errado.

<a id="a-solucao"></a>
## A solução

Cada jeito de calcular vira um objeto com a mesma interface, e quem precisa do cálculo recebe o objeto em vez de um texto. São três papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Estratégia | A interface: o que o contexto precisa, e nada mais | `RegraDeComissao` |
| Estratégia concreta | Um jeito de fazer, sem conhecer o contexto | `Percentual`, `Escalonada`, `PorMeta` |
| Contexto | Quem usa a estratégia, sem saber qual é | `Fechamento` |

O ponto é quem escolhe. O contexto não decide qual regra usar: ele **recebe** uma pronta. A escolha sobe para o lugar que monta o sistema, onde ela é uma linha de configuração em vez de uma ramificação no meio do cálculo.

<a id="implementacao"></a>
## Implementação

```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

@dataclass(frozen=True)
class Venda:
    vendedor: str
    total: Decimal
    meta_do_mes: Decimal

# 1. a estratégia: o que o fechamento precisa, e nada mais
class RegraDeComissao(Protocol):
    def calcular(self, venda: Venda) -> Decimal: ...

# 2. as estratégias concretas: um jeito cada, sem conhecer o fechamento
class Percentual:
    def __init__(self, taxa: Decimal):
        self._taxa = taxa

    def calcular(self, venda):
        return venda.total * self._taxa

class Escalonada:
    def __init__(self, faixas: list[tuple[Decimal, Decimal]]):
        self._faixas = faixas  # [(limite, taxa), ...] em ordem crescente

    def calcular(self, venda):
        for limite, taxa in self._faixas:
            if venda.total <= limite:
                return venda.total * taxa
        raise ValueError("a última faixa precisa ter teto infinito")

class PorMeta:
    def __init__(self, taxa: Decimal, bonus: Decimal):
        self._taxa, self._bonus = taxa, bonus

    def calcular(self, venda):
        comissao = venda.total * self._taxa
        if venda.total >= venda.meta_do_mes:
            comissao += self._bonus
        return comissao

# 3. o contexto: usa uma regra, e não sabe qual
class Fechamento:
    def __init__(self, regra: RegraDeComissao):
        self._regra = regra

    def comissao_de(self, venda: Venda) -> Decimal:
        return self._regra.calcular(venda).quantize(Decimal("0.01"))

# a escolha acontece na montagem, em uma linha
fechamento = Fechamento(Escalonada([
    (Decimal("1000"), Decimal("0.03")),
    (Decimal("5000"), Decimal("0.05")),
    (Decimal("Infinity"), Decimal("0.07")),
]))
```

> **Dica.** Testar a `Escalonada` é chamar `calcular` com vendas de 999, 1000 e 1001: sem fechamento, sem texto de regra, sem nada no caminho. E o teste do `Fechamento` usa uma regra de uma linha que devolve sempre 10, porque ele só quer saber se o arredondamento acontece.

<a id="quando-usar"></a>
## Quando usar

O Strategy vale quando três coisas acontecem ao mesmo tempo: existe **mais de um jeito** de fazer a mesma coisa, com a mesma entrada e o mesmo tipo de saída; a escolha de qual jeito usar **vem de fora** (usuário, configuração, contexto), e não do tipo do objeto; e quem usa o resultado **não deve saber** qual jeito foi usado.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um texto ou enum escolhe o algoritmo | `if ordem == "preco"` … `elif ordem == "nota"` …, e cada opção nova da tela é um `elif` | [Uso #1](uso.md#ordenacao-escolhida) |
| O mesmo resultado, com custos diferentes | `if len(dados) > LIMITE` trocando de implementação dentro da função, ou um booleano como `tempo_real=True` | [Uso #2](uso.md#custo-diferente) |
| Um laço com uma política dentro | `time.sleep(2 ** tentativa)` e `range(8)` escritos no meio do laço, copiados com números diferentes | [Uso #3](uso.md#politica-de-retentativa) |
| Teste que dorme, sorteia ou depende do relógio | `time.sleep`, `random` ou `datetime.now()` chamados direto dentro da regra; o teste demora ou falha de vez em quando | [Uso #3](uso.md#politica-de-retentativa) |
| Regra que muda por cliente e hoje exige deploy | `if cliente.id == 42`, ou um `dict` de parâmetros lido por dentro da regra | [Uso #4](uso.md#regra-do-cadastro) |
| Uma função cheia de parâmetros de "modo" | `calcular(venda, com_bonus=True, arredondar=False, tabela="2024")` | — |

> **Dica.** O que os sinais têm em comum: uma *decisão* misturada com a *execução*. O `if` que escolhe e o código que faz estão no mesmo lugar. O Strategy os separa, e a decisão vira um valor que se passa.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Existe mais de um jeito de verdade?** Se há um só hoje e nenhum à vista, escreva a função direto.
2. **Os jeitos recebem as mesmas entradas e devolvem o mesmo tipo de resultado?** Se não, não são intercambiáveis. Provavelmente são coisas diferentes com o mesmo verbo.
3. **A escolha é fixa por tipo, para sempre?** Se um `Boleto` sempre calcula de um jeito e um `Cartao` de outro, é polimorfismo comum: um método em cada classe.
4. **A escolha vem de fora e pode mudar sem mexer na classe?** Usuário, configuração, tamanho dos dados. Se sim, é Strategy.

<a id="quando-nao-usar"></a>
## Quando não usar

O Strategy tem um custo fixo: uma interface e uma classe por variante, e a lógica deixa de estar à vista. Para entender "como a comissão é calculada" você abre um arquivo, depois outro, e ainda precisa achar onde a regra é escolhida. Ele só se paga quando a variação é real.

| Situação | Por que não | Faça isto |
|---|---|---|
| Só há um jeito, ou dois que não vão mudar | Uma interface e duas classes para o que cabe em um `if` de três linhas | Fique com o `if`. Extraia quando aparecer o terceiro jeito, ou quando a escolha vier de fora |
| Cada variante é uma função pequena e sem estado | A classe é cerimônia em torno de um método | Passe a própria função (`Callable` no Python, arrow function no TypeScript) |
| A variação é fixa por tipo | O polimorfismo da linguagem já escolhe o método certo | Um método em cada subclasse |
| O objeto muda de comportamento conforme o próprio estado | Quem decide é o objeto, ao passar de um estado para outro, e não quem o chama | [State](../state/explicacao.md) |
| Você quer acrescentar cache, log ou limite sem trocar o algoritmo | O jeito de fazer continua o mesmo; o que muda é o que o envolve | Decorator |
| As variantes diferem em um número | Uma classe por taxa duplica a estrutura inteira para variar um valor | Um parâmetro no construtor |

<a id="sinais-de-abuso"></a>
### Sinais de que o Strategy saiu do lugar

- **A estratégia mexe no contexto.** Se `calcular` chega em `self._contexto._campo`, ela deixou de ser intercambiável: só funciona ao lado daquele contexto.
- **O `if` só mudou de lugar.** Uma estratégia com `if tipo == …` dentro escondeu a ramificação, e o problema original continua inteiro.
- **Quem usa pergunta qual é.** Um `isinstance(regra, PorMeta)` no contexto mostra que a interface não está segurando a diferença.
- **Uma estratégia por `if` de uma linha.** Quatro classes para escolher entre `<` e `>` é abstração por precaução, cobrada hoje.
- **A estratégia nunca varia em execução e só tem uma implementação.** É uma interface com um único implementador, que só acrescenta um salto na leitura.

> **Perigo.** O sinal mais comum: a interface cresce para caber na variante mais exigente. `calcular(venda, cliente, mes, tabela, config, sessao)`, e cada estratégia usa dois parâmetros e ignora quatro. O contexto passa a conhecer o que só uma delas precisa. O que sobra deveria entrar no construtor dessa estratégia.

> **Nota.** Na dúvida, comece com o `if` ou com uma função. A segunda variante cabe em um parâmetro. O sinal para extrair é a terceira variante, ou a escolha passar a vir de fora do código: aí a refatoração é pequena, porque cada ramo do `if` já é uma função em potencial.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [State](../state/explicacao.md) | Tem a mesma forma, mas quem troca de objeto é o próprio contexto, quando seu estado muda. No Strategy, a troca vem de fora e o contexto não a faz sozinho |
| [Command](../command/explicacao.md) | É uma ação concreta, com seus dados, que se guarda e se executa depois. A estratégia é um jeito de fazer, usado na hora, e normalmente nem carrega os dados |
| [Template Method](../template-method/explicacao.md) | Fixa o esqueleto do algoritmo e deixa os passos para as subclasses, trocando por herança. O Strategy troca o algoritmo inteiro, por composição, em execução |
| [Decorator](../../estruturais/decorator/explicacao.md) | Envolve por fora, mantendo o algoritmo. O Strategy troca o miolo por dentro |
| [Bridge](../../estruturais/bridge/explicacao.md) | Tem a mesma forma, mas a abstração também varia e as duas hierarquias crescem. No Strategy só o lado do algoritmo varia |

Regra prática: se quem escolhe o jeito de fazer é quem chama, é Strategy; se é o próprio objeto, ao mudar de estado, é State.

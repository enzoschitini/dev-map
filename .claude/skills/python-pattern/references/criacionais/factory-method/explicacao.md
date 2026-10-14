<!-- Gerado de pages/clean-code/criacionais/factory-method/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Factory Method — Explicação

*Clean Code / Design Pattern / Factory Method*

Como deixar o código principal criar um objeto sem saber qual classe exata está criando, entregando essa escolha para as subclasses.

<a id="o-problema"></a>
## O problema

O sistema gera relatórios: o de vendas mostra um gráfico de barras, o de estoque mostra um gráfico de linhas. O fluxo é o mesmo nos dois — coletar os dados, montar o gráfico, renderizar — e só duas coisas mudam: de onde vêm os dados e **qual gráfico** é criado.

A saída mais curta é uma classe só, com o tipo do relatório como parâmetro e um `if` em cada ponto que varia:

**antes — a classe conhece todos os relatórios e todos os gráficos**

```python
class Relatorio:
    def __init__(self, tipo):
        self.tipo = tipo

    def gerar(self):
        if self.tipo == "vendas":
            dados = consultar_vendas()
        elif self.tipo == "estoque":
            dados = consultar_estoque()
        else:
            raise ValueError(self.tipo)

        if self.tipo == "vendas":
            grafico = GraficoDeBarras(dados)
        elif self.tipo == "estoque":
            grafico = GraficoDeLinhas(dados)   # o mesmo if, de novo

        return grafico.renderizar()
```

Três coisas aparecem aos poucos: um relatório novo exige editar a classe em **dois lugares** — e esquecer um só dá erro em produção; a classe passa a conhecer todos os gráficos, então testar o relatório de vendas carrega o código do de estoque; e a cadeia de `if` cresce a cada pedido, sempre dentro de um método que já faz coisa demais. É o Open/Closed ao contrário: toda extensão vira modificação.

<a id="a-solucao"></a>
## A solução

Tire a criação do meio do fluxo e dê a ela um nome: um método, `criar_grafico()`, que a classe base *chama* mas não *implementa*. Cada tipo de relatório vira uma subclasse e decide o que criar. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Produto | A interface do que é criado | `Grafico` |
| Produto concreto | Uma implementação do produto | `GraficoDeBarras`, `GraficoDeLinhas` |
| Criador | A classe com o fluxo; chama o método fábrica sem saber o que volta | `Relatorio` |
| Criador concreto | A subclasse que sobrescreve o método fábrica | `RelatorioDeVendas` |

O ponto é **quem decide o tipo**. O fluxo mora em um lugar só, na classe base, e fica fechado para modificação. A decisão de qual gráfico criar sai dele e vai para quem já é, por outros motivos, o especialista naquele relatório.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. o produto: o que o criador espera receber
class Grafico(ABC):
    @abstractmethod
    def renderizar(self) -> str: ...

class GraficoDeBarras(Grafico):
    def __init__(self, dados):
        self._dados = dados

    def renderizar(self):
        return f"barras({self._dados})"

# 2. o criador: o fluxo, com o método fábrica no meio
class Relatorio(ABC):
    def gerar(self):
        dados = self.coletar()
        grafico = self.criar_grafico(dados)   # não sabe qual é
        return grafico.renderizar()

    @abstractmethod
    def coletar(self): ...

    @abstractmethod
    def criar_grafico(self, dados) -> Grafico: ...   # o método fábrica

# 3. o criador concreto: decide o tipo e mais nada do fluxo
class RelatorioDeVendas(Relatorio):
    def coletar(self):
        return consultar_vendas()

    def criar_grafico(self, dados):
        return GraficoDeBarras(dados)

# quem chama já sabe qual relatório quer
RelatorioDeVendas().gerar()
```

> **Dica.** O teste do fluxo agora é uma subclasse de três linhas cujo `criar_grafico` devolve um `GraficoFalso` que guarda o que recebeu. Nenhum dos relatórios reais entra no teste.

> **Nota.** Em Python, quando a subclasse só troca a *classe* criada, um atributo basta: `classe_do_grafico = GraficoDeBarras` na subclasse e `self.classe_do_grafico(dados)` na base. É o mesmo padrão com menos cerimônia — e o método fábrica só se justifica quando a criação precisa de mais lógica do que "qual classe".

<a id="quando-usar"></a>
## Quando usar

O Factory Method vale quando três coisas acontecem ao mesmo tempo: o código **precisa criar** um objeto cujo tipo exato ele não deveria conhecer; o resto do fluxo é **comum** e só o objeto criado muda; e **subclasses** já existem (ou fazem sentido) porque as variantes diferem em outras coisas além da criação.

No código, isso aparece de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um método longo em que só a linha de criação muda entre variantes | `if self.tipo == …` escolhendo qual classe instanciar, no meio de um fluxo que repete igual | [Uso #1](uso.md#fluxo-fixo) |
| Uma biblioteca ou classe base que outros times estendem | A biblioteca importa as classes concretas de quem a usa; cada necessidade nova vira PR nela | [Uso #2](uso.md#ponto-de-extensao) |
| A mesma escolha de tipo em vários métodos da mesma classe | A mesma cadeia `if`/`elif` ou `isinstance` copiada em `novo()`, `abrir()` e `duplicar()` | [Uso #3](uso.md#tipo-em-um-lugar) |
| Teste que precisa trocar um objeto criado no meio de um método | `@patch("modulo.requests.get")`; o objeto é criado dentro do método e o construtor não aceita parâmetros | [Uso #4](uso.md#costura-de-teste) |

> **Dica.** O que os sinais têm em comum: a pergunta "qual classe?" aparece **dentro** de um código que não tinha nada a ver com ela. O método fábrica é o lugar para onde essa pergunta vai.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **O tipo criado muda?** Se é sempre a mesma classe, chame `Classe()` direto.
2. **A escolha vem de um dado em tempo de execução** (extensão do arquivo, campo do JSON, string de configuração)? Então use uma função fábrica ou um mapa: o Factory Method pede que a escolha seja feita por *quem é a subclasse*, não por um valor.
3. **As variantes diferem só na criação?** Então não precisa de herança: receba a fábrica (ou o próprio objeto) por parâmetro.
4. **Existe um fluxo comum, e as variantes são subclasses por outros motivos?** Se sim, Factory Method.

<a id="quando-nao-usar"></a>
## Quando não usar

O Factory Method paga com **herança**: uma classe criadora por variante, mais uma hierarquia de produtos em paralelo. Para saber o que o fluxo realmente cria, é preciso saber qual subclasse está rodando, e o "ir para a definição" cai no método abstrato da base. Para uma variação de uma linha, o custo é desproporcional.

| Situação | Por que não | Faça isto |
|---|---|---|
| O tipo vem de um dado (extensão, campo, configuração) | Alguém ainda precisa de um `if` ou mapa para escolher a subclasse — você só moveu o problema | Uma função fábrica ou um dicionário `{".csv": LeitorCsv}` |
| Só a criação varia, e nada mais | Uma subclasse inteira para sobrescrever uma linha é muita estrutura | Receba o objeto, ou uma função que o cria, pelo construtor |
| Você pode injetar a dependência pelo construtor | A injeção é mais simples e mais explícita que uma subclasse de teste | Injeção de dependência |
| Vários produtos que precisam combinar entre si (botão e janela do mesmo tema) | Um método fábrica só cria um produto; a consistência entre eles fica a seu cargo | Abstract Factory |
| O objeto tem muitos parâmetros e é montado passo a passo | O problema não é "qual tipo", é "como montar" | Builder |

<a id="sinais-de-abuso"></a>
### Sinais de que o Factory Method saiu do lugar

- **O método fábrica recebe um `tipo` e faz `if`.** Você moveu a cadeia de `if` de lugar, e agora ela mora dentro de um método com nome de padrão.
- **Subclasses que só sobrescrevem a criação.** Se nada mais as diferencia, a herança não está dizendo nada: é uma função com mais arquivos.
- **Uma hierarquia nova para cada produto novo, sem ninguém pedir variação.** Dois produtos paralelos que crescem juntos "por precaução" dobram o custo de toda mudança.
- **O método fábrica faz mais que criar.** Abrir conexão, registrar em log, gravar em disco. Quem chama `criar_x()` não espera efeito colateral.
- **O criador depende do tipo concreto que criou.** Um `isinstance(grafico, GraficoDeBarras)` no fluxo mostra que a abstração não está segurando a diferença.

> **Perigo.** O sinal mais comum: toda subclasse de criador se resume a `return NovaClasse()`. O padrão virou um `if` com mais arquivos.

> **Nota.** Na dúvida, comece com `Classe()` direto. A segunda variação é o momento certo para extrair o método fábrica: a refatoração é pequena (extrair o método, criar a subclasse), e agora você tem dois casos reais para desenhá-lo, em vez de um palpite.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Fábrica simples (função ou mapa) | Escolhe o tipo por um `if` ou dicionário sobre um dado, sem herança. O Factory Method entrega a escolha a uma subclasse |
| Abstract Factory | Cria *famílias* de objetos que combinam entre si; costuma ser implementada com vários métodos fábrica |
| Template Method | Esqueleto fixo com passos sobrescritos. O Factory Method é um Template Method em que um dos passos é criar um objeto |
| Strategy | Troca o comportamento por composição: o objeto é passado de fora. O Factory Method troca por herança: a subclasse o cria |
| Builder | Monta um objeto complexo passo a passo; não decide o tipo, decide como montar |

Regra prática: se a escolha do tipo é feita por um `if` sobre um dado, é uma fábrica simples. Se é feita por uma subclasse, é Factory Method.

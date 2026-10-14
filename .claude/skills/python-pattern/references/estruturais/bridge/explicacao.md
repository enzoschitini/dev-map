<!-- Gerado de pages/clean-code/estruturais/bridge/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Bridge — Explicação

*Clean Code / Design Pattern / Bridge*

Como deixar duas coisas que variam por motivos diferentes crescerem separadas, em vez de multiplicar uma subclasse para cada combinação.

<a id="o-problema"></a>
## O problema

O sistema gera o relatório de vendas do mês em CSV. Funciona, então alguém pede o mesmo relatório em HTML, para mandar por e-mail. Você cria uma subclasse. Na semana seguinte entra o relatório de estoque, que também precisa dos dois formatos. Mais duas subclasses.

Cada pedido novo parece pequeno, e a herança resolve cada um com uma classe:

**antes — uma subclasse para cada combinação**

```python
class RelatorioDeVendasCsv:
    def gerar(self, pedidos):
        saida = io.StringIO()
        escritor = csv.writer(saida)
        escritor.writerow(["pedido", "cliente", "total"])
        for p in pedidos:
            escritor.writerow([p.id, p.cliente, f"{p.total:.2f}"])
        return saida.getvalue()

class RelatorioDeVendasHtml:
    def gerar(self, pedidos):
        linhas = "".join(
            f"<tr><td>{p.id}</td><td>{escape(p.cliente)}</td><td>{p.total:.2f}</td></tr>"
            for p in pedidos
        )
        return f"<h1>Vendas do mês</h1><table>{linhas}</table>"

# RelatorioDeEstoqueCsv: o mesmo csv.writer, outras colunas
# RelatorioDeEstoqueHtml: o mesmo <table>, outras colunas
# e o PDF que o financeiro pediu? Mais duas classes.
```

O defeito não aparece na primeira classe. Aparece na conta: com **2 tipos** e **2 formatos** são 4 classes; com 3 formatos, 6; com 5 tipos, 15. Cada tipo novo custa uma classe por formato, e cada formato novo custa uma classe por tipo. Pior: a montagem do CSV está copiada em todas, então corrigir o escape de uma vírgula é uma busca por arquivos. Cada classe tem dois motivos para mudar, o que entra no relatório e como ele é escrito, e isso é o Single Responsibility sendo violado.

<a id="a-solucao"></a>
## A solução

Separe as duas coisas que variam em duas hierarquias e ligue-as por **composição**: o relatório guarda uma referência a um formato, e delega a ele a parte de escrever. Os papéis são cinco:

| Papel | Quem é | No exemplo |
|---|---|---|
| Abstração | O "o quê". Guarda a referência à implementação e delega a ela | `Relatorio` |
| Abstração refinada | Cada variação do "o quê" | `RelatorioDeVendas`, `RelatorioDeEstoque` |
| Implementação | A interface do "como", em operações pequenas | `Formato` |
| Implementação concreta | Cada variação do "como" | `FormatoCsv`, `FormatoHtml` |
| Cliente | Quem escolhe o par e usa a abstração | O job que envia o relatório do mês |

O ponto é que as duas interfaces **não são parecidas**. A abstração fala de relatórios; a implementação fala de colunas, linhas e texto. Essa referência entre elas é a "ponte". Com ela, 5 tipos e 3 formatos são 8 classes, e não 15.

<a id="implementacao"></a>
## Implementação

```python
import csv, io
from abc import ABC, abstractmethod
from html import escape

# 1. a implementação: o "como", sem saber de vendas nem de estoque
class Formato(ABC):
    @abstractmethod
    def montar(self, titulo: str, colunas: list[str], linhas: list[list[str]]) -> str: ...

class FormatoCsv(Formato):
    def montar(self, titulo, colunas, linhas):
        saida = io.StringIO()
        escritor = csv.writer(saida)
        escritor.writerow(colunas)
        escritor.writerows(linhas)
        return saida.getvalue()

class FormatoHtml(Formato):
    def montar(self, titulo, colunas, linhas):
        cabecalho = "".join(f"<th>{escape(c)}</th>" for c in colunas)
        corpo = "".join(
            "<tr>" + "".join(f"<td>{escape(v)}</td>" for v in linha) + "</tr>"
            for linha in linhas
        )
        return f"<h1>{escape(titulo)}</h1><table><tr>{cabecalho}</tr>{corpo}</table>"

# 2. a abstração: o "o quê", com a ponte na primeira linha do __init__
class Relatorio(ABC):
    titulo: str

    def __init__(self, formato: Formato):
        self._formato = formato

    @abstractmethod
    def colunas(self) -> list[str]: ...

    @abstractmethod
    def linhas(self) -> list[list[str]]: ...

    def gerar(self) -> str:
        return self._formato.montar(self.titulo, self.colunas(), self.linhas())

# 3. abstração refinada: sabe de vendas, não sabe de CSV
class RelatorioDeVendas(Relatorio):
    titulo = "Vendas do mês"

    def __init__(self, formato: Formato, pedidos):
        super().__init__(formato)
        self._pedidos = pedidos

    def colunas(self):
        return ["pedido", "cliente", "total"]

    def linhas(self):
        return [[str(p.id), p.cliente, f"{p.total:.2f}"] for p in self._pedidos]

# 4. o cliente escolhe o par; qualquer par funciona
RelatorioDeVendas(FormatoCsv(), pedidos).gerar()
RelatorioDeVendas(FormatoHtml(), pedidos).gerar()
```

> **Dica.** Dá para testar cada lado sozinho. `FormatoCsv` recebe colunas e linhas escritas na mão, sem pedido nenhum. `RelatorioDeVendas` recebe um `Formato` falso que só guarda o que recebeu. São N + M testes, e não N × M.

<a id="quando-usar"></a>
## Quando usar

O Bridge vale quando três coisas acontecem ao mesmo tempo: existem **duas dimensões** de variação, cada uma tem **mais de uma variante** (ou a segunda está confirmada), e a escolha em uma **não depende** da escolha na outra.

No código, isso costuma aparecer de formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Nomes de classe que juntam duas ideias | `RelatorioDeVendasCsv`, `CobrancaPorSms`: um "o quê" colado a um "como" | [Uso #1](uso.md#avisos-e-canais) |
| Cada novo X exige uma subclasse por Y | Um pull request para "adicionar WhatsApp" que cria uma classe em cada tipo de aviso | [Uso #1](uso.md#avisos-e-canais) |
| A mesma lógica precisa rodar sobre plataformas diferentes | `if typeof document === "undefined"` ou `if sys.platform == …` dentro de uma regra | [Uso #2](uso.md#mesmo-grafico-varios-ambientes) |
| Implementações escritas por outras pessoas, em número aberto | Uma classe central com `if banco == "postgres"` … `elif banco == "mysql"` em cada método | [Uso #3](uso.md#bancos-de-dados) |
| A mesma lógica de alto nível copiada em cada implementação | `PostgresRelatorio` e `MysqlRelatorio` com o mesmo laço, diferindo em duas linhas | [Uso #3](uso.md#bancos-de-dados) |

> **Dica.** Os sinais têm uma coisa em comum: dois assuntos diferentes respondidos no mesmo lugar. "O que estou montando?" e "onde isso vai sair?" aparecem juntos no nome da classe, no `if`, na cópia. A ponte é o lugar onde as duas perguntas passam a ter respostas separadas.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Mais de uma coisa varia, de verdade?** Se só uma dimensão tem variantes, é herança simples, ou Strategy se você escolhe o algoritmo em tempo de execução. Pare.
2. **As duas dimensões são independentes?** Se só alguns pares fazem sentido (estoque nunca sai em PDF), não são eixos: são combinações. Modele as que existem.
3. **Você consegue descrever cada lado sem citar o outro?** "O que entra no relatório" e "como ele é escrito" funcionam. Se para explicar um você precisa do outro, a ponte vai vazar.
4. **Já são mais de 2 × 2, ou o terceiro está a caminho?** Se são 4 classes e vão continuar 4, a herança direta custa menos. Se o terceiro formato ou o terceiro tipo já tem data, é Bridge.

<a id="quando-nao-usar"></a>
## Quando não usar

O Bridge tem um custo fixo: duas hierarquias em vez de uma, uma interface a mais e uma referência entre elas. Quem lê uma chamada precisa seguir dois lugares para entender o que acontece. E a interface da implementação é a parte mais difícil de acertar: larga demais, cada implementação sofre; estreita demais, a abstração não consegue fazer o que precisa.

| Situação | Por que não | Faça isto |
|---|---|---|
| Só um eixo varia | Não há produto cartesiano; a ponte liga um lado a nada | Herança simples, ou Strategy para trocar o algoritmo em tempo de execução |
| Dois eixos, mas 2 × 2 e parados | Quatro classes custam menos que duas hierarquias e uma interface | Subclasses diretas. Extraia a ponte quando o terceiro valor aparecer |
| Os eixos não são independentes | A ponte promete qualquer combinação; as inválidas viram erro só em tempo de execução | Modele as combinações que existem, ou valide o par na construção |
| A implementação já existe, com a interface de outra pessoa | O problema é encaixe, não separação de eixos | Adapter |
| Você quer acrescentar cache, log ou retry | A interface antes e depois é a mesma; não há segunda dimensão | Decorator |

<a id="sinais-de-abuso"></a>
### Sinais de que o Bridge saiu do lugar

- **A interface da implementação espelha a da abstração.** Se `Formato` tem `montar_vendas` e `montar_estoque`, o formato conhece os tipos. Os eixos não foram separados; foram só copiados.
- **A abstração pergunta qual é a implementação.** Um `isinstance(self._formato, FormatoCsv)` dentro do relatório mostra que a interface não segura a diferença.
- **Só existe uma implementação, "para o futuro".** É a segunda hierarquia criada antes de existir a segunda variante. O custo é cobrado hoje, e o futuro pode não vir.
- **A implementação toma decisão de negócio.** Um `FormatoCsv` que arredonda o total ou esconde cliente inativo faz com que a regra seja reescrita, e possa divergir, em cada formato.
- **A abstração tem um único filho.** Uma hierarquia "refinada" com uma classe só é uma classe com uma interface sobrando.

> **Perigo.** O sinal mais comum: a interface da implementação ganha um método novo a cada tipo novo. É o produto cartesiano voltando, agora em métodos em vez de classes, e o custo para cada implementação continua sendo N × M.

> **Nota.** Na dúvida, espere o segundo eixo. Com um tipo de relatório, uma subclasse por formato é razoável. Quando o segundo tipo aparecer, a extração é mecânica: as subclasses viram implementações, a classe base vira a abstração e o formato passa a entrar pelo construtor.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| [Adapter](../adapter/explicacao.md) | Entra depois, para encaixar duas interfaces que já existiam; o Bridge é desenhado antes, para as duas partes crescerem separadas. A forma em código é parecida; a intenção é outra |
| Strategy | Injeta um algoritmo em uma classe, e só o lado do algoritmo varia. No Bridge a abstração também tem variantes e as duas hierarquias evoluem |
| Template Method | Varia partes de um algoritmo por herança, dentro de uma só hierarquia. O Bridge troca essa herança por composição |
| Abstract Factory | Cria famílias de objetos que combinam entre si. Pode ser quem monta a ponte, escolhendo a implementação certa para o ambiente |

Regra prática: se as duas interfaces nasceram juntas, para variar em separado, é Bridge; se uma delas já existia e você teve de encaixá-la, é Adapter.

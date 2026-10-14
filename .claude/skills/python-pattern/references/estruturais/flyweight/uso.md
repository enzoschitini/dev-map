<!-- Gerado de pages/clean-code/estruturais/flyweight/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Flyweight — Uso

*Clean Code / Design Pattern / Flyweight*

Três situações em que o Flyweight resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o flyweight compartilha em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Flyweight. Marcadores de mapa, glifos de um editor e partículas de um jogo são o mesmo raciocínio do exemplo da [explicação](explicacao.md#implementacao) (muitos objetos com o mesmo estado pesado por tipo), então ele não se repete aqui. Sobraram três motivos que ela não cobre. Os casos que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o flyweight compartilha |
|---|---|---|
| 1 | [Milhões de linhas com os mesmos poucos textos](#valores-repetidos) | Cada valor repetido, em uma única cópia |
| 2 | [Um objeto imutável caro, criado a cada requisição](#objeto-caro-de-criar) | O objeto, uma vez por chave |
| 3 | [Uma grade de milhões de células](#grade-de-tiles) | A descrição de cada tipo; a grade guarda só um número |

<a id="valores-repetidos"></a>
## 1. Milhões de linhas com os mesmos poucos textos

**Situação.** O time de análise carrega em memória um CSV de 2 milhões de entregas para calcular indicadores. As colunas `cidade`, `status` e `transportadora` têm centenas de valores diferentes no total, repetidos milhões de vezes.

**sem o pattern — cada linha traz a própria cópia do texto**

```python
@dataclass
class Entrega:
    id: int
    cidade: str
    status: str
    transportadora: str
    valor: float

def carregar(caminho):
    with open(caminho, newline="") as f:
        return [
            Entrega(int(l["id"]), l["cidade"], l["status"], l["transportadora"], float(l["valor"]))
            for l in csv.DictReader(f)
        ]
```

**O que dói.** O leitor de CSV cria um objeto `str` novo para cada célula. Seis milhões de textos de uns 50 bytes cada são algo da ordem de 300 MB para guardar umas poucas centenas de valores diferentes. Comparar `e.status == "entregue"` compara caractere por caractere, em cada uma das 2 milhões de linhas.

**com o pattern — cada valor existe uma vez; as linhas apontam para ele**

```python
import sys

def carregar(caminho):
    internar = sys.intern     # a "fábrica": devolve sempre o mesmo objeto para o mesmo texto
    with open(caminho, newline="") as f:
        return [
            Entrega(
                int(l["id"]),
                internar(l["cidade"]),
                internar(l["status"]),
                internar(l["transportadora"]),
                float(l["valor"]),
            )
            for l in csv.DictReader(f)
        ]
```

**O que o flyweight compartilha.** O próprio valor. Aqui **não existe classe de flyweight**: o texto é o flyweight, e `sys.intern` é a fábrica. Isso só é possível porque `str` é imutável, o mesmo requisito do exemplo da explicação, em escala mínima. Um benefício extra aparece na comparação: com a mesma instância, o Python resolve `==` por identidade antes de olhar os caracteres.

> **Cuidado.** Só vale para campos de **baixa cardinalidade**. Internar o `id` ou um comentário em texto livre enche a tabela de internamento com valores que nunca se repetem, e a memória sobe em vez de descer. Confira com `len(set(coluna))` antes.

<a id="objeto-caro-de-criar"></a>
## 2. Um objeto imutável caro, criado a cada requisição

**Situação.** O cadastro valida o documento de cada pessoa conforme o país: cada país tem um arquivo de regras (padrão e dígitos verificadores). O serviço recebe 50 cadastros por segundo, de uns 200 países, e o problema aqui não é a memória: é o **tempo** de criar o validador.

**sem o pattern — o validador é lido e compilado a cada chamada**

```python
class ValidadorDeDocumento:
    def __init__(self, pais: str):
        regras = json.loads(Path(f"regras/{pais}.json").read_text())   # disco
        self._padrao = re.compile(regras["padrao"])
        self._dv = regras["digitos_verificadores"]

    def valido(self, documento: str) -> bool: ...

def cadastrar(pessoa):
    if not ValidadorDeDocumento(pessoa.pais).valido(pessoa.documento):
        raise DocumentoInvalido(pessoa.documento)
```

**O que dói.** Cada cadastro lê um arquivo e compila uma expressão regular, para jogar fora o resultado logo depois. A 50 por segundo, são 50 leituras de disco e 50 compilações por segundo, com o mesmo resultado, e a latência do cadastro inclui esse trabalho. O teste tem que falsificar o sistema de arquivos para exercitar a validação.

**com o pattern — uma fábrica entrega o mesmo validador para o mesmo país**

```python
import functools

@dataclass(frozen=True)
class ValidadorDeDocumento:
    padrao: re.Pattern
    digitos_verificadores: tuple

    def valido(self, documento: str) -> bool: ...

@functools.cache
def validador_para(pais: str) -> ValidadorDeDocumento:
    regras = json.loads(Path(f"regras/{pais}.json").read_text())
    return ValidadorDeDocumento(
        re.compile(regras["padrao"]),
        tuple(regras["digitos_verificadores"]),
    )

def cadastrar(pessoa):
    if not validador_para(pessoa.pais).valido(pessoa.documento):
        raise DocumentoInvalido(pessoa.documento)
```

**O que o flyweight compartilha.** O objeto inteiro, uma vez por chave. O motivo aqui é o **custo de criação**, não a memória: 200 validadores ocupam pouco, o que pesa é lê-los e compilá-los de novo. O chamador não mudou de interface; mudou o `ValidadorDeDocumento(pais)` por `validador_para(pais)`. A biblioteca padrão tem exemplos da mesma forma: `zoneinfo.ZoneInfo("America/Sao_Paulo")` devolve a mesma instância para a mesma chave, e o módulo `re` guarda as expressões já compiladas.

> **Cuidado.** Compartilhar objeto entre requisições, e entre *threads*, só é seguro porque o validador é imutável (`frozen=True`, tupla em vez de lista). Se ele guardasse "o último documento validado", duas requisições simultâneas se atropelariam. E `functools.cache` não tem limite: com chaves abertas, use `lru_cache(maxsize=…)`.

<a id="grade-de-tiles"></a>
## 3. Uma grade de milhões de células

**Situação.** O editor de mapas de um jogo trabalha com uma grade de 2.000 × 2.000 células, 4 milhões no total. Cada célula é de um tipo (grama, água, pedra), e cada tipo define textura, se é transitável e quanto custa atravessar. O mapa é salvo e carregado inteiro.

**sem o pattern — um objeto por célula, com campos copiados do tipo**

```python
class Tile:
    def __init__(self, tipo: str):
        self.tipo = tipo
        self.textura = TEXTURAS[tipo]
        self.passavel = tipo != "agua"
        self.custo = CUSTOS[tipo]

mapa = [[Tile(tipo_em(x, y)) for x in range(2000)] for y in range(2000)]

# no editor, ao pintar uma célula de água:
mapa[y][x].tipo = "agua"      # e o passavel? e o custo? esqueceram
```

**O que dói.** Quatro milhões de objetos Python, cada um com o próprio dicionário de atributos, passam de **1 GB** e demoram segundos para ser criados. Salvar e carregar o mapa percorre todos eles. E os campos derivados do tipo (`passavel`, `custo`) ficam desatualizados quando alguém troca só o `tipo`.

**com o pattern — a grade guarda um número, o tipo guarda o resto**

```python
@dataclass(frozen=True)
class TipoDeTile:          # o flyweight: um por tipo
    nome: str
    textura: Textura
    passavel: bool
    custo: int

TIPOS = [
    TipoDeTile("grama", TEXTURAS["grama"], passavel=True, custo=1),
    TipoDeTile("agua", TEXTURAS["agua"], passavel=False, custo=0),
    TipoDeTile("pedra", TEXTURAS["pedra"], passavel=True, custo=3),
]

class Mapa:
    def __init__(self, largura: int, altura: int):
        self._largura = largura
        self._tiles = bytearray(largura * altura)   # um byte por célula: o índice em TIPOS

    def tipo_em(self, x: int, y: int) -> TipoDeTile:
        return TIPOS[self._tiles[y * self._largura + x]]

    def pintar(self, x: int, y: int, indice: int):
        self._tiles[y * self._largura + x] = indice
```

**O que o flyweight compartilha.** A descrição do tipo, e o que este exemplo ensina é o outro lado: o **contexto pode ser mínimo**. A célula não é um objeto; é um byte, e a sua posição nem é guardada, porque sai do índice no array. O estado extrínseco (`x`, `y`) é *calculado*, não armazenado. Os 4 milhões de objetos viram 4 MB, e salvar o mapa é gravar o `bytearray`.

> **Dica.** Como o tipo mora em um lugar só, `pintar` não pode deixar `passavel` inconsistente: não existe campo para esquecer. E mudar o custo da pedra para 4 é uma linha em `TIPOS`, que vale para as milhões de células de pedra.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na explicação):

| Caso | Já coberto por |
|---|---|
| Ícones e estilos de marcadores em um mapa | Explicação — o exemplo condutor |
| Glifos e estilos de caractere em um editor de texto | Explicação — o mesmo raciocínio: estado do tipo compartilhado, posição por argumento |
| Partículas de um jogo com a mesma textura e a mesma física | Explicação — o mesmo raciocínio |
| Categorias e países repetidos em uma tabela de milhões de linhas | 1 — valores repetidos |
| Fusos horários, expressões regulares, formatadores caros de construir | 2 — objeto imutável caro de criar |
| Tabuleiro de xadrez ou de jogo de estratégia | 3 — a grade guarda índices |

E dois casos que parecem Flyweight, mas não são. Um *pool* de conexões também reaproveita objetos caros, mas empresta cada um a um chamador por vez e o recebe de volta: os objetos são mutáveis, e não se compartilham ao mesmo tempo. E um Singleton garante *uma* instância para a classe toda, enquanto o Flyweight tem uma por valor da chave. Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.

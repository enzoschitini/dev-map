<!-- Gerado de pages/clean-code/comportamentais/strategy/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Strategy — Uso

*Clean Code / Design Pattern / Strategy*

Quatro situações em que o Strategy resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que ele isola em cada caso.

<a id="como-escolhi"></a>
## Por que quatro

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Strategy. Quando dois casos se resolvem com o mesmo raciocínio — validar documento por país e escolher a ordenação por uma opção da tela, por exemplo — só um fica. Seguindo essa regra, sobraram quatro motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o Strategy isola |
|---|---|---|
| 1 | [O usuário escolhe como a lista é ordenada](#ordenacao-escolhida) | A opção da tela, do algoritmo que a atende |
| 2 | [O mesmo resultado, com custos diferentes](#custo-diferente) | O *como* do *quando* |
| 3 | [Uma política de espera que o laço consulta](#politica-de-retentativa) | A mecânica do laço, da política dentro dele |
| 4 | [A regra vem do cadastro, não do código](#regra-do-cadastro) | O texto gravado no banco, do objeto que o executa |

<a id="ordenacao-escolhida"></a>
## 1. O usuário escolhe como a lista é ordenada

**Situação.** A listagem de produtos tem um seletor "Ordenar por": menor preço, melhor avaliação, mais vendidos, entrega mais rápida. A tela manda uma string, e alguém precisa traduzi-la em uma ordenação. O catálogo cresce uma opção por trimestre.

**sem o pattern — um if por opção do seletor**

```typescript
function ordenar(produtos: Produto[], ordem: string): Produto[] {
  const copia = [...produtos];
  if (ordem === "preco") {
    return copia.sort((a, b) => a.preco - b.preco);
  } else if (ordem === "avaliacao") {
    return copia.sort((a, b) => b.nota - a.nota);
  } else if (ordem === "vendidos") {
    return copia.sort((a, b) => b.vendas - a.vendas);
  }
  return copia;  // "entrega"? a opção existe na tela, o if nunca foi escrito
}
```

**O que dói.** A tela e este `if` precisam concordar em cada texto, e a única checagem é a memória de quem escreve. Uma opção sem `if` cai no `return` do fim, em silêncio, e a lista parece "ordenada". Em empate de nota, o desempate por preço teria que ser lembrado em cada ramo.

**com o pattern — a ordem é um comparador em uma tabela**

```typescript
type Comparador = (a: Produto, b: Produto) => number;

const ordens = {
  preco:     (a, b) => a.preco - b.preco,
  avaliacao: (a, b) => b.nota - a.nota || a.preco - b.preco,
  vendidos:  (a, b) => b.vendas - a.vendas || a.preco - b.preco,
  entrega:   (a, b) => a.prazoDias - b.prazoDias || a.preco - b.preco,
} satisfies Record<string, Comparador>;

export type Ordem = keyof typeof ordens;

export function ordenar(produtos: readonly Produto[], ordem: Ordem): Produto[] {
  return [...produtos].sort(ordens[ordem]);
}

// o seletor da tela sai da própria tabela
export const opcoes = Object.keys(ordens) as Ordem[];
```

**O que o Strategy isola.** A opção da tela, do algoritmo que a atende. `Array.prototype.sort` já é um contexto de Strategy: ele não sabe ordenar nada por si, recebe o comparador de fora. A tabela é a única lista de opções, o seletor é gerado a partir dela, e o compilador recusa uma `Ordem` que não existe. Uma nova opção é uma linha, e o `ordenar` não é tocado.

> **Dica.** Aqui a estratégia é uma *função*, e não uma classe. Em linguagens com funções de primeira classe, essa é a forma normal do Strategy: uma classe com um único método e sem estado é uma função com cerimônia.

<a id="custo-diferente"></a>
## 2. O mesmo resultado, com custos diferentes

**Situação.** O sistema comprime dois tipos de dado. Os logs seguem em tempo real para o coletor: precisam sair rápido, e ocupar um pouco mais não importa. O backup noturno tem a madrugada inteira e quer o menor arquivo possível. Nos dois casos, o que se faz com o resultado é o mesmo: gravar em disco e, depois, ler de volta.

**sem o pattern — a política e o algoritmo no mesmo if**

```python
def guardar(dados: bytes, destino: Path, tempo_real: bool):
    if tempo_real:
        saida = gzip.compress(dados, compresslevel=1)
        destino = destino.with_suffix(".gz")
    elif len(dados) > 50_000_000:
        saida = lzma.compress(dados, preset=9)
        destino = destino.with_suffix(".xz")
    else:
        saida = bz2.compress(dados)
        destino = destino.with_suffix(".bz2")
    destino.write_bytes(saida)

# e o mesmo if, de novo, em ler(), para escolher o descompressor
```

**O que dói.** Quando usar cada algoritmo e como usar cada um estão no mesmo lugar, e a decisão está duplicada em `ler`. Se alguém mudar o limite de 50 MB em uma das duas pontas, os arquivos gravados ficam sem leitura. O booleano `tempo_real` já é a versão de bolso do problema: a próxima necessidade vira outro booleano.

**com o pattern — um objeto por algoritmo, e a escolha em um lugar**

```python
class Compressor(Protocol):
    extensao: str
    def comprimir(self, dados: bytes) -> bytes: ...
    def descomprimir(self, dados: bytes) -> bytes: ...

class Gzip:                      # rápido
    extensao = ".gz"
    def comprimir(self, dados):    return gzip.compress(dados, compresslevel=1)
    def descomprimir(self, dados): return gzip.decompress(dados)

class Bzip2:                     # meio-termo
    extensao = ".bz2"
    def comprimir(self, dados):    return bz2.compress(dados)
    def descomprimir(self, dados): return bz2.decompress(dados)

class Lzma:                      # menor arquivo, mais lento
    extensao = ".xz"
    def comprimir(self, dados):    return lzma.compress(dados, preset=9)
    def descomprimir(self, dados): return lzma.decompress(dados)

def guardar(dados: bytes, destino: Path, compressor: Compressor):
    destino.with_suffix(compressor.extensao).write_bytes(compressor.comprimir(dados))

def ler(origem: Path, compressor: Compressor) -> bytes:
    return compressor.descomprimir(origem.read_bytes())

# a política: o único lugar que fala em "tempo real" e em tamanho
def compressor_para(tempo_real: bool, tamanho: int) -> Compressor:
    if tempo_real:
        return Gzip()
    return Lzma() if tamanho > 50_000_000 else Bzip2()
```

**O que o Strategy isola.** O *como* do *quando*. Os três algoritmos são equivalentes no que importa para quem grava e lê: bytes entram, bytes comprimidos saem, e voltam iguais. O que muda é o custo (tempo contra tamanho). Por isso a política de escolha cabe em quatro linhas, e pode mudar depois de uma medição sem tocar em nenhuma das três classes.

> **Cuidado.** A leitura não pode usar a política de *hoje*: o arquivo foi gravado com a de ontem. Escolha o descompressor pelo que está no arquivo (a extensão, ou um identificador no cabeçalho), e a política passa a valer só para o que ainda vai ser gravado.

<a id="politica-de-retentativa"></a>
## 3. Uma política de espera que o laço consulta

**Situação.** Três partes do sistema chamam a mesma API de terceiros, que responde com erro temporário de vez em quando. A consulta de cotação tenta três vezes, com meio segundo entre elas, porque a tela está esperando. O relatório diário tenta oito vezes, esperando cada vez o dobro. O envio de webhooks faz o mesmo, mas com um sorteio na espera, para as tentativas não baterem juntas.

**sem o pattern — o laço copiado, com a política dentro**

```python
def buscar_cotacao(par):
    for tentativa in range(3):
        try:
            return api.get(f"/cotacoes/{par}")
        except ErroTemporario:
            time.sleep(0.5)
    raise TentativasEsgotadas(par)

def baixar_relatorio(dia):
    for tentativa in range(8):
        try:
            return api.get(f"/relatorios/{dia}")
        except ErroTemporario:
            time.sleep(2 ** tentativa + random.uniform(0, 1))
    raise TentativasEsgotadas(dia)
```

**O que dói.** A mecânica de tentar de novo está escrita três vezes, cada uma com um número diferente embutido, então ninguém sabe qual é "a política da empresa". O teste de `baixar_relatorio`, para chegar ao `raise`, dorme mais de quatro minutos de verdade. E o sorteio dentro do laço faz o teste falhar de vez em quando.

**com o pattern — o laço pergunta quanto esperar e quando desistir**

```python
class Espera(Protocol):
    def apos(self, tentativa: int) -> float | None:
        """Segundos até a próxima tentativa; None para desistir."""

class Fixa:
    def __init__(self, segundos: float, tentativas: int):
        self._segundos, self._tentativas = segundos, tentativas

    def apos(self, tentativa):
        return self._segundos if tentativa < self._tentativas - 1 else None

class Exponencial:
    def __init__(self, tentativas: int, sorteio=random.uniform):
        self._tentativas, self._sorteio = tentativas, sorteio

    def apos(self, tentativa):
        if tentativa >= self._tentativas - 1:
            return None
        return 2 ** tentativa + self._sorteio(0, 1)

def com_retentativas(operacao, espera: Espera, dormir=time.sleep):
    tentativa = 0
    while True:
        try:
            return operacao()
        except ErroTemporario:
            pausa = espera.apos(tentativa)
            if pausa is None:
                raise
            dormir(pausa)
            tentativa += 1

cotacao = com_retentativas(lambda: api.get(f"/cotacoes/{par}"), Fixa(0.5, tentativas=3))
relatorio = com_retentativas(lambda: api.get(f"/relatorios/{dia}"), Exponencial(tentativas=8))
```

**O que o Strategy isola.** A mecânica do laço, da política dentro dele. O laço só sabe perguntar "quanto espero?" e ouvir um número ou `None`; a estratégia sabe tudo sobre números. O teste troca as duas peças: `Fixa(0, 3)` e um `dormir` que não faz nada, e a falha percorre as três tentativas em microssegundos. O sorteio entra pelo construtor da `Exponencial` pelo mesmo motivo.

> **Dica.** O sorteio na espera existe para que vários clientes, falhando ao mesmo tempo, não tentem todos no mesmo instante e derrubem a API de novo. É um bom exemplo do que uma estratégia nomeada carrega: um motivo que, no `sleep` solto, ninguém escreve.

<a id="regra-do-cadastro"></a>
## 4. A regra vem do cadastro, não do código

**Situação.** Clientes corporativos negociam descontos diferentes. Um tem 10% fixo; outro tem 5% a partir de 100 licenças e 12% a partir de 500. O comercial ajusta contratos toda semana, e hoje cada ajuste vira um pedido para o time de desenvolvimento. A regra de cada cliente está gravada em uma linha do cadastro: `{"tipo": "faixas", "parametros": {…}}`.

**sem o pattern — o mesmo if em três funções, lendo o dict por dentro**

```python
def desconto_do_pedido(cliente, pedido):
    regra = cliente.regra_de_desconto            # dict vindo do banco
    if regra["tipo"] == "fixo":
        return pedido.subtotal * Decimal(regra["parametros"]["percentual"]) / 100
    elif regra["tipo"] == "faixas":
        for faixa in regra["parametros"]["faixas"]:
            if pedido.licencas >= faixa["a_partir_de"]:
                pct = faixa["percentual"]
        return pedido.subtotal * Decimal(pct) / 100   # e se nenhuma faixa bateu?

# descricao_na_fatura(cliente) e simular(cliente, qtd), na tela do comercial,
# repetem o mesmo if regra["tipo"] — cada um com o seu jeito de ler os parâmetros
```

**O que dói.** Cada operação sobre a regra (calcular, descrever, simular) tem o seu `if` por tipo, e um tipo novo precisa ser lembrado nas três. Um contrato salvo com parâmetro faltando só explode quando o cliente fizer um pedido, semanas depois, em produção. Se nenhuma faixa bater, `pct` nem existe.

**com o pattern — o cadastro vira objeto em um ponto só**

```python
class RegraDeDesconto(Protocol):
    def valor(self, pedido: Pedido) -> Decimal: ...
    def descricao(self) -> str: ...

@dataclass(frozen=True)
class Fixo:
    percentual: Decimal

    def valor(self, pedido):
        return pedido.subtotal * self.percentual / 100

    def descricao(self):
        return f"{self.percentual}% fixo"

@dataclass(frozen=True)
class PorFaixa:
    faixas: tuple[tuple[int, Decimal], ...]   # (a_partir_de, percentual), em ordem

    def valor(self, pedido):
        pct = Decimal(0)
        for a_partir_de, percentual in self.faixas:
            if pedido.licencas >= a_partir_de:
                pct = percentual
        return pedido.subtotal * pct / 100

    def descricao(self):
        return "por faixa de licenças"

# a única tabela que liga o nome gravado no cadastro à classe
REGRAS = {
    "fixo": lambda p: Fixo(Decimal(p["percentual"])),
    "faixas": lambda p: PorFaixa(tuple(
        (f["a_partir_de"], Decimal(f["percentual"])) for f in p["faixas"]
    )),
}

def regra_do_cadastro(linha: dict) -> RegraDeDesconto:
    try:
        return REGRAS[linha["tipo"]](linha["parametros"])
    except (KeyError, InvalidOperation) as e:
        raise ContratoInvalido(linha) from e

# o resto do sistema só conhece valor() e descricao()
regra = regra_do_cadastro(cliente.regra_de_desconto)
desconto = regra.valor(pedido)
texto_da_fatura = regra.descricao()
```

**O que o Strategy isola.** O texto gravado no banco, do objeto que o executa. A fronteira vira uma função: depois dela, ninguém lê `dict` nem compara `"fixo"`. As três operações viraram um método cada, em vez de um `if` cada. E o erro aparece cedo: a tela do comercial chama `regra_do_cadastro` ao salvar o contrato, e o `ContratoInvalido` aparece na hora, não semanas depois no pedido.

> **Cuidado.** As chaves de `REGRAS` estão gravadas no banco. Renomear a classe é seguro; renomear `"faixas"` deixa todas as linhas existentes sem estratégia. O nome no cadastro é um contrato de dados, e se muda, muda com uma migração.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos quatro:

| Caso | Já coberto por |
|---|---|
| Validar documento de identidade conforme o país do cliente | 1 — uma tabela de chave para função, escolhida por um valor de fora |
| Modo de reprodução de um player (sequencial, aleatório, repetir uma) | 1 — a escolha vem do usuário, e o objeto só guarda a referência |
| Escolher o algoritmo de busca ou de ordenação conforme o tamanho da lista | 2 — resultados equivalentes, custos diferentes |
| Política de expiração de um cache (por tempo, por uso) | 3 — o mecanismo consulta uma política que decide |
| Fixar relógio e sorteio para o teste ficar determinístico | 3 — a dependência entra pelo construtor |
| Imposto por município, tabela de preço por cliente, regra de frete por contrato | 4 — a regra é um dado, e vira objeto na fronteira |

E um caso que parece Strategy, mas não é: o pedido que se comporta de um jeito quando está *pendente* e de outro quando está *pago*. A troca de objeto ali acontece sozinha, a cada mudança de estado, e não vem de quem chama — o nome certo é [State](../state/explicacao.md). Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.

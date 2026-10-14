<!-- Gerado de pages/clean-code/comportamentais/iterator/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Iterator — Uso

*Clean Code / Design Pattern / Iterator*

Três situações em que o Iterator resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o iterador esconde de quem percorre.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Iterator. Quando dois casos se resolvem com o mesmo raciocínio — ler um arquivo linha a linha e consumir um cursor de banco, por exemplo — só um fica. Percorrer uma API paginada como se fosse uma lista é o mesmo raciocínio do exemplo 2, e já tem seção própria na [página de Uso do Adapter](../../estruturais/adapter/uso.md#paginacao). Sobraram três motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o iterador esconde |
|---|---|---|
| 1 | [Mais de uma ordem de percurso sobre a mesma árvore](#varios-percursos) | A estrutura e a ordem do percurso |
| 2 | [Uma fonte grande demais para carregar inteira](#fonte-grande) | Que a fonte não existe inteira em lugar nenhum |
| 3 | [Retomar um percurso do ponto onde ele parou](#retomar-de-onde-parou) | Onde, na fonte, o percurso está |

<a id="varios-percursos"></a>
## 1. Mais de uma ordem de percurso sobre a mesma árvore

**Situação.** Um explorador de arquivos na web. A busca precisa passar por tudo, em profundidade. A lista de "resultados mais próximos" precisa ir por níveis, em largura, para mostrar o que está perto da raiz primeiro. E o painel de tamanho só quer os arquivos, sem as pastas. A Explicação mostrou um percurso só; aqui há três, sobre a mesma árvore.

**sem o pattern — cada ordem é uma função que lê .filhos**

```typescript
function emProfundidade(no: No, saida: No[] = []): No[] {
  saida.push(no);
  no.filhos.forEach((f) => emProfundidade(f, saida));
  return saida;
}

function emLargura(raiz: No): No[] {
  const fila = [raiz], saida: No[] = [];
  while (fila.length) {
    const no = fila.shift()!;
    saida.push(no);
    fila.push(...no.filhos);
  }
  return saida;
}

function soArquivos(no: No): No[] {
  return no.filhos.length ? no.filhos.flatMap(soArquivos) : [no];
}

// as três leem .filhos direto. No dia em que a pasta carregar os filhos
// sob demanda, são três correções, uma em cada função.
```

**O que dói.** A estrutura da árvore está copiada em três lugares, e cada função monta a lista inteira antes de devolver, mesmo para mostrar só os dez primeiros resultados. Quem precisar de uma quarta ordem escreve uma quarta cópia.

**com o pattern — cada percurso é um método que devolve um iterador novo**

```typescript
class No implements Iterable<No> {
  constructor(readonly nome: string, private filhos: No[] = []) {}

  get ehArquivo() { return this.filhos.length === 0; }

  // o percurso padrão: em profundidade
  *[Symbol.iterator](): Generator<No> {
    yield this;
    for (const f of this.filhos) yield* f;
  }

  *emLargura(): Generator<No> {
    const fila: No[] = [this];
    while (fila.length) {
      const no = fila.shift()!;
      yield no;
      fila.push(...no.filhos);
    }
  }

  *arquivos(): Generator<No> {
    for (const no of this) if (no.ehArquivo) yield no;
  }
}

// os clientes escolhem a ordem e param quando quiserem
let vistos = 0;
for (const no of raiz.emLargura()) {
  mostrarResultado(no);
  if (++vistos === 10) break;
}
const bytes = [...raiz.arquivos()].reduce((s, a) => s + a.tamanho, 0);
```

**O que o iterador esconde.** A estrutura e a ordem. O campo `filhos` é lido em uma classe só, e cada percurso é um método que devolve um iterador novo, com posição própria. Dois percursos ao mesmo tempo, por exemplo a busca e o painel de tamanho, não se atrapalham. Uma ordem nova é um método novo, sem tocar em nenhum cliente.

> **Cuidado.** `raiz.emLargura()` devolve um gerador **novo** a cada chamada, mas o gerador em si é de uso único. Se você guardar o resultado em uma variável e percorrer duas vezes, a segunda passada vem vazia. Chame o método de novo, ou materialize com `[...]`.

<a id="fonte-grande"></a>
## 2. Uma fonte grande demais para carregar inteira

**Situação.** O log de acessos do dia tem 8 GB. O relatório conta os erros 500 e mostra os cinco primeiros, para quem está de plantão ver rápido. O arquivo nunca cabe em memória, e a fonte do "log de hoje" ainda está sendo escrita enquanto o relatório roda.

**sem o pattern — o arquivo inteiro vira uma lista**

```python
def erros_500(caminho):
    with open(caminho) as f:
        linhas = f.readlines()                  # 8 GB na memória
    return [l for l in linhas if " 500 " in l]

primeiros = erros_500("acessos.log")[:5]
```

**O que dói.** O processo estoura a memória antes de mostrar nada. Mesmo com memória de sobra, o relatório lê os 8 GB inteiros para exibir cinco linhas, e nada aparece até o fim da leitura.

**com o pattern — cada etapa é um iterador sobre o anterior**

```python
from itertools import islice

def linhas(caminho):
    with open(caminho) as f:
        for linha in f:                  # o arquivo já é um iterador: uma linha por vez
            yield linha.rstrip("\n")

def erros_500(linhas):
    return (l for l in linhas if " 500 " in l)

primeiros = list(islice(erros_500(linhas("acessos.log")), 5))   # lê só até achar cinco
```

**O que o iterador esconde.** Que a fonte não existe inteira em lugar nenhum. Cada linha nasce quando o consumidor pede e some quando ele passa para a próxima; a memória usada é a de uma linha. As etapas se encadeiam sem listas intermediárias, e o `islice` encerra tudo assim que acha a quinta, deixando o resto do arquivo sem ser lido.

O mesmo desenho serve para fontes que não têm fim: `itertools.count()`, um fluxo de eventos, um cursor de banco. Para o consumidor, o fim é só a hora em que ele para de pedir.

> **Cuidado.** A preguiça esconde *quando* o trabalho acontece. Um erro de leitura estoura dentro do laço de quem consome, e não onde o gerador foi criado. E, se você parar no meio, o arquivo fica aberto até o gerador ser descartado ou fechado.

<a id="retomar-de-onde-parou"></a>
## 3. Retomar um percurso do ponto onde ele parou

**Situação.** A importação noturna lê um CSV de dois milhões de linhas e grava cada registro no banco. Às vezes o processo cai no meio: um timeout, um deploy. Na noite seguinte, ela precisa continuar da linha em que parou, sem reprocessar o que já entrou.

**sem o pattern — reler tudo só para pular até o ponto**

```python
def importar(caminho, ultima_linha=0):
    with open(caminho, newline="") as f:
        for n, registro in enumerate(csv.reader(f)):
            if n < ultima_linha:
                continue                    # relê 1,35 milhão de linhas só para pular
            gravar(registro)
            if n % 1000 == 0:
                salvar_checkpoint(n)       # o controle misturado com a regra de importação
```

**O que dói.** Retomar custa o tempo de reler tudo que já foi processado. A posição do percurso vive em uma variável solta, `n`, no meio da regra de importação, ao lado de `gravar`. E ela é um número de linha, e não um ponto no arquivo: para continuar dali, é preciso reler desde o começo para chegar nele.

**com o pattern — o iterador expõe a própria posição**

```python
class LeitorDeRegistros:
    """Percorre um CSV de um registro por linha, e sabe voltar ao ponto onde estava."""

    def __init__(self, caminho, posicao=0):
        self._f = open(caminho, newline="")
        self._f.seek(posicao)             # pula direto, sem reler

    def __iter__(self):
        return self

    def __next__(self):
        linha = self._f.readline()
        if not linha:
            self._f.close()
            raise StopIteration
        return next(csv.reader([linha]))

    @property
    def posicao(self):
        return self._f.tell()           # o estado do percurso é do iterador

def importar(caminho):
    leitor = LeitorDeRegistros(caminho, posicao=checkpoint.carregar())
    for i, registro in enumerate(leitor, 1):
        gravar(registro)
        if i % 1000 == 0:
            checkpoint.salvar(leitor.posicao)
```

**O que o iterador esconde.** Onde, no arquivo, o percurso está. A importação trata a posição como um valor opaco: pede ao leitor, guarda, devolve ao construtor na vez seguinte. O `seek` e o `tell` ficam dentro do leitor, e a regra de importação não conhece arquivo nenhum. Aqui o iterador é uma classe de verdade, e não um gerador, porque o estado dele precisa ser *lido de fora*.

> **Cuidado.** Se o processo cair entre `gravar` e `checkpoint.salvar`, o último lote é gravado duas vezes na retomada. A importação precisa ser idempotente (um *upsert* pela chave do registro), ou gravar e salvar a posição na mesma transação.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três:

| Caso | Já coberto por |
|---|---|
| Percorrer uma API paginada como se fosse uma lista | 2 — fonte que não existe inteira; com o código completo no [Uso do Adapter, #6](../../estruturais/adapter/uso.md#paginacao) |
| Consumir o resultado de uma consulta ao banco com um cursor | 2 — as linhas chegam sob demanda |
| Gerar uma sequência sem fim (ids, números de uma série) | 2 — o consumidor é quem decide parar |
| Percorrer pastas e subpastas (`os.walk`) | 1 — estrutura em árvore escondida atrás de um percurso |
| Botões "anterior" e "próximo" sobre uma lista de resultados | 3 — a posição como um valor que o cliente guarda |

E um caso que parece Iterator, mas não é: `for item in lista:`. A lista da linguagem já é um iterável, e escrever uma classe de iterador para ela é só cerimônia. Veja a seção [Quando não usar](explicacao.md#quando-nao-usar) da explicação.

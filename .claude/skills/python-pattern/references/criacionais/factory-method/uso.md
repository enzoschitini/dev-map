<!-- Gerado de pages/clean-code/criacionais/factory-method/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Factory Method — Uso

*Clean Code / Design Pattern / Factory Method*

Quatro situações em que o Factory Method resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o método fábrica adia para a subclasse em cada caso.

<a id="como-escolhi"></a>
## Por que quatro

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para criar o objeto em uma subclasse. Quando dois casos se resolvem com o mesmo raciocínio — um relatório que escolhe o gráfico e um job que escolhe o parser, por exemplo —, só um fica. O Factory Method tem poucos motivos próprios, porque muitas situações em que ele parece servir se resolvem melhor com uma função ou com injeção. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o Factory Method adia |
|---|---|---|
| 1 | [O fluxo é o mesmo, só muda o objeto criado](#fluxo-fixo) | A escolha do parser, para cada job |
| 2 | [Uma biblioteca que não conhece as suas classes](#ponto-de-extensao) | A escolha do destino, para quem usa a biblioteca |
| 3 | [A mesma escolha de tipo em vários métodos](#tipo-em-um-lugar) | O tipo do documento, em um ponto só |
| 4 | [Uma costura para o teste, sem reescrever o código](#costura-de-teste) | A escolha do cliente, para o teste |

> **Nota.** O exemplo 4 usa `requests` e `datetime` com o formato real. Os demais usam módulos fictícios (`conciliacao`, `ClienteDeCupons`) no lugar de código interno.

<a id="fluxo-fixo"></a>
## 1. O fluxo é o mesmo, só muda o objeto criado

**Situação.** Todo dia, um job importa o extrato de cada banco: ler o arquivo, conciliar cada lançamento na conta do banco e registrar quantos entraram. Os passos são os mesmos. O Itaú entrega CNAB 240; o Nubank, CSV. Cada banco tem o seu job agendado, que já sabe qual é.

**sem o pattern — um importador que conhece todos os bancos**

```python
class ImportadorDeExtrato:
    def importar(self, banco, caminho):
        if banco == "itau":
            parser = ParserCnab240()
            conta = "ITAU-001"
        elif banco == "nubank":
            parser = ParserCsvNubank()
            conta = "NU-777"
        else:
            raise ValueError(banco)

        lancamentos = parser.ler(caminho)
        for l in lancamentos:
            conciliacao.registrar(conta, l)
        log.info("%s: %d lançamentos", banco, len(lancamentos))
```

**O que dói.** Cada banco novo reabre o método que também concilia e registra em log, e uma troca no CNAB do Itaú passa por um arquivo que o Nubank também usa. Testar a conciliação exige escolher um banco só para chegar nela. E o `if` de parser e conta tem tendência a crescer com as exceções de cada banco.

**com o pattern — o fluxo na base, o parser em cada subclasse**

```python
class ImportadorDeExtrato(ABC):
    conta: str

    def importar(self, caminho):
        parser = self.criar_parser()
        lancamentos = parser.ler(caminho)
        for l in lancamentos:
            conciliacao.registrar(self.conta, l)
        log.info("%s: %d lançamentos", self.conta, len(lancamentos))

    @abstractmethod
    def criar_parser(self) -> Parser: ...

class ImportadorItau(ImportadorDeExtrato):
    conta = "ITAU-001"

    def criar_parser(self):
        return ParserCnab240()

class ImportadorNubank(ImportadorDeExtrato):
    conta = "NU-777"

    def criar_parser(self):
        return ParserCsvNubank()

# cada job já sabe qual banco é
def job_itau():
    ImportadorItau().importar("/dados/itau/hoje.rem")
```

**O que o Factory Method adia.** A escolha do parser, para a subclasse. O fluxo — ler, conciliar, registrar — fica em um lugar só e não muda quando um banco entra. Um banco novo é uma classe nova com duas linhas, sem tocar em nenhuma outra.

> **Nota.** Se o nome do banco chegar de fora (uma fila, um campo no banco), alguém ainda precisa de `{"itau": ImportadorItau, "nubank": ImportadorNubank}[nome]` para escolher a subclasse. O `if` não some: ele sai do fluxo e vira uma tabela de uma linha por banco.

<a id="ponto-de-extensao"></a>
## 2. Uma biblioteca que não conhece as suas classes

**Situação.** A plataforma mantém uma biblioteca interna de tarefas agendadas: ela monta o arquivo, tenta enviar três vezes e emite uma métrica. Cada time dono de uma tarefa usa a biblioteca no próprio repositório, e cada um precisa mandar o arquivo para um lugar diferente.

**sem o pattern — a biblioteca importa todos os destinos**

```typescript
// dentro da biblioteca @acme/tarefas
import { DestinoS3 } from "./destinos/s3";
import { DestinoSftp } from "./destinos/sftp";

export class Tarefa {
  constructor(private tipoDeDestino: "s3" | "sftp") {}

  async executar(dados: Buffer) {
    const destino = this.tipoDeDestino === "s3" ? new DestinoS3() : new DestinoSftp();
    for (let i = 0; i < 3; i++) {
      try { await destino.enviar(dados); return; } catch {}
    }
    throw new Error("falha ao enviar");
  }
}
```

**O que dói.** O time de dados precisa de Google Cloud Storage. Para isso, ele abre um PR na biblioteca, espera uma versão nova e atualiza os doze serviços que a usam. A biblioteca acumula destinos e dependências (o SDK do GCS, o do Azure) que quase ninguém usa, e a união `"s3" | "sftp"` cresce a cada pedido.

**com o pattern — a biblioteca pede o destino, e quem usa o fornece**

```typescript
// dentro da biblioteca @acme/tarefas
export interface Destino {
  enviar(dados: Buffer): Promise<void>;
}

export abstract class Tarefa {
  protected abstract criarDestino(): Destino;

  async executar(dados: Buffer) {
    const destino = this.criarDestino();
    for (let i = 0; i < 3; i++) {
      try { await destino.enviar(dados); return; } catch {}
    }
    throw new Error("falha ao enviar");
  }
}

// no repositório do time de dados — a biblioteca nem foi tocada
class TarefaParaGcs extends Tarefa {
  protected criarDestino() {
    return new DestinoGcs("bucket-de-dados");
  }
}
```

**O que o Factory Method adia.** A escolha do destino, **para fora da biblioteca**. Aqui a razão não é só "evitar o `if`": o autor da biblioteca nem pode escrever o `new`, porque a classe que precisa ser criada ainda não existe e vai ser escrita por outro time. O retry e a métrica continuam em um lugar só.

> **Dica.** A biblioteca pode trazer uma implementação padrão em `criarDestino()` (por exemplo, o S3) em vez de deixá-lo abstrato. Quem não precisa de nada especial não sobrescreve nada.

<a id="tipo-em-um-lugar"></a>
## 3. A mesma escolha de tipo em vários métodos

**Situação.** Um editor tem operações que produzem um documento: `novo()`, `abrir()` e `duplicar()`. Hoje o editor suporta texto e planilha, e o time quer incluir apresentação.

**sem o pattern — a escolha do tipo, copiada em cada operação**

```python
class Editor:
    def novo(self, tipo):
        if tipo == "texto":
            return DocumentoTexto()
        elif tipo == "planilha":
            return DocumentoPlanilha()

    def abrir(self, caminho, tipo):
        if tipo == "texto":
            doc = DocumentoTexto()
        elif tipo == "planilha":
            doc = DocumentoPlanilha()
        doc.carregar(caminho)
        return doc

    def duplicar(self, doc):
        if isinstance(doc, DocumentoTexto):
            return DocumentoTexto(doc.conteudo)
        elif isinstance(doc, DocumentoPlanilha):
            return DocumentoPlanilha(doc.conteudo)
```

**O que dói.** "Apresentação" exige achar e editar três métodos, e o `duplicar()` que ficar para trás devolve `None` sem avisar. A cadeia aparece em toda operação nova (`importar`, `converter`), sempre com o mesmo desenho.

**com o pattern — o tipo é decidido uma vez, e todas as operações o usam**

```python
class Editor(ABC):
    @abstractmethod
    def criar_documento(self) -> Documento: ...   # o único ponto de decisão

    def novo(self):
        return self.criar_documento()

    def abrir(self, caminho):
        doc = self.criar_documento()
        doc.carregar(caminho)
        return doc

    def duplicar(self, doc):
        copia = self.criar_documento()
        copia.conteudo = doc.conteudo
        return copia

class EditorDeTexto(Editor):
    def criar_documento(self):
        return DocumentoTexto()

class EditorDePlanilha(Editor):
    def criar_documento(self):
        return DocumentoPlanilha()
```

**O que o Factory Method adia.** O tipo do documento, e o adia **uma vez só**. A diferença para o exemplo 1 é a quantidade: ali, a variação aparece em um ponto do fluxo; aqui, várias operações independentes precisam concordar sobre o tipo. Com o método fábrica, elas concordam porque usam o mesmo método. "Apresentação" é uma classe nova, e nenhum método existente é aberto.

<a id="costura-de-teste"></a>
## 4. Uma costura para o teste, sem reescrever o código

**Situação.** O `ServicoDeCupom` consulta uma API para validar o código do cupom. Ele vem de um código legado, é instanciado por um framework de injeção que só sabe chamar `ServicoDeCupom()`, e o construtor não pode ganhar parâmetros agora.

**sem o pattern — a chamada de rede mora no meio do método**

```python
class ServicoDeCupom:
    def aplicar(self, pedido, codigo):
        resp = requests.get(f"https://cupons.exemplo.com/{codigo}", timeout=3)
        cupom = resp.json()
        if datetime.now() > datetime.fromisoformat(cupom["expira_em"]):
            raise CupomExpirado(codigo)
        pedido.desconto = cupom["percentual"]

# o teste precisa trocar o requests do módulo inteiro
@patch("servico_de_cupom.requests.get")
def test_cupom_valido(get):
    get.return_value.json.return_value = {"expira_em": "2099-01-01", "percentual": 10}
    ...
```

**O que dói.** O `@patch` aponta para um caminho de módulo: se alguém trocar `requests` por `httpx` ou mover a importação, o teste quebra sem que o comportamento tenha mudado. E o teste conhece o formato da resposta HTTP, não a regra do cupom.

**com o pattern — a criação do cliente vira um método que o teste sobrescreve**

```python
class ServicoDeCupom:
    def criar_cliente(self):
        return ClienteDeCupons("https://cupons.exemplo.com")

    def aplicar(self, pedido, codigo):
        cupom = self.criar_cliente().buscar(codigo)
        if datetime.now() > datetime.fromisoformat(cupom.expira_em):
            raise CupomExpirado(codigo)
        pedido.desconto = cupom.percentual

# no teste: uma subclasse de três linhas, sem patch
class ServicoDeCupomDeTeste(ServicoDeCupom):
    def __init__(self, cupons):
        self._cupons = cupons

    def criar_cliente(self):
        return ClienteFalso(self._cupons)

def test_cupom_valido():
    servico = ServicoDeCupomDeTeste({"BEMVINDO": Cupom("2099-01-01", 10)})
    pedido = Pedido()
    servico.aplicar(pedido, "BEMVINDO")
    assert pedido.desconto == 10
```

**O que o Factory Method adia.** A escolha do cliente, **para o teste**. O construtor continua o mesmo, o framework continua chamando `ServicoDeCupom()`, e o teste fala em cupom, não em HTTP. A parte do `datetime` ainda usa o relógio real; funciona porque o teste usa uma data longe no futuro, mas é a próxima costura natural (`agora()`).

> **Cuidado.** Isso é uma **costura**: um jeito de abrir uma porta onde você não pode mudar o construtor. Se pode, receba o cliente por parâmetro: `ServicoDeCupom(cliente)` é mais simples e não exige uma subclasse só para o teste.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos quatro ou porque a resposta certa é outro padrão:

| Caso | Já coberto por |
|---|---|
| Criar inimigos diferentes em cada fase de um jogo | 1 — fluxo fixo, objeto variável |
| `get_form_class` e `get_queryset` de views do Django, `createDocument` de frameworks | 2 — ponto de extensão de quem usa |
| Criar o cliente HTTP, o relógio ou o gerador de IDs para trocá-los em teste | 4 — costura de teste |
| Escolher o leitor pela extensão do arquivo (`.csv`, `.xlsx`) | Fábrica simples: um mapa de extensão para classe. Veja "Quando não usar" |
| Criar botão e janela com o visual do sistema operacional | Abstract Factory: dois produtos que precisam combinar |

E um caso que parece Factory Method, mas usa só o nome: os **construtores nomeados** como `Dinheiro.de_centavos(1050)` ou `Data.hoje()`, em Python normalmente um `@classmethod`. Em Java e Python eles são chamados de "factory methods", mas não há criador, subclasse ou decisão adiada: é só um construtor com nome. São úteis, mas é outra coisa — veja a diferença na seção [Parecidos](explicacao.md#parecidos) da explicação.

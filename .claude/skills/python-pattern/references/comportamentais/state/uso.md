<!-- Gerado de pages/clean-code/comportamentais/state/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# State — Uso

*Clean Code / Design Pattern / State*

Três situações em que o State resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o estado absorve.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o State. O ciclo de vida de um pedido, o caso mais comum, já é o exemplo da [Explicação](explicacao.md#o-problema), e outros fluxos de aprovação se resolvem com o mesmo raciocínio. Sobraram três motivos aqui. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o estado absorve |
|---|---|---|
| 1 | [O mesmo gesto, uma ferramenta diferente por vez](#ferramenta-ativa) | O que fazer com cada gesto, e os dados do gesto em andamento |
| 2 | [Flags que descrevem a fase juntas](#disjuntor) | Em que modo de falha o sistema está, e o que ele guarda para decidir |
| 3 | [Algo que precisa acontecer ao entrar e ao sair](#reserva-com-prazo) | O que fazer em toda entrada e saída, por qualquer caminho |

<a id="ferramenta-ativa"></a>
## 1. O mesmo gesto, uma ferramenta diferente por vez

**Situação.** Um editor de imagens no navegador. O canvas recebe três eventos do mouse: pressionar, mover e soltar. O que eles fazem depende da ferramenta ativa: o pincel risca, a seleção desenha um retângulo, e a pessoa troca de ferramenta quando quiser.

**sem o pattern — cada handler testa a ferramenta, e as variáveis soltas vazam**

```typescript
let ferramenta: "pincel" | "borracha" | "selecao" = "pincel";
let desenhando = false;
let inicio: { x: number; y: number } | null = null;

canvas.addEventListener("mousedown", (e) => {
  if (ferramenta === "pincel")        { desenhando = true; tracar(e.offsetX, e.offsetY, cor); }
  else if (ferramenta === "borracha") { desenhando = true; apagar(e.offsetX, e.offsetY); }
  else if (ferramenta === "selecao")  { inicio = { x: e.offsetX, y: e.offsetY }; }
});

canvas.addEventListener("mousemove", (e) => {
  if (ferramenta === "pincel" && desenhando)        tracar(e.offsetX, e.offsetY, cor);
  else if (ferramenta === "borracha" && desenhando) apagar(e.offsetX, e.offsetY);
  else if (ferramenta === "selecao" && inicio)      retanguloDeSelecao(inicio, e);
});

canvas.addEventListener("mouseup", (e) => {
  desenhando = false;
  if (ferramenta === "selecao" && inicio) { confirmarSelecao(inicio, e); inicio = null; }
});
```

**O que dói.** Cada ferramenta nova obriga a abrir os três handlers. As variáveis `desenhando` e `inicio` são de uma ferramenta, mas vivem no escopo de todas: troque da seleção para o pincel no meio de um arrasto e o estado de uma passa para a outra. E o que o pincel faz está espalhado em três lugares.

**com o pattern — cada ferramenta é um objeto, com o próprio estado**

```typescript
interface Ferramenta {
  aoPressionar(x: number, y: number): void;
  aoMover(x: number, y: number): void;
  aoSoltar(x: number, y: number): void;
}

class Pincel implements Ferramenta {
  private desenhando = false;
  constructor(private cor: string) {}

  aoPressionar(x: number, y: number) { this.desenhando = true; tracar(x, y, this.cor); }
  aoMover(x: number, y: number)     { if (this.desenhando) tracar(x, y, this.cor); }
  aoSoltar()                      { this.desenhando = false; }
}

class Selecao implements Ferramenta {
  private inicio?: { x: number; y: number };

  aoPressionar(x: number, y: number) { this.inicio = { x, y }; }
  aoMover(x: number, y: number)     { if (this.inicio) retanguloDeSelecao(this.inicio, { x, y }); }
  aoSoltar(x: number, y: number) {
    if (this.inicio) confirmarSelecao(this.inicio, { x, y });
    this.inicio = undefined;
  }
}

class Editor {
  private ferramenta: Ferramenta = new Pincel("#000");

  trocar(nova: Ferramenta) { this.ferramenta = nova; }   // o arrasto da anterior morre com ela

  ligar(canvas: HTMLCanvasElement) {
    canvas.addEventListener("mousedown", (e) => this.ferramenta.aoPressionar(e.offsetX, e.offsetY));
    canvas.addEventListener("mousemove", (e) => this.ferramenta.aoMover(e.offsetX, e.offsetY));
    canvas.addEventListener("mouseup",   (e) => this.ferramenta.aoSoltar(e.offsetX, e.offsetY));
  }
}
```

**O que o estado absorve.** O que fazer com cada gesto *e* os dados do gesto em andamento. O `desenhando` pertence ao pincel e o `inicio` pertence à seleção; trocar de ferramenta descarta o objeto e o que ele guardava. O `Editor` fica com três linhas de delegação, e uma ferramenta nova é uma classe nova.

> **Nota.** Este é o caso mais próximo do Strategy: quem troca de ferramenta é a pessoa, de fora. O que o mantém como State é que cada ferramenta guarda dados de um gesto em andamento, e esses dados nascem e morrem com ela. Se as ferramentas não guardassem nada, seria Strategy.

<a id="disjuntor"></a>
## 2. Flags que descrevem a fase juntas

**Situação.** O serviço de cotação de frete cai de vez em quando, e cada queda deixa o checkout esperando um timeout. A defesa é um disjuntor: depois de cinco falhas seguidas ele *abre* e passa a falhar rápido, sem chamar o serviço, por 30 segundos. Depois deixa passar uma tentativa de teste: se der certo, volta ao normal; se falhar, abre de novo.

**sem o pattern — três campos que juntos dizem "em que fase estou"**

```python
class ClienteFrete:
    def __init__(self):
        self.falhas = 0
        self.aberto = False
        self.meio_aberto = False
        self.aberto_desde = None

    def cotar(self, pedido):
        if self.aberto:
            if time.monotonic() - self.aberto_desde > 30:
                self.aberto = False
                self.meio_aberto = True
            else:
                raise ServicoIndisponivel()
        try:
            resp = frete_api.cotar(pedido)
        except Exception:
            self.falhas += 1
            if self.meio_aberto or self.falhas >= 5:
                self.aberto, self.meio_aberto = True, False
                self.aberto_desde = time.monotonic()
            raise
        self.falhas = 0
        self.meio_aberto = False
        return resp
```

**O que dói.** A fase é *inferida* de três campos, e nada impede que `aberto` e `meio_aberto` sejam verdadeiros juntos. Cada regra nova (um limite de tempo, um contador de sucessos) é mais um `if` nesse método de vinte linhas, e testá-lo exige montar combinações de campos. E `aberto_desde` sobra preenchido quando o disjuntor não está aberto.

**com o pattern — três fases, cada uma com os dados que são dela**

```python
class Disjuntor:
    def __init__(self, chamada, limite=5, espera=30):
        self.chamada, self.limite, self.espera = chamada, limite, espera
        self._estado = Fechado()

    def executar(self, *args):
        return self._estado.executar(self, *args)

    def ir_para(self, estado):
        self._estado = estado

class Fechado:
    def __init__(self):
        self._falhas = 0                         # só existe aqui

    def executar(self, d, *args):
        try:
            resp = d.chamada(*args)
        except Exception:
            self._falhas += 1
            if self._falhas >= d.limite:
                d.ir_para(Aberto())
            raise
        self._falhas = 0
        return resp

class Aberto:
    def __init__(self):
        self._desde = time.monotonic()           # só existe aqui

    def executar(self, d, *args):
        if time.monotonic() - self._desde < d.espera:
            raise ServicoIndisponivel()          # falha rápido, sem chamar
        d.ir_para(MeioAberto())
        return d.executar(*args)

class MeioAberto:
    def executar(self, d, *args):
        try:
            resp = d.chamada(*args)
        except Exception:
            d.ir_para(Aberto())
            raise
        d.ir_para(Fechado())
        return resp

cotar = Disjuntor(frete_api.cotar).executar
```

**O que o estado absorve.** A fase e os dados que só fazem sentido nela. As falhas pertencem a `Fechado`, e o instante de abertura pertence a `Aberto`; cada um nasce zerado quando a fase começa, sem ninguém "limpar flags". A combinação "aberto e meio-aberto ao mesmo tempo" deixa de ser representável. As transições são disparadas pelo *resultado* das chamadas, e cada fase tem pouco mais de dez linhas.

> **Cuidado.** Com várias threads, as transições competem: duas falhas simultâneas podem abrir o disjuntor duas vezes, ou deixar passar duas tentativas no meio-aberto. Este exemplo não protege isso. Em produção, use uma biblioteca de circuit breaker madura em vez de uma versão escrita à mão.

<a id="reserva-com-prazo"></a>
## 3. Algo que precisa acontecer ao entrar e ao sair

**Situação.** A venda de ingressos reserva o lugar por 15 minutos. Ao reservar, um timer é armado; se a pessoa não pagar, o lugar volta para a venda. Se pagar, ou se cancelar, o timer precisa ser desarmado, senão ele devolve à venda um lugar que já foi pago ou já foi vendido a outra pessoa.

**sem o pattern — o timer cancelado em cada caminho de saída, à mão**

```python
class Ingresso:
    def __init__(self):
        self.status = "disponivel"
        self._timer = None

    def reservar(self):
        self.status = "reservado"
        self._timer = threading.Timer(15 * 60, self.expirar)
        self._timer.start()

    def pagar(self):
        self.status = "pago"
        self._timer.cancel()

    def cancelar(self):
        self.status = "disponivel"          # esqueceu o timer: ele vai expirar o lugar de outra pessoa

    def expirar(self):
        self.status = "disponivel"
```

**O que dói.** A limpeza do timer está em cada caminho de saída de "reservado", e um dos caminhos a esqueceu. O erro só aparece de madrugada, quando um lugar vendido a outra pessoa é devolvido à venda por um timer velho. E o próximo caminho de saída, como "reserva removida pelo administrador", é mais um lugar onde lembrar.

**com o pattern — entrar e sair são ganchos do estado**

```python
class Ingresso:
    def __init__(self):
        self._estado = Disponivel()

    def ir_para(self, novo):
        self._estado.sair(self)         # toda saída passa por aqui
        self._estado = novo
        novo.entrar(self)                # toda entrada, também

    def reservar(self): self._estado.reservar(self)
    def pagar(self):    self._estado.pagar(self)
    def cancelar(self): self._estado.cancelar(self)
    def expirar(self):  self._estado.expirar(self)

class Estado:
    def entrar(self, ingresso): ...
    def sair(self, ingresso): ...
    def reservar(self, ingresso): raise TransicaoInvalida(type(self).__name__)
    def pagar(self, ingresso):    raise TransicaoInvalida(type(self).__name__)
    def cancelar(self, ingresso): raise TransicaoInvalida(type(self).__name__)
    def expirar(self, ingresso):  raise TransicaoInvalida(type(self).__name__)

class Disponivel(Estado):
    def reservar(self, i): i.ir_para(Reservado())

class Reservado(Estado):
    def entrar(self, i):
        self._timer = threading.Timer(15 * 60, i.expirar)
        self._timer.start()

    def sair(self, i):
        self._timer.cancel()             # qualquer saída desarma o timer

    def pagar(self, i):    i.ir_para(Pago())
    def cancelar(self, i): i.ir_para(Disponivel())
    def expirar(self, i):  i.ir_para(Disponivel())

class Pago(Estado): ...
```

**O que o estado absorve.** O que precisa acontecer ao entrar e ao sair, por qualquer caminho. O timer é armado em `entrar` e desarmado em `sair`, uma vez, dentro do estado a que pertence. Um caminho de saída novo, como "removida pelo administrador", passa por `ir_para` e herda a limpeza sem ninguém lembrar.

> **Cuidado.** `sair` e `entrar` rodam no meio da transição. Se um deles falhar, o contexto fica entre dois estados. Defina a ordem e o que acontece em caso de erro, e mantenha esses ganchos curtos e idempotentes.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na Explicação):

| Caso | Já coberto por |
|---|---|
| Ciclo de vida de pedido, documento, assinatura ou chamado | O exemplo da [Explicação](explicacao.md#o-problema) |
| Catraca, máquina de venda, semáforo | A Explicação — as mesmas transições entre fases, com outros nomes |
| Personagem de jogo (parado, andando, pulando) | 1 — o mesmo gesto tem efeitos diferentes por modo |
| Conexão com reconexão e espera crescente | 2 — fases que dependem do resultado das tentativas |
| Sessão de usuário (anônima, logada, expirada) | 3 — limpar o token e armar o prazo ao entrar e sair |

E um caso que parece State, mas não é: uma coluna `status` no banco, com uma tabela que diz quais transições são válidas. Se as fases não têm comportamento próprio, só permissão, a tabela é mais curta que as classes — veja a seção [Quando não usar](explicacao.md#quando-nao-usar) da explicação.

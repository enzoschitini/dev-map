<!-- Gerado de pages/clean-code/criacionais/abstract-factory/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Abstract Factory — Uso

*Clean Code / Design Pattern / Abstract Factory*

Três situações em que a Abstract Factory resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a fábrica garante em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para criar as peças por uma fábrica. Quando dois casos se resolvem com o mesmo raciocínio — dialetos de SQL e componentes por sistema operacional, por exemplo — só um fica. A Abstract Factory tem poucos motivos próprios, e a lista é curta de propósito. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a Abstract Factory garante |
|---|---|---|
| 1 | [Peças que só funcionam juntas](#pecas-que-combinam) | Que as peças são da mesma família |
| 2 | [Peças que precisam do mesmo contexto](#contexto-compartilhado) | Que todas usam a mesma conexão |
| 3 | [Uma família diferente a cada pedido](#familia-por-pedido) | Que a escolha existe em um lugar só |

> **Nota.** O exemplo 2 usa `psycopg2` com a chamada simplificada. Os repositórios e as classes fiscais são fictícios; o objetivo é mostrar a estrutura.

<a id="pecas-que-combinam"></a>
## 1. Peças que só funcionam juntas

**Situação.** A tela de cadastro tem tema claro e escuro. Os componentes — botão, campo de texto e aviso — são desenhados em pares: o campo escuro tem fundo escuro e texto claro, e o aviso escuro assume que está sobre esse fundo. Cada componente é montado onde é usado, a partir do tema.

**sem o pattern — um ternário por componente**

```typescript
function montarFormulario(tema: "claro" | "escuro") {
  const botao = tema === "claro" ? new BotaoClaro() : new BotaoEscuro();
  const campo = tema === "claro" ? new CampoClaro() : new CampoEscuro();
  const aviso = tema === "escuro" ? new AvisoClaro() : new AvisoEscuro();   // invertido
  return { botao, campo, aviso };
}
```

**O que dói.** O ternário invertido do aviso passa em qualquer leitura rápida, e o resultado é texto claro sobre fundo claro, só no tema escuro. Cada tela repete esses três ternários, então o erro tem três chances de nascer em cada uma. E um tema novo (alto contraste) é um terceiro ramo em cada ternário, em todas as telas.

**com o pattern — a escolha do tema é a escolha de uma fábrica**

```typescript
interface FabricaDeComponentes {
  criarBotao(): Botao;
  criarCampo(): Campo;
  criarAviso(): Aviso;
}

class ComponentesClaros implements FabricaDeComponentes {
  criarBotao() { return new BotaoClaro(); }
  criarCampo() { return new CampoClaro(); }
  criarAviso() { return new AvisoClaro(); }
}

class ComponentesEscuros implements FabricaDeComponentes {
  criarBotao() { return new BotaoEscuro(); }
  criarCampo() { return new CampoEscuro(); }
  criarAviso() { return new AvisoEscuro(); }
}

function montarFormulario(f: FabricaDeComponentes) {
  return { botao: f.criarBotao(), campo: f.criarCampo(), aviso: f.criarAviso() };
}

// a escolha do tema, uma vez
const fabrica = tema === "escuro" ? new ComponentesEscuros() : new ComponentesClaros();
montarFormulario(fabrica);
```

**O que a fábrica garante.** Que as peças são **da mesma família**. Para pôr um aviso claro em uma tela escura, alguém precisaria escrever isso de propósito, fora da fábrica. O tema novo é uma classe nova, e `montarFormulario` nem é aberta.

> **Cuidado.** Repare no preço: um componente novo (`criarTooltip()`) obriga a mexer na interface e em **cada** fábrica. A Abstract Factory facilita incluir temas, não incluir tipos de componente. Se os tipos mudam toda semana, o padrão vai incomodar.

<a id="contexto-compartilhado"></a>
## 2. Peças que precisam do mesmo contexto

**Situação.** Fechar um pedido grava o pedido e soma os pontos de fidelidade do cliente. Os dois gravam no PostgreSQL, por dois repositórios, e precisam acontecer juntos: ou os dois, ou nenhum.

**sem o pattern — cada repositório abre a sua própria conexão**

```python
class ServicoDePedidos:
    def fechar(self, pedido):
        pedidos = RepositorioDePedidos(psycopg2.connect(DSN))
        clientes = RepositorioDeClientes(psycopg2.connect(DSN))   # outra conexão, outra transação

        pedidos.salvar(pedido)                              # confirmado aqui
        clientes.somar_pontos(pedido.cliente_id, pedido.total)   # e se isto falhar?
```

**O que dói.** São duas conexões, portanto duas transações. Se a segunda operação falha, o pedido já está gravado e o cliente não ganhou os pontos: o banco fica inconsistente, sem erro visível. E para trocar o banco em teste, é preciso achar cada `connect`.

**com o pattern — a fábrica guarda a conexão e a entrega às peças**

```python
class FabricaDeRepositorios(ABC):
    @abstractmethod
    def pedidos(self) -> RepositorioDePedidos: ...
    @abstractmethod
    def clientes(self) -> RepositorioDeClientes: ...
    @abstractmethod
    def confirmar(self) -> None: ...
    @abstractmethod
    def desfazer(self) -> None: ...

class RepositoriosPostgres(FabricaDeRepositorios):
    def __init__(self, dsn):
        self._conn = psycopg2.connect(dsn)     # uma conexão para a família toda

    def pedidos(self):
        return PedidosPostgres(self._conn)

    def clientes(self):
        return ClientesPostgres(self._conn)

    def confirmar(self):
        self._conn.commit()

    def desfazer(self):
        self._conn.rollback()

class ServicoDePedidos:
    def __init__(self, repos: FabricaDeRepositorios):
        self._repos = repos

    def fechar(self, pedido):
        try:
            self._repos.pedidos().salvar(pedido)
            self._repos.clientes().somar_pontos(pedido.cliente_id, pedido.total)
            self._repos.confirmar()
        except Exception:
            self._repos.desfazer()
            raise
```

**O que a fábrica garante.** Que todas as peças usam **o mesmo contexto**. A diferença para o exemplo 1 é o que as peças têm em comum: ali, a aparência; aqui, um recurso que existe uma vez por fábrica — a conexão. Os repositórios não sabem se são Postgres ou SQLite, mas todos sabem que a conexão é a da fábrica, e o `commit` vale para os dois.

<a id="familia-por-pedido"></a>
## 3. Uma família diferente a cada pedido

**Situação.** A loja vende para o Brasil e para Portugal. Cada pedido gera um documento fiscal, e o país muda tudo ao mesmo tempo: o cálculo do imposto (ICMS ou IVA), o documento (nota fiscal ou fatura) e a numeração. As operações que mexem nisso são várias: emitir, cancelar e reemitir.

**sem o pattern — o país decide cada peça, em cada operação**

```python
def emitir(pedido):
    if pedido.pais == "BR":
        imposto = ImpostoBR().calcular(pedido)
        numero = NumeracaoBR().proximo()
        return NotaFiscalBR(pedido, imposto, numero)
    elif pedido.pais == "PT":
        imposto = IvaPT().calcular(pedido)
        numero = NumeracaoPT().proximo()
        return FaturaPT(pedido, imposto, numero)

def reemitir(pedido):
    if pedido.pais == "BR":
        ...   # mesmos três ramos, de novo
    elif pedido.pais == "PT":
        ...

def cancelar(pedido):
    if pedido.pais == "BR":
        ...   # e uma terceira vez
```

**O que dói.** Um país novo (Espanha) é um ramo em **cada** função, e esquecer uma delas só aparece quando um pedido espanhol cai exatamente nela. As regras de um país ficam picotadas em várias funções, e nenhuma delas mostra como é "ser a Fatura de Portugal" por inteiro.

**com o pattern — o país escolhe a fábrica, e as operações a usam**

```python
class FabricaFiscal(ABC):
    @abstractmethod
    def criar_calculador(self) -> CalculadorDeImposto: ...
    @abstractmethod
    def criar_numeracao(self) -> Numeracao: ...
    @abstractmethod
    def criar_documento(self, pedido, imposto, numero) -> DocumentoFiscal: ...

class FabricaFiscalBR(FabricaFiscal):
    def criar_calculador(self):
        return ImpostoBR()

    def criar_numeracao(self):
        return NumeracaoBR()

    def criar_documento(self, pedido, imposto, numero):
        return NotaFiscalBR(pedido, imposto, numero)

# FabricaFiscalPT: a mesma forma, com IvaPT, NumeracaoPT e FaturaPT

# o único lugar que conhece os países
FABRICAS = {"BR": FabricaFiscalBR(), "PT": FabricaFiscalPT()}

def emitir(pedido):
    f = FABRICAS[pedido.pais]
    imposto = f.criar_calculador().calcular(pedido)
    numero = f.criar_numeracao().proximo()
    return f.criar_documento(pedido, imposto, numero)
```

**O que a fábrica garante.** Que a escolha acontece **uma vez por pedido**, e todo o resto fala com a interface. A diferença para os exemplos anteriores é a fonte da escolha: ali, o tema ou o ambiente é decidido na inicialização; aqui, o país vem do pedido, e a fábrica é um parâmetro que vai de função em função. Espanha é uma classe e uma linha no dicionário — nenhuma operação é aberta.

O dicionário ainda é uma escolha por dado. A diferença é que ele existe *uma vez*, e que entrega a família inteira; as três operações não perguntam mais "qual país".

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três:

| Caso | Já coberto por |
|---|---|
| Dialetos de SQL: aspas, paginação e upsert de cada banco | 1 — peças que só combinam em conjunto |
| Janela, menu e diálogo com a aparência de cada sistema operacional | 1 — peças que só combinam em conjunto |
| Unit of Work: repositórios que compartilham uma transação | 2 — mesmo contexto |
| SDK de um fornecedor: cliente, cobrança e reembolso com a mesma chave de API | 2 — mesmo contexto |
| Formatação de endereço, telefone e moeda por localidade | 3 — família por pedido |
| Inimigos, obstáculos e itens de cada fase de um jogo | 3 — família escolhida em tempo de execução |
| Escolher um único objeto pela configuração | Factory Method, ou uma função fábrica; não há família |

E um caso que parece Abstract Factory, mas não é: um módulo `fabricas.py` com funções soltas (`criar_botao()`, `criar_campo()`), sem uma interface que garanta que as peças vêm do mesmo conjunto. Agrupa criadores, mas não impede a mistura — que é a única coisa que o padrão acrescenta. A seção [Parecidos](explicacao.md#parecidos) da explicação mostra a diferença para o Factory Method.

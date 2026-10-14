<!-- Gerado de pages/clean-code/estruturais/decorator/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Decorator — Uso

*Clean Code / Design Pattern / Decorator*

Três situações em que o Decorator resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o decorador acrescenta em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Decorator. Cache, log, retry, métrica e trace sobre um cliente são o mesmo raciocínio, e ele já está inteiro no exemplo da [explicação](explicacao.md#implementacao). Comprimir ou criptografar um stream é o mesmo raciocínio do segundo exemplo. Sobraram três motivos, e os casos que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o decorador acrescenta |
|---|---|---|
| 1 | [Adicionais que o cliente escolhe no checkout](#adicionais-no-checkout) | Um valor e uma descrição, na ordem escolhida |
| 2 | [Upload que precisa de limite e de hash](#upload-com-limite) | Limite e medição sobre um objeto que não é seu |
| 3 | [Permissão e métrica em dezenas de handlers](#funcoes-de-handler) | O que acontece em volta de uma função |

<a id="adicionais-no-checkout"></a>
## 1. Adicionais que o cliente escolhe no checkout

**Situação.** O cinema vende ingresso inteira ou meia, e o cliente pode somar adicionais na compra: sessão em 3D, assento VIP e combo de pipoca. A taxa de serviço de 10% incide sobre o total. A tela de resumo mostra o preço e uma descrição ("Meia + 3D + combo"), e os dois precisam bater.

**sem o pattern — um booleano por adicional, em duas funções**

```python
def preco_do_ingresso(sessao, meia=False, tres_d=False, vip=False, combo=False):
    preco = sessao.preco_base
    if meia:
        preco = preco / 2        # a meia vale sobre o base, não sobre os extras
    if tres_d:
        preco += 8
    if vip:
        preco += 25
    if combo:
        preco += 22
    return preco * Decimal("1.10")

def descricao_do_ingresso(meia=False, tres_d=False, vip=False, combo=False):
    partes = ["Meia" if meia else "Inteira"]
    if tres_d:
        partes.append("3D")
    if combo:
        partes.append("combo")       # e o vip? esqueceram aqui
    return " + ".join(partes)
```

**O que dói.** Preço e descrição têm os mesmos `if` em duas funções, e já divergiram: o VIP está no preço e não está na descrição. Cada adicional novo é um parâmetro em todos os chamadores. Quatro booleanos são 16 combinações para testar. E a regra "meia vale sobre o base" só existe pela posição de uma linha.

**com o pattern — cada adicional embrulha o ingresso e altera o resultado**

```python
class Ingresso(ABC):
    @abstractmethod
    def preco(self) -> Decimal: ...
    @abstractmethod
    def descricao(self) -> str: ...

class Inteira(Ingresso):
    def __init__(self, sessao):
        self._sessao = sessao

    def preco(self):
        return self._sessao.preco_base

    def descricao(self):
        return "Inteira"

class Meia(Inteira):
    def preco(self):
        return self._sessao.preco_base / 2

    def descricao(self):
        return "Meia"

class Adicional(Ingresso):
    NOME: str

    def __init__(self, interno: Ingresso):
        self._interno = interno

    def descricao(self):
        return f"{self._interno.descricao()} + {self.NOME}"

class Em3D(Adicional):
    NOME = "3D"
    def preco(self): return self._interno.preco() + Decimal(8)

class Vip(Adicional):
    NOME = "VIP"
    def preco(self): return self._interno.preco() + Decimal(25)

class Combo(Adicional):
    NOME = "combo"
    def preco(self): return self._interno.preco() + Decimal(22)

class TaxaDeServico(Adicional):
    NOME = "taxa"
    def preco(self): return self._interno.preco() * Decimal("1.10")

# a ordem dos adicionais fica escrita aqui, e em lugar nenhum mais
ADICIONAIS = {"3d": Em3D, "vip": Vip, "combo": Combo}

def montar_ingresso(sessao, meia: bool, escolhidos: set[str]) -> Ingresso:
    ingresso = Meia(sessao) if meia else Inteira(sessao)
    for nome, classe in ADICIONAIS.items():
        if nome in escolhidos:
            ingresso = classe(ingresso)
    return TaxaDeServico(ingresso)     # por último: incide sobre tudo
```

**O que o decorador acrescenta.** Aqui o decorador **muda o resultado**, em vez de só observar: soma ao preço e acrescenta à descrição, na mesma classe e portanto sem divergir. Os exemplos de cache e log não mudam o que a chamada devolve; estes mudam. A pilha é montada em tempo de execução, a partir do que o cliente marcou na tela, com um laço. Um adicional novo é uma classe e uma linha no dicionário.

> **Cuidado.** Quando há percentuais, a ordem muda o preço: 10% de taxa antes de somar o combo dá um valor, depois dá outro. Por isso a ordem está em um único lugar, com um comentário, e não depende da ordem em que o cliente clicou.

<a id="upload-com-limite"></a>
## 2. Upload que precisa de limite e de hash

**Situação.** O endpoint de importação recebe um arquivo de até 10 MB e precisa guardar o hash SHA-256 dele para auditoria. O objeto de arquivo vem do framework (`request.files`), e o destino é uma função da biblioteca padrão que só sabe chamar `.read()`.

**sem o pattern — lê tudo para a memória e depois confere**

```python
def importar(arquivo, destino):
    dados = arquivo.read()                  # e se vierem 2 GB?
    if len(dados) > LIMITE:
        raise ArquivoGrande(LIMITE)
    sha = hashlib.sha256(dados).hexdigest()
    destino.write(dados)
    return sha
```

**O que dói.** A checagem acontece *depois* de o arquivo todo estar na memória, que é justamente o que o limite devia evitar. Se o código trocar para leitura em blocos, o contador e o hash entram no meio do laço, junto da cópia. E `shutil.copyfileobj`, que já copia em blocos, deixa de poder ser usado.

**com o pattern — dois leitores que embrulham o arquivo e falam .read()**

```python
class LeitorLimitado:
    def __init__(self, origem, limite: int):
        self._origem, self._limite, self._lidos = origem, limite, 0

    def read(self, n=-1):
        bloco = self._origem.read(n)
        self._lidos += len(bloco)
        if self._lidos > self._limite:
            raise ArquivoGrande(self._limite)
        return bloco

class LeitorComHash:
    def __init__(self, origem):
        self._origem, self._sha = origem, hashlib.sha256()

    def read(self, n=-1):
        bloco = self._origem.read(n)
        self._sha.update(bloco)
        return bloco

    def hexdigest(self):
        return self._sha.hexdigest()

def importar(arquivo, destino):
    lido = LeitorComHash(LeitorLimitado(arquivo, LIMITE))
    shutil.copyfileobj(lido, destino)   # em blocos; estoura no meio, sem carregar tudo
    return lido.hexdigest()
```

**O que o decorador acrescenta.** Limite e medição sobre um objeto **que não é seu**, sem tocar nele nem no consumidor. `copyfileobj` só chama `.read(n)`, e o decorador responde a isso, então o consumidor não sabe que há camadas. O que este exemplo ensina e o anterior não: o decorador guarda **estado** enquanto os dados passam (bytes lidos, hash parcial), e age *durante* a leitura, não antes nem depois. A biblioteca padrão usa a mesma forma: `gzip.GzipFile(fileobj=arquivo)` e `io.BufferedReader` embrulham um arquivo e continuam sendo um arquivo.

> **Cuidado.** O decorador só responde ao que implementou. Se o consumidor chamar `.seek()`, `.name` ou `.close()`, vai falhar. Implemente o que o consumidor usa, ou repasse o resto com `__getattr__`, sabendo que repassar `seek` sem ajustar o contador quebra o limite.

<a id="funcoes-de-handler"></a>
## 3. Permissão e métrica em dezenas de handlers

**Situação.** A API de administração tem 30 handlers. Todos precisam checar o papel do usuário e registrar a duração da chamada. Cada handler é uma função simples que recebe o usuário e os argumentos da operação.

**sem o pattern — o mesmo cabeçalho e o mesmo try/finally em cada função**

```python
def cancelar_pedido(usuario, pedido_id):
    if "admin" not in usuario.papeis:
        raise Proibido("admin")
    inicio = time.perf_counter()
    try:
        pedido = pedidos.buscar(pedido_id)
        pedido.cancelar()
        return pedido
    finally:
        metricas.registrar("cancelar_pedido", time.perf_counter() - inicio)

# reembolsar_pedido, bloquear_cliente, exportar_relatorio...
# o mesmo bloco, com o nome da métrica copiado à mão em cada um
```

**O que dói.** A regra de negócio de cada handler é três linhas no meio de doze. O nome da métrica é copiado à mão e já há dois handlers registrando com o nome do outro. E esquecer o `if` de permissão em um handler novo não dá erro nenhum: dá um buraco de segurança.

**com o pattern — a função é embrulhada na definição**

```python
import functools

def exige_papel(papel):
    def decorador(funcao):
        @functools.wraps(funcao)
        def embrulhada(usuario, *args, **kwargs):
            if papel not in usuario.papeis:
                raise Proibido(papel)
            return funcao(usuario, *args, **kwargs)
        return embrulhada
    return decorador

def medido(funcao):
    @functools.wraps(funcao)
    def embrulhada(*args, **kwargs):
        inicio = time.perf_counter()
        try:
            return funcao(*args, **kwargs)
        finally:
            metricas.registrar(funcao.__name__, time.perf_counter() - inicio)
    return embrulhada

@exige_papel("admin")
@medido
def cancelar_pedido(usuario, pedido_id):
    pedido = pedidos.buscar(pedido_id)
    pedido.cancelar()
    return pedido
```

**O que o decorador acrescenta.** O que acontece **em volta** de uma função, sem que ela saiba. Aqui o "componente" é uma função, e a "interface" é a assinatura: `(*args, **kwargs)` faz o mesmo decorador servir a qualquer handler. Não existe classe nem camada para montar: a pilha está escrita em cima da função, e `functools.wraps` mantém o nome e a docstring, para que o log e as ferramentas de rota continuem mostrando `cancelar_pedido` e não `embrulhada`. O Python e o TypeScript trazem essa forma como sintaxe (`@`), mas é o mesmo pattern.

> **Dica.** A ordem de empilhar é a ordem de execução, de cima para baixo. Com `@exige_papel` por fora, uma chamada negada nunca chega à métrica. Invertendo, as tentativas proibidas passam a contar na latência dos handlers, e uma ou outra pode ser o que você quer. Decida de propósito.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na explicação):

| Caso | Já coberto por |
|---|---|
| Cache, retry, log, métrica ou trace sobre um cliente ou repositório | Explicação — o exemplo condutor, com a pilha de camadas |
| Pizza ou café com ingredientes extras | 1 — adicionais que mudam o resultado, em ordem |
| Comprimir ou criptografar um stream | 2 — um objeto que continua sendo um arquivo |
| Notificação que vai por e-mail e também por SMS e Slack | 1 — mas, se for "avisar vários", veja o Composite |
| Middleware de um framework web (autenticação, CORS, log) | 3 — comportamento em volta de um handler |
| Validação, cache e log em métodos de classe | 3 — o mesmo decorador, aplicado em método |

E dois casos que parecem Decorator, mas não são. Um objeto que cria o real só quando alguém o usa, ou que checa permissão antes de repassar, é um Proxy: controla o acesso, não acrescenta comportamento. E um embrulho que muda a assinatura (recebe um dicionário e chama o objeto com argumentos nomeados) é um Adapter. Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.

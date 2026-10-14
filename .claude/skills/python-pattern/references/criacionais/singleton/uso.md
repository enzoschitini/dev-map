<!-- Gerado de pages/clean-code/criacionais/singleton/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Singleton — Uso

*Clean Code / Design Pattern / Singleton*

Cinco situações em que o Singleton resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a instância única garante em cada caso.

<a id="como-escolhi"></a>
## Por que cinco

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para ter uma instância só. Quando dois casos se resolvem com o mesmo raciocínio — um pool de conexões e um cliente HTTP, por exemplo — só um fica. O Singleton tem poucos motivos legítimos, e a lista é curta de propósito. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a instância única garante |
|---|---|---|
| 1 | [Recurso caro criado a cada uso](#recurso-caro) | O custo é pago uma vez |
| 2 | [Estado que deveria ser um só](#estado-compartilhado) | Todo mundo vê os mesmos dados |
| 3 | [Recurso exclusivo disputado](#recurso-exclusivo) | Um dono, uma trava |
| 4 | [Objeto pesado criado sob concorrência](#criacao-concorrente) | Criação preguiçosa e segura |
| 5 | [Unicidade sem acesso global](#sem-global) | Um só, sem estado global |

> **Nota.** Os exemplos 1 e 4 usam `psycopg2` e `joblib` com as chamadas simplificadas: o formato é o real, mas parâmetros opcionais e configuração foram omitidos.

<a id="recurso-caro"></a>
## 1. Recurso caro criado a cada uso

**Situação.** O repositório de pedidos abre uma conexão com o PostgreSQL a cada consulta, usa e fecha. Em desenvolvimento, com uma pessoa clicando, funciona. Em produção, com centenas de requisições por segundo, o banco começa a recusar conexões.

**sem o pattern — uma conexão nova por consulta**

```python
class RepositorioDePedidos:
    def buscar(self, id):
        conn = psycopg2.connect(DSN)   # TCP + autenticação, toda vez
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pedidos WHERE id = %s", (id,))
            return cur.fetchone()
        finally:
            conn.close()
```

**O que dói.** Abrir a conexão custa mais que a consulta. Sob carga, o número de conexões simultâneas passa de `max_connections` e o banco responde com erro. E cada repositório novo repete o mesmo `connect`.

**com o pattern — um pool, criado uma vez**

```python
class Banco:
    _instancia = None
    _trava = threading.Lock()

    def __init__(self):
        self._pool = ThreadedConnectionPool(minconn=2, maxconn=10, dsn=DSN)

    @classmethod
    def instancia(cls):
        if cls._instancia is None:
            with cls._trava:
                if cls._instancia is None:
                    cls._instancia = cls()
        return cls._instancia

    @contextmanager
    def conexao(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

class RepositorioDePedidos:
    def buscar(self, id):
        with Banco.instancia().conexao() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM pedidos WHERE id = %s", (id,))
            return cur.fetchone()
```

**O que a instância única garante.** Que o custo de criar o recurso é pago uma vez, e que o limite de conexões vale para o processo inteiro. Dois pools de dez conexões não são "um pool com limite dez": é justamente isso que a unicidade protege.

> **Cuidado.** A garantia é **por processo**. Um servidor com 8 workers tem 8 pools de 10, ou seja, até 80 conexões. Some isso ao limite do banco antes de escolher o `maxconn`.

<a id="estado-compartilhado"></a>
## 2. Estado que deveria ser um só

**Situação.** A API limita cada cliente a 100 requisições por minuto. O limitador guarda a contagem em memória. Cada arquivo de rotas — pedidos, produtos — cria o seu, e a regra "100 por minuto" é uma regra do *cliente*, não de cada rota.

**sem o pattern — um limitador por arquivo, cada um com sua contagem**

```typescript
// pedidos.ts
const limitador = new Limitador(100);
app.get("/pedidos", (req, res) => {
  if (!limitador.permitir(req.ip)) return res.status(429).end();
  // ...
});

// produtos.ts
const limitador = new Limitador(100);   // outra contagem, do zero
app.get("/produtos", (req, res) => {
  if (!limitador.permitir(req.ip)) return res.status(429).end();
  // ...
});
```

**O que dói.** Um cliente faz 100 chamadas em `/pedidos` e mais 100 em `/produtos` no mesmo minuto, e nenhuma é recusada: o limite real é 100 *por rota*, e cresce a cada arquivo novo. O bug não dá erro, só deixa passar, e é por isso que demora a ser notado.

**com o pattern — uma contagem para todas as rotas**

```typescript
export class Limitador {
  private static _instancia: Limitador | undefined;
  private contagem = new Map<string, number>();

  private constructor(private readonly limitePorMinuto: number) {
    setInterval(() => this.contagem.clear(), 60_000).unref();
  }

  static get instancia(): Limitador {
    return (Limitador._instancia ??= new Limitador(100));
  }

  permitir(cliente: string): boolean {
    const n = (this.contagem.get(cliente) ?? 0) + 1;
    this.contagem.set(cliente, n);
    return n <= this.limitePorMinuto;
  }
}

// pedidos.ts e produtos.ts, iguais
app.get("/pedidos", (req, res) => {
  if (!Limitador.instancia.permitir(req.ip)) return res.status(429).end();
  // ...
});
```

**O que a instância única garante.** Que existe **uma verdade só**. Aqui o motivo não é custo, como no exemplo 1: é correção. Duas instâncias não são mais caras, são *erradas* — cada uma enxerga uma parte dos fatos. Esse é o teste mais confiável do padrão: se duas instâncias dariam respostas diferentes para a mesma pergunta, ele é a ferramenta certa.

<a id="recurso-exclusivo"></a>
## 3. Recurso exclusivo disputado

**Situação.** A emissão de notas fiscais exige numeração sequencial, sem buracos e sem repetição. O último número fica em um arquivo, e três serviços emitem notas ao mesmo tempo, em threads diferentes.

**sem o pattern — ler, somar e gravar, sem ninguém na frente**

```python
def proximo_numero():
    atual = int(Path("ultima_nota.txt").read_text())
    novo = atual + 1
    Path("ultima_nota.txt").write_text(str(novo))
    return novo
```

**O que dói.** Duas threads leem `41` antes de qualquer uma gravar; as duas devolvem `42`, e há duas notas com o mesmo número. É uma falha de numeração fiscal, que só aparece sob concorrência — ou seja, em produção, não nos testes.

**com o pattern — um dono do arquivo, uma trava**

```python
class NumeradorDeNotas:
    _instancia = None
    _trava_de_criacao = threading.Lock()

    def __init__(self, arquivo=Path("ultima_nota.txt")):
        self._arquivo = arquivo
        self._ultimo = int(arquivo.read_text())
        self._trava = threading.Lock()          # protege o número

    @classmethod
    def instancia(cls):
        # mesmo corpo do instancia() da Configuracao
        ...

    def proximo(self):
        with self._trava:
            self._ultimo += 1
            self._arquivo.write_text(str(self._ultimo))
            return self._ultimo

# em qualquer serviço
numero = NumeradorDeNotas.instancia().proximo()
```

**O que a instância única garante.** Que existe **um único dono** do recurso, e portanto uma única trava para ele. Uma trava só funciona se todos disputam *a mesma*: duas instâncias teriam duas travas, e nenhuma protegeria nada.

> **Nota.** Em um sistema real, a numeração pertence ao banco: uma `SEQUENCE` do PostgreSQL entrega números sem repetição para todos os processos, o que um Singleton em memória não consegue. O exemplo mostra o princípio — um dono, uma trava — e não a melhor forma de numerar notas.

<a id="criacao-concorrente"></a>
## 4. Objeto pesado criado sob concorrência

**Situação.** Um serviço de classificação de tickets usa um modelo de 400 MB, que leva dois segundos para carregar. Carregá-lo no `import` atrasa o início de qualquer comando, até os que nem classificam. Então alguém o carrega "só quando precisar".

**sem o pattern — carga preguiçosa, mas com uma corrida**

```python
_modelo = None

def classificar(texto):
    global _modelo
    if _modelo is None:
        _modelo = joblib.load("classificador.pkl")   # duas threads chegam aqui juntas
    return _modelo.predict([texto])[0]
```

**O que dói.** Com as primeiras requisições chegando juntas, várias threads veem `_modelo is None` ao mesmo tempo e cada uma carrega os 400 MB. O pico de memória é múltiplo do esperado, e o serviço pode ser derrubado logo após uma implantação. Em testes sequenciais, nada disso aparece.

**com o pattern — a criação é preguiçosa e protegida**

```python
class Classificador:
    _instancia = None
    _trava = threading.Lock()

    def __init__(self):
        self._modelo = joblib.load("classificador.pkl")

    @classmethod
    def instancia(cls):
        if cls._instancia is None:             # caminho rápido: sem trava
            with cls._trava:
                if cls._instancia is None:     # só uma thread chega aqui com None
                    cls._instancia = cls()
        return cls._instancia

    def classificar(self, texto):
        return self._modelo.predict([texto])[0]

def classificar(texto):
    return Classificador.instancia().classificar(texto)
```

**O que a instância única garante.** A **criação** acontece uma vez, na primeira vez que alguém precisa, e só uma thread a executa — as outras esperam na trava e depois reaproveitam. Ele resolve duas coisas juntas: não paga a carga se ninguém usar, e não paga duas vezes se muitos usarem ao mesmo tempo.

> **Dica.** O `functools.cache` sobre uma função `carregar_modelo()` resolve a parte preguiçosa com uma linha, mas ele não segura a chamada: duas threads simultâneas ainda podem executá-la ao mesmo tempo. Se a carga é cara e a concorrência é real, a trava continua sendo necessária.

<a id="sem-global"></a>
## 5. Unicidade sem acesso global

**Situação.** A `Configuracao` da Explicação funciona, mas o `Mailer` a busca com `Configuracao.instancia()` lá dentro do método. Alguém precisa testar o envio com outro host de SMTP.

**sem o pattern — o teste altera o global e contamina os seguintes**

```python
class Mailer:
    def enviar(self, destino, texto):
        host = Configuracao.instancia().dados["smtp_host"]   # dependência escondida
        ...

def test_envio_usa_o_host_configurado():
    Configuracao.instancia().dados["smtp_host"] = "localhost"
    Mailer().enviar("ana@exemplo.com", "oi")
    # o "localhost" continua lá para todos os testes que rodarem depois
```

**O que dói.** O construtor de `Mailer` não diz que depende de configuração: para descobrir, é preciso ler o corpo do método. O teste altera o estado compartilhado e o deixa lá, então o resultado de um teste passa a depender de quais rodaram antes dele — e o `reset()` que aparece para consertar é o sintoma descrito em "Sinais de que o Singleton saiu do lugar".

**com a unicidade, sem o global — criar uma vez e passar adiante**

```python
class Configuracao:
    def __init__(self, dados: dict):
        self.dados = dados

    @classmethod
    def carregar(cls, caminho: str):
        with open(caminho, encoding="utf-8") as f:
            return cls(json.load(f))

class Mailer:
    def __init__(self, config: Configuracao):
        self._config = config

    def enviar(self, destino, texto):
        host = self._config.dados["smtp_host"]
        ...

# a única criação, no ponto de entrada da aplicação
def main():
    config = Configuracao.carregar("config.json")
    mailer = Mailer(config)
    relatorio = Relatorio(config, mailer)
    ...

# o teste cria a sua, e mais nada é afetado
def test_envio_usa_o_host_configurado():
    mailer = Mailer(Configuracao({"smtp_host": "localhost"}))
    mailer.enviar("ana@exemplo.com", "oi")
```

**O que a instância única garante.** Aqui a unicidade não vem da classe, e sim do **lugar onde ela é criada**: a aplicação cria uma `Configuracao`, uma vez, e todo mundo recebe a mesma. É um "Singleton por convenção" — você mantém o "um só" e perde o "global". Na maior parte dos sistemas, é a forma de usar essa ideia que menos dá trabalho depois.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos cinco:

| Caso | Já coberto por |
|---|---|
| Cliente HTTP ou SDK de terceiros criado uma vez e reaproveitado | 1 — recurso caro |
| Pool de threads ou de workers | 1 — recurso caro, com um limite global |
| Cache em memória, registro de plugins ou de handlers | 2 — estado que deveria ser um só |
| Logger da aplicação | 2 e 3 — estado único e destino exclusivo; na prática `logging.getLogger` já cuida disso |
| Gerador de IDs sequenciais | 3 — um dono, uma trava |
| Carregar configuração do disco só na primeira vez | 4 — criação preguiçosa |
| Configuração da aplicação | 5 — criar uma vez e passar |

E um caso que parece Singleton, mas não é: uma classe só com métodos estáticos e nenhum estado, para agrupar funções. Não há instância controlada nem ciclo de vida — é um módulo com outro nome, e a seção [Parecidos](explicacao.md#parecidos) da explicação mostra a diferença.

<!-- Gerado de pages/clean-code/estruturais/facade/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Facade — Uso

*Clean Code / Design Pattern / Facade*

Três situações em que o Facade resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que a fachada esconde em cada caso.

<a id="como-escolhi"></a>
## Por que três

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Facade. O fluxo de vários passos repetido por vários chamadores (o checkout) já está inteiro na [explicação](explicacao.md#implementacao), e qualquer outro orquestrador de serviços é o mesmo raciocínio. Sobraram três motivos que ela não cobre. Os casos que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que a fachada esconde |
|---|---|---|
| 1 | [Uma ferramenta de linha de comando cheia de opções](#ffmpeg-e-ffprobe) | As flags e os erros de um programa externo |
| 2 | [Um módulo cujos internos vazaram pelo projeto](#fronteira-de-modulo) | Dezenas de classes internas, atrás de quatro funções |
| 3 | [Subir e derrubar vários componentes em ordem](#ambiente-de-teste) | A ordem de subida e a de descida |

> **Nota.** As chamadas ao `ffmpeg` e ao `ffprobe` usam flags reais, mas foram reduzidas ao necessário. Os módulos `pagamentos` e `infra_de_teste` são fictícios.

<a id="ffmpeg-e-ffprobe"></a>
## 1. Uma ferramenta de linha de comando cheia de opções

**Situação.** A plataforma de cursos gera uma miniatura e lê a duração de cada vídeo enviado. Isso é feito chamando o `ffmpeg` e o `ffprobe`, que têm centenas de opções. O time usa duas operações. Cada tela que precisa delas escreveu a própria chamada.

**sem o pattern — as flags copiadas, cada cópia um pouco diferente**

```python
# upload.py
subprocess.run(
    ["ffmpeg", "-i", caminho, "-ss", "5", "-frames:v", "1", destino],
)   # -ss depois do -i decodifica até o segundo 5; sem -y, falha se a miniatura existe

# reprocessar.py
r = subprocess.run(
    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
     "-of", "csv=p=0", caminho],
    capture_output=True, text=True,
)
duracao = float(r.stdout)   # vídeo corrompido: stdout vazio, ValueError longe da causa
```

**O que dói.** Sem `check=True`, o `ffmpeg` falha e o código segue em frente com uma miniatura que não existe. Quando falha com erro, o `stderr`, que diz o motivo, é jogado fora. Cada tela decidiu sozinha o tamanho da miniatura, e a posição do `-ss` muda a velocidade em dezenas de vezes. Quem precisa de uma terceira operação copia a mais próxima.

**com o pattern — duas operações com nome, e as flags em um lugar**

```python
class Video:
    def __init__(self, caminho: Path):
        self._caminho = caminho

    def duracao(self) -> float:
        saida = self._executar(
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(self._caminho),
        )
        return float(saida)

    def miniatura(self, segundo: float, destino: Path, largura: int = 320) -> Path:
        self._executar(
            "ffmpeg", "-y", "-ss", str(segundo), "-i", str(self._caminho),
            "-frames:v", "1", "-vf", f"scale={largura}:-1", str(destino),
        )
        return destino

    def _executar(self, *comando: str) -> str:
        try:
            return subprocess.run(comando, check=True, capture_output=True, text=True).stdout
        except FileNotFoundError as e:
            raise FerramentaAusente(comando[0]) from e
        except subprocess.CalledProcessError as e:
            ultima = (e.stderr.strip().splitlines() or ["sem detalhes"])[-1]
            raise VideoInvalido(self._caminho, ultima) from e

# o chamador
video = Video(caminho)
video.miniatura(5, destino)
duracao = video.duracao()
```

**O que a fachada esconde.** O vocabulário de uma ferramenta de 30 anos: os nomes das flags, a ordem delas e o que cada código de saída quer dizer. O chamador ganha duas operações com nome e dois erros do *domínio* (`FerramentaAusente`, `VideoInvalido`) no lugar de um `CalledProcessError` genérico. O que este exemplo ensina e o do checkout não: a fachada aqui **reduz superfície**. Ela não organiza passos; escolhe, entre centenas de opções, as duas que o time usa.

> **Cuidado.** Resista a expor todas as flags "por via das dúvidas". Quando alguém precisar de um novo recorte ou de um formato diferente, acrescente o parâmetro que ele precisa. Uma fachada que aceita `**opcoes` e as passa adiante voltou a ser a própria ferramenta, com um nome a mais.

<a id="fronteira-de-modulo"></a>
## 2. Um módulo cujos internos vazaram pelo projeto

**Situação.** O módulo de pagamentos tem um gateway, regras antifraude, conciliação e modelos próprios, em dezenas de arquivos. Outros times importam o que precisam, de onde estiver. A empresa decidiu trocar de gateway, e o time de pagamentos descobre que não consegue mexer por dentro sem quebrar o resto.

**sem o pattern — os outros módulos importam os internos**

```python
# pedidos/servico.py
from pagamentos.gateway.stripe_adapter import GatewayStripe
from pagamentos.antifraude.regras import pontuar, LIMITE

def pagar(pedido):
    if pontuar(pedido.id, pedido.total) > LIMITE:
        raise PedidoSuspeito(pedido.id)
    return GatewayStripe(CHAVE).cobrar(pedido.total, pedido.token)

# faturas/estorno.py
from pagamentos.gateway.stripe_adapter import GatewayStripe   # sem antifraude: ninguém lembrou

# relatorios/conciliacao.py: mais um import de pagamentos.gateway.*
```

**O que dói.** Trocar de gateway é editar imports em seis módulos de times diferentes, e o time de pagamentos precisa de um acordo com cada um. A regra de antifraude, que devia valer sempre, está só em quem lembrou de chamá-la. Quanto mais gente importa os internos, mais cara fica qualquer mudança neles.

**com o pattern — o módulo tem uma porta, e o resto fica atrás dela**

```python
# pagamentos/__init__.py — a única coisa que os outros módulos importam
from decimal import Decimal
from ._modelos import Resultado
from ._servico import ServicoDePagamento

_servico = ServicoDePagamento.padrao()

def cobrar(pedido_id: str, valor: Decimal, token: str) -> Resultado:
    return _servico.cobrar(pedido_id, valor, token)   # antifraude + gateway, juntos

def estornar(cobranca_id: str) -> None:
    _servico.estornar(cobranca_id)

__all__ = ["cobrar", "estornar", "Resultado"]

# pedidos/servico.py
import pagamentos

def pagar(pedido):
    resultado = pagamentos.cobrar(pedido.id, pedido.total, pedido.token)
    if resultado.suspeito:
        raise PedidoSuspeito(pedido.id)
    return resultado
```

**O que a fachada esconde.** Os internos do módulo inteiro, atrás de duas funções e um tipo. Aqui ela é uma **fronteira**, não uma conveniência: a regra passa a ser "só se importa o que está em `pagamentos/__init__.py`", e pode ser verificada por uma ferramenta de imports (o `import-linter` faz isso em Python), em vez de depender de revisão. Trocar de gateway é uma mudança em `_servico.py`, e nenhum outro time é consultado. A antifraude passa a rodar sempre, porque está no único caminho.

> **Cuidado.** A fachada de módulo não pode devolver objetos internos. Se `cobrar()` devolver um `stripe.Charge`, quem usa passa a depender do gateway pelo tipo do retorno, e a fronteira é só aparente. Por isso `Resultado` é um tipo do próprio módulo, pequeno e estável.

<a id="ambiente-de-teste"></a>
## 3. Subir e derrubar vários componentes em ordem

**Situação.** Os testes de integração precisam de um Postgres, de um Redis, de um servidor SMTP falso e da aplicação, nessa ordem, porque a aplicação precisa dos três. Cada arquivo de teste sobe tudo na mão, e a CI roda alguns em paralelo.

**sem o pattern — subir em ordem, derrubar de memória**

```python
def test_confirmacao_envia_email():
    db = subir_postgres()
    aplicar_migracoes(db.url)
    redis = subir_redis()
    smtp = subir_smtp_falso(porta=2525)    # fixa: dois testes em paralelo colidem
    app = criar_app(db.url, redis.url, smtp.porta)
    try:
        app.post("/checkout", json=CARRINHO)
        assert smtp.mensagens[-1].assunto == "Pedido confirmado"
    finally:
        app.parar()
        smtp.parar()
        db.parar()          # e o redis?
```

**O que dói.** O `finally` esqueceu o Redis, que fica rodando depois de cada teste. Se `subir_smtp_falso` falhar, o Postgres que já subiu nunca é derrubado, porque a exceção acontece antes do `try`. E os vinte testes de integração têm o mesmo bloco de nove linhas, que muda quando entra um componente novo.

**com o pattern — um ambiente que sobe e desce sozinho**

```python
from contextlib import ExitStack, contextmanager

@dataclass(frozen=True)
class Ambiente:
    app: object
    db: object
    redis: object
    smtp: object

@contextmanager
def ambiente_de_teste():
    with ExitStack() as pilha:
        db = pilha.enter_context(postgres_temporario())
        aplicar_migracoes(db.url)
        redis = pilha.enter_context(redis_temporario())
        smtp = pilha.enter_context(smtp_falso())          # porta livre, escolhida na hora
        app = pilha.enter_context(app_em_teste(db.url, redis.url, smtp.porta))
        yield Ambiente(app=app, db=db, redis=redis, smtp=smtp)

def test_confirmacao_envia_email():
    with ambiente_de_teste() as env:
        env.app.post("/checkout", json=CARRINHO)
        assert env.smtp.mensagens[-1].assunto == "Pedido confirmado"
```

**O que a fachada esconde.** A ordem de subida e, principalmente, a ordem **inversa** de descida, que o `ExitStack` faz sozinho. Ao contrário dos outros exemplos, aqui a fachada coordena um *ciclo de vida*, e não uma chamada: o que importa é o que acontece com os componentes que já subiram quando um deles falha no meio. Se o app não sobe, o Redis, o SMTP e o Postgres são derrubados, nessa ordem. O teste só vê um `Ambiente` com o que ele quer tocar.

> **Dica.** No `pytest`, a mesma função vira uma *fixture* com `yield` e escopo de sessão ou de módulo, para pagar o custo de subir o Postgres uma vez e não a cada teste. A fachada continua a mesma; só muda quem a chama.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos três (ou na explicação):

| Caso | Já coberto por |
|---|---|
| Fluxo de pedido, de matrícula ou de cadastro que chama vários serviços | Explicação — o exemplo do checkout |
| Cliente simplificado para o S3 ou para uma fila, com três operações | 1 — reduzir a superfície de uma SDK grande |
| Cliente de uma API REST complexa, com autenticação e paginação | 1 — reduzir a superfície |
| O `api.py` ou a camada de serviço de cada módulo de um monólito | 2 — fachada como fronteira de módulo |
| Script de *seed*, de *deploy* ou de inicialização local | 3 — ordem de subida e de descida |
| Um `docker compose up` que o time criou para o desenvolvimento | 3 — é a mesma fachada, em outra ferramenta |

E dois casos que parecem Facade, mas não são. Uma classe que tem um método para cada método da SDK, só com outros nomes, não simplifica nada: é um repasse. E uma classe que converte a interface de *uma* peça na que o código já esperava é um Adapter. Veja a seção [Parecidos](explicacao.md#parecidos) da explicação.

<!-- Gerado de pages/clean-code/estruturais/adapter/uso.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Adapter — Uso

*Clean Code / Design Pattern / Adapter*

Sete situações em que o Adapter resolve o problema. Cada uma traz o código sem o pattern, o código com ele e o que o adaptador está absorvendo.

<a id="como-escolhi"></a>
## Por que sete

Cada exemplo entrou com uma regra: precisa trazer um **motivo diferente** para usar o Adapter. Quando dois casos se resolvem com o mesmo raciocínio — trocar a SDK de SMS e trocar a SDK de e-mail, por exemplo — só um fica. Seguindo essa regra, sobraram sete motivos. Os que ficaram de fora estão no [fim da página](#fora-da-lista).

| # | Situação | O que o adaptador traduz |
|---|---|---|
| 1 | [Vários provedores para a mesma operação](#varios-provedores) | Assinatura, unidades e retorno de cada SDK |
| 2 | [Código legado que ninguém pode mexer](#codigo-legado) | Uma assinatura antiga em uma nova |
| 3 | [Payload de API vazando para o domínio](#payload-externo) | O vocabulário de fora no vocabulário de dentro |
| 4 | [Infraestrutura que trava dev e teste](#dependencia-de-infra) | Operações *e* erros |
| 5 | [API de callback em código async](#callback-promise) | O modelo de execução |
| 6 | [API paginada consumida como lista](#paginacao) | Um protocolo da linguagem |
| 7 | [O framework espera uma interface dele](#framework) | O seu código para a interface de fora |

> **Nota.** As chamadas de SDK estão simplificadas para caber na página. O formato é o real; parâmetros opcionais e configuração foram omitidos.

<a id="varios-provedores"></a>
## 1. Vários provedores para a mesma operação

**Situação.** A loja cobra cartão pelo Stripe. O comercial fechou contrato com o Mercado Pago, e parte das vendas passa a ir para lá. As duas SDKs fazem a mesma coisa — cobrar — de jeitos diferentes: o Stripe recebe o valor em *centavos* e responde `"succeeded"`; o Mercado Pago recebe em *reais* e responde `"approved"`.

**sem o pattern — o checkout conhece as duas SDKs**

```python
class Checkout:
    def pagar(self, pedido, gateway):
        if gateway == "stripe":
            r = stripe.PaymentIntent.create(
                amount=int(pedido.total * 100),  # centavos
                currency="brl",
                payment_method=pedido.token,
                confirm=True,
            )
            aprovado = r.status == "succeeded"
            transacao = r.id
        elif gateway == "mercadopago":
            r = mp.payment().create({
                "transaction_amount": float(pedido.total),  # reais
                "token": pedido.token,
                "payer": {"email": pedido.email},
            })["response"]
            aprovado = r["status"] == "approved"
            transacao = str(r["id"])

        if not aprovado:
            raise PagamentoRecusado(pedido.id)
        pedido.marcar_pago(transacao)
```

**O que dói.** Um terceiro gateway é mais um `elif` dentro da regra de negócio. Um erro de unidade (cobrar 100 vezes o valor) mora no mesmo método que decide se o pedido foi pago. E testar o checkout exige as duas SDKs.

**com o pattern — um adaptador por provedor**

```python
# o alvo: o que o checkout precisa, nos termos dele
@dataclass(frozen=True)
class Cobranca:
    aprovada: bool
    transacao: str

class Gateway(ABC):
    @abstractmethod
    def cobrar(self, valor: Decimal, token: str, email: str) -> Cobranca: ...

# os adaptadores: cada um conhece só a sua SDK
class GatewayStripe(Gateway):
    def cobrar(self, valor, token, email):
        r = stripe.PaymentIntent.create(
            amount=int(valor * 100), currency="brl",
            payment_method=token, confirm=True, receipt_email=email,
        )
        return Cobranca(aprovada=r.status == "succeeded", transacao=r.id)

class GatewayMercadoPago(Gateway):
    def __init__(self, sdk):
        self._sdk = sdk

    def cobrar(self, valor, token, email):
        r = self._sdk.payment().create({
            "transaction_amount": float(valor),
            "token": token,
            "payer": {"email": email},
        })["response"]
        return Cobranca(aprovada=r["status"] == "approved", transacao=str(r["id"]))

# o cliente: uma linha de pagamento, nenhum provedor
class Checkout:
    def __init__(self, gateway: Gateway):
        self._gateway = gateway

    def pagar(self, pedido):
        cobranca = self._gateway.cobrar(pedido.total, pedido.token, pedido.email)
        if not cobranca.aprovada:
            raise PagamentoRecusado(pedido.id)
        pedido.marcar_pago(cobranca.transacao)
```

**O que o adaptador absorve.** Centavos contra reais, `"succeeded"` contra `"approved"`, objeto contra dicionário, id numérico contra texto. Nada disso chega ao `Checkout`. O retorno também é seu: `Cobranca` tem os dois campos que a regra usa, e não o objeto inteiro da SDK. Um terceiro provedor vira uma classe nova, e o checkout não é tocado.

> **Cuidado.** Resista a pôr em `Cobranca` todo campo que alguma SDK devolve "porque pode ser útil". O alvo cresce até virar a soma das duas APIs, e aí o checkout volta a depender delas.

<a id="codigo-legado"></a>
## 2. Código legado que ninguém pode mexer

**Situação.** O cálculo de frete é um módulo de 2014, usado por outros três sistemas da empresa. Ninguém tem coragem — nem permissão — de mudar a assinatura. Ele recebe CEPs só com dígitos, peso em *gramas*, o serviço como número mágico (`1` = PAC, `2` = SEDEX) e devolve uma string: `"R$ 1.023,90|5"`, valor e prazo separados por barra.

**sem o pattern — cada chamador faz o próprio parse**

```python
def resumo_do_carrinho(carrinho, cep_destino):
    bruto = legado.calc_frete(
        "01310100",
        cep_destino.replace("-", ""),
        int(carrinho.peso_kg * 1000),
        2,  # SEDEX... ou era PAC?
    )
    valor, prazo = bruto.split("|")
    valor = Decimal(valor.replace("R$ ", "").replace(".", "").replace(",", "."))
    return carrinho.subtotal + valor, int(prazo)

# e o mesmo parse aparece de novo na página do produto, na API
# de cotação e no job de reprecificação — cada um um pouco diferente.
# um deles esqueceu o .replace(".", "") e quebra em fretes acima de R$ 999.
```

**O que dói.** O formato esquisito do legado se espalhou. Cada cópia do parse é um lugar onde um bug pode estar, e é justamente o tipo de bug que só aparece com um valor específico.

**com o pattern — o legado fica intacto, atrás de uma interface nova**

```python
class Servico(Enum):
    PAC = 1
    SEDEX = 2

@dataclass(frozen=True)
class Cotacao:
    valor: Decimal
    prazo_dias: int

class CotadorDeFrete(Protocol):
    def cotar(self, origem: str, destino: str, peso_kg: float, servico: Servico) -> Cotacao: ...

class CotadorLegado:
    """Único lugar do sistema que conhece o formato 'R$ 1.023,90|5'."""

    def cotar(self, origem, destino, peso_kg, servico):
        bruto = legado.calc_frete(
            _so_digitos(origem),
            _so_digitos(destino),
            round(peso_kg * 1000),
            servico.value,
        )
        valor, prazo = bruto.split("|")
        return Cotacao(_moeda_para_decimal(valor), int(prazo))

# o chamador fala a língua nova
def resumo_do_carrinho(carrinho, cep_destino, cotador: CotadorDeFrete):
    c = cotador.cotar(LOJA.cep, cep_destino, carrinho.peso_kg, Servico.SEDEX)
    return carrinho.subtotal + c.valor, c.prazo_dias
```

**O que o adaptador absorve.** Gramas, número mágico, CEP sem hífen e a string com barra. O módulo de 2014 não muda uma linha, os outros três sistemas continuam funcionando, e o parse existe uma vez só — com um teste só.

O ganho maior é o do dia seguinte: quando o frete for reescrito, nasce um `CotadorNovo` que implementa o mesmo `CotadorDeFrete`. Dá para migrar tela por tela, ou rodar os dois lado a lado e comparar os resultados antes de desligar o antigo.

> **Dica.** O `Protocol` do Python dispensa herança: qualquer classe com um método `cotar` com essa assinatura serve. É útil quando o adaptador mora em outro pacote e você não quer que ele importe a interface.

<a id="payload-externo"></a>
## 3. Payload de API vazando para o domínio

**Situação.** O formulário de endereço preenche a rua a partir do CEP, usando o ViaCEP. O JSON dele usa os nomes dele — `logradouro`, `localidade`, `uf` — e, quando o CEP não existe, responde `200` com `{ erro: true }` em vez de um 404.

**sem o pattern — o JSON do ViaCEP em três arquivos**

```typescript
// checkout.tsx
const dados = await (await fetch(`https://viacep.com.br/ws/${cep}/json/`)).json();
if (dados.erro) return mostrarErro("CEP não encontrado");
setForm({ ...form, rua: dados.logradouro, cidade: dados.localidade, uf: dados.uf });

// frete.ts
const dados = await (await fetch(`https://viacep.com.br/ws/${cep}/json/`)).json();
const regiao = regiaoDoEstado(dados.uf);

// cadastro.tsx — este esqueceu do erro; com CEP inválido grava rua undefined
const { logradouro, bairro } = await (await fetch(`https://viacep.com.br/ws/${cep}/json/`)).json();
```

**O que dói.** O vocabulário do ViaCEP virou o vocabulário do sistema. O jeito de detectar "não encontrado" está repetido — e esquecido em um lugar. Se o ViaCEP sair do ar e a decisão for usar a BrasilAPI, que chama os mesmos campos de `street`, `city` e `state`, a troca é uma caça ao tesouro.

**com o pattern — o domínio escolhe os próprios nomes**

```typescript
// o alvo: o endereço como o seu sistema o entende
export interface Endereco {
  cep: string; rua: string; bairro: string; cidade: string; uf: string;
}

export interface BuscaCep {
  /** null quando o CEP não existe — um único significado para "não achei" */
  buscar(cep: string): Promise<Endereco | null>;
}

export class ViaCep implements BuscaCep {
  async buscar(cep: string) {
    const d = await (await fetch(`https://viacep.com.br/ws/${cep}/json/`)).json();
    if (d.erro) return null;
    return { cep: d.cep, rua: d.logradouro, bairro: d.bairro, cidade: d.localidade, uf: d.uf };
  }
}

export class BrasilApiCep implements BuscaCep {
  async buscar(cep: string) {
    const r = await fetch(`https://brasilapi.com.br/api/cep/v1/${cep}`);
    if (r.status === 404) return null;
    const d = await r.json();
    return { cep: d.cep, rua: d.street, bairro: d.neighborhood, cidade: d.city, uf: d.state };
  }
}

// checkout.tsx — não sabe de onde o endereço veio
const endereco = await buscaCep.buscar(cep);
if (!endereco) return mostrarErro("CEP não encontrado");
setForm({ ...form, ...endereco });
```

**O que o adaptador absorve.** Nomes de campo e o jeito de cada API dizer "não existe" — um pelo corpo, o outro pelo status. A palavra `logradouro` agora aparece em um arquivo só. Essa é a ideia por trás da *camada anticorrupção* do Domain-Driven Design: um Adapter na fronteira, para que o modelo de fora não contamine o de dentro.

<a id="dependencia-de-infra"></a>
## 4. Infraestrutura que trava dev e teste

**Situação.** Relatórios mensais em PDF são guardados no S3 como cache: se já existe, devolve; se não, gera e grava. Para rodar o projeto na máquina, cada pessoa precisa de credenciais da AWS. Nos testes, alguém sobe um S3 falso. E a regra de negócio captura a exceção do `boto3` pelo código de erro.

**sem o pattern — a regra sabe o que é um ClientError**

```python
import boto3
from botocore.exceptions import ClientError

class Relatorios:
    def __init__(self):
        self._s3 = boto3.client("s3")

    def mensal(self, mes):
        chave = f"relatorios/{mes}.pdf"
        try:
            return self._s3.get_object(Bucket="empresa-docs", Key=chave)["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchKey":
                raise
        pdf = montar_pdf(mes)
        self._s3.put_object(Bucket="empresa-docs", Key=chave, Body=pdf)
        return pdf
```

**O que dói.** O cliente do S3 é criado dentro da classe, então não há como trocar. E `"NoSuchKey"` é um detalhe da AWS dentro de uma regra que só quer saber "o arquivo existe?".

**com o pattern — um adaptador para a nuvem, outro para o disco**

```python
class ArquivoNaoEncontrado(Exception): ...

class Armazenamento(Protocol):
    def ler(self, caminho: str) -> bytes: ...
    def gravar(self, caminho: str, dados: bytes) -> None: ...

class ArmazenamentoS3:
    def __init__(self, cliente, bucket):
        self._s3, self._bucket = cliente, bucket

    def ler(self, caminho):
        try:
            return self._s3.get_object(Bucket=self._bucket, Key=caminho)["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise ArquivoNaoEncontrado(caminho) from e
            raise

    def gravar(self, caminho, dados):
        self._s3.put_object(Bucket=self._bucket, Key=caminho, Body=dados)

class ArmazenamentoLocal:
    def __init__(self, raiz: Path):
        self._raiz = raiz

    def ler(self, caminho):
        try:
            return (self._raiz / caminho).read_bytes()
        except FileNotFoundError as e:
            raise ArquivoNaoEncontrado(caminho) from e

    def gravar(self, caminho, dados):
        destino = self._raiz / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(dados)

class Relatorios:
    def __init__(self, armazenamento: Armazenamento):
        self._arquivos = armazenamento

    def mensal(self, mes):
        caminho = f"relatorios/{mes}.pdf"
        try:
            return self._arquivos.ler(caminho)
        except ArquivoNaoEncontrado:
            pdf = montar_pdf(mes)
            self._arquivos.gravar(caminho, pdf)
            return pdf
```

**O que o adaptador absorve.** As chamadas, sim — mas principalmente os **erros**. Exceção faz parte da interface: se `ClientError` e `FileNotFoundError` passassem direto, a regra teria que conhecer as duas. Os dois adaptadores traduzem para `ArquivoNaoEncontrado`, que é do seu domínio.

Em produção, `ArmazenamentoS3(boto3.client("s3"), "empresa-docs")`. Na máquina, `ArmazenamentoLocal(Path("./.dados"))`. No teste, o mesmo local apontando para o `tmp_path` do pytest. A escolha acontece em um lugar só, na montagem da aplicação, e não dentro de `Relatorios`.

<a id="callback-promise"></a>
## 5. API de callback em código async

**Situação.** A tela de lojas próximas precisa da posição do usuário. O resto do front é `async/await`, mas `navigator.geolocation.getCurrentPosition` é dos tempos dos callbacks: recebe uma função de sucesso e outra de erro.

**sem o pattern — duas trilhas de erro e um finally que não existe**

```typescript
function mostrarLojasProximas() {
  carregando(true);
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      fetch(`/api/lojas?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}`)
        .then((r) => r.json())
        .then((lojas) => { render(lojas); carregando(false); })
        .catch((e) => { mostrarErro(e); carregando(false); });
    },
    (e) => { mostrarErro(e); carregando(false); },
    { timeout: 5000 },
  );
}
```

**O que dói.** `carregando(false)` aparece três vezes, porque não dá para usar `try/finally` através de um callback. O erro de permissão e o erro de rede seguem caminhos diferentes. E testar a tela exige simular o objeto `navigator`.

**com o pattern — a mesma API, agora com cara de Promise**

```typescript
export interface Coordenadas { lat: number; lng: number }

export interface Localizador {
  posicaoAtual(): Promise<Coordenadas>;
}

export class LocalizadorDoNavegador implements Localizador {
  posicaoAtual() {
    return new Promise<Coordenadas>((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        (erro) => reject(new SemLocalizacao(erro.message)),
        { timeout: 5000 },
      );
    });
  }
}

async function mostrarLojasProximas(localizador: Localizador) {
  carregando(true);
  try {
    const { lat, lng } = await localizador.posicaoAtual();
    const lojas = await (await fetch(`/api/lojas?lat=${lat}&lng=${lng}`)).json();
    render(lojas);
  } catch (e) {
    mostrarErro(e);
  } finally {
    carregando(false);
  }
}
```

**O que o adaptador absorve.** Aqui não são nomes nem formatos: é o **modelo de execução**. Callback vira Promise, dois caminhos de erro viram um `reject`, e o formato `GeolocationPosition` vira um `{ lat, lng }` simples. No teste, um `Localizador` falso é um objeto com um método que retorna `Promise.resolve({ lat: -23.5, lng: -46.6 })`.

> **Dica.** O Node já traz um adaptador genérico desse tipo: `util.promisify` transforma qualquer função no estilo `(err, valor) => …` em uma que retorna Promise. Quando o callback não segue esse formato — como o da geolocalização —, você escreve o seu.

<a id="paginacao"></a>
## 6. API paginada consumida como lista

**Situação.** Os clientes moram em um CRM externo, cuja API devolve 100 por vez: `{"data": [...], "next_cursor": "..."}`. Toda função que precisa "de todos os clientes" reescreve o mesmo laço de paginação.

**sem o pattern — o laço de cursor copiado em cada função**

```python
def exportar_csv(crm, arquivo):
    cursor = None
    while True:
        resp = crm.get("/contacts", params={"limit": 100, "cursor": cursor})
        for c in resp["data"]:
            arquivo.write(f'{c["id"]},{c["email"]}\n')
        cursor = resp.get("next_cursor")
        if not cursor:
            break

def contar_inativos(crm):
    total, cursor = 0, None
    while True:
        resp = crm.get("/contacts", params={"limit": 100, "cursor": cursor})
        total += sum(1 for c in resp["data"] if not c["active"])
        cursor = resp.get("next_cursor")
        if not cursor:
            break
    return total
```

**O que dói.** Metade de cada função é mecânica de paginação, e a regra de verdade — uma linha — fica soterrada. As funções só aceitam o cliente do CRM, então testar exige simular páginas e cursores.

**com o pattern — a API paginada se comporta como um iterável**

```python
class ContatosDoCrm:
    """Adapta a paginação por cursor ao protocolo de iteração do Python."""

    def __init__(self, crm, por_pagina=100):
        self._crm, self._por_pagina = crm, por_pagina

    def __iter__(self) -> Iterator[Contato]:
        cursor = None
        while True:
            resp = self._crm.get("/contacts", params={"limit": self._por_pagina, "cursor": cursor})
            for c in resp["data"]:
                yield Contato(id=c["id"], email=c["email"], ativo=c["active"])
            cursor = resp.get("next_cursor")
            if not cursor:
                return

# os consumidores aceitam qualquer iterável de Contato
def exportar_csv(contatos: Iterable[Contato], arquivo):
    for c in contatos:
        arquivo.write(f"{c.id},{c.email}\n")

def contar_inativos(contatos: Iterable[Contato]):
    return sum(1 for c in contatos if not c.ativo)

# uso
contar_inativos(ContatosDoCrm(crm))
```

**O que o adaptador absorve.** O alvo aqui não é uma interface que você escreveu: é o **protocolo de iteração da própria linguagem**. Por isso o ganho vai além do esperado: o `for`, o `sum`, o `itertools` — tudo passa a funcionar com o CRM. E como o gerador é preguiçoso, `islice(ContatosDoCrm(crm), 10)` busca só a primeira página e para.

O teste de `contar_inativos` recebe uma lista comum: `[Contato(1, "a@x", False), Contato(2, "b@x", True)]`. Nenhuma página falsa.

> **Dica.** A biblioteca padrão tem outros adaptadores para protocolos da linguagem. `contextlib.closing`, por exemplo, faz qualquer objeto com `.close()` funcionar em um `with`.

<a id="framework"></a>
## 7. O framework espera uma interface dele

**Situação.** O time já tem um `AlertaSlack`, com um método `alertar(canal, texto)`. A decisão é que todo erro de produção chegue no canal `#ops`. Até aqui, os outros exemplos adaptavam o código de fora para a sua interface. Este vai na **direção contrária**: o `logging` do Python tem a interface dele, e o seu código é que precisa caber nela.

**sem o pattern — alerta manual ao lado de cada log**

```python
try:
    processar_lote(lote)
except Exception:
    logger.exception("falha no lote %s", lote.id)
    alerta.alertar("#ops", f"falha no lote {lote.id}")  # e nos outros 40 except?

# e os erros que as bibliotecas registram sozinhas
# (banco, cliente HTTP, fila) nunca chegam ao Slack
```

**O que dói.** O alerta depende de alguém lembrar de escrevê-lo, a mensagem é escrita duas vezes, e tudo o que é registrado fora do seu código fica invisível.

**com o pattern — o AlertaSlack vestido de logging.Handler**

```python
class HandlerSlack(logging.Handler):
    """Adapta o AlertaSlack à interface que o logging espera."""

    def __init__(self, alerta: AlertaSlack, canal: str):
        super().__init__(level=logging.ERROR)
        self._alerta, self._canal = alerta, canal

    def emit(self, record):
        try:
            self._alerta.alertar(self._canal, self.format(record))
        except Exception:
            self.handleError(record)  # o log nunca derruba a aplicação

# uma vez, na inicialização
logging.getLogger().addHandler(HandlerSlack(alerta, "#ops"))

# no código, só log
try:
    processar_lote(lote)
except Exception:
    logger.exception("falha no lote %s", lote.id)
```

**O que o adaptador absorve.** Os papéis se invertem: o **alvo** é `logging.Handler`, que não é seu; o **adaptado** é o `AlertaSlack`, que é. O cliente passa a ser o framework inteiro — e por isso os erros das bibliotecas também chegam ao Slack, sem nenhuma linha a mais.

O mesmo formato aparece sempre que um framework oferece um ponto de extensão: um backend de storage do Django, um transporte customizado do `httpx`, um `Comparator` em Java. Você implementa a interface deles, e por dentro chama o que já tem.

> **Cuidado.** Adaptador para um framework precisa respeitar o contrato inteiro dele, não só a assinatura. O `logging` exige que `emit` não propague exceções — se o Slack cair, a aplicação não pode cair junto. Por isso o `handleError`.

<a id="fora-da-lista"></a>
## O que ficou de fora

Casos comuns que não ganharam seção própria, porque o motivo já está em um dos sete:

| Caso | Já coberto por |
|---|---|
| Trocar a SDK de e-mail, de SMS ou de push | 1 — vários provedores, mesma operação |
| Migrar da v1 para a v2 de uma API sem parar o sistema | 2 — os dois lados atrás da mesma interface durante a troca |
| Envolver um componente de UI de terceiros (datepicker, gráfico) no seu design system | 3 — os nomes e formatos de fora traduzidos na fronteira |
| Converter unidades ou fusos de um sensor ou serviço externo | 3 — é tradução de dados |
| Fazer um objeto com `.close()` funcionar em um `with` | 6 — adaptar a um protocolo da linguagem |

E um caso que parece Adapter, mas não é: esconder uma SDK enorme atrás de dois métodos simples. Se o objetivo é *reduzir* a superfície de um subsistema, e não converter uma interface em outra que já existia, o nome certo é Facade — veja a seção [Parecidos](explicacao.md#parecidos) da explicação.

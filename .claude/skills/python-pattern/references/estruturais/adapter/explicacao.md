<!-- Gerado de pages/clean-code/estruturais/adapter/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Adapter — Explicação

*Clean Code / Design Pattern / Adapter*

Como encaixar uma interface que você não controla na interface que o seu código espera, sem espalhar a diferença pelo sistema inteiro.

<a id="o-problema"></a>
## O problema

O seu código já sabe o que quer: `enviar(destino, texto)`. Aí entra um serviço de fora — uma SDK, uma API, uma biblioteca legada — que faz exatamente isso, mas com outro nome, outra ordem de argumentos e outro formato de retorno.

A saída preguiçosa é chamar o serviço direto, de dentro das regras de negócio:

**antes — a diferença vaza para dentro**

```python
class AvisoDePedido:
    def confirmar(self, pedido):
        # a regra de negócio agora sabe o nome da SDK,
        # o formato do telefone e o código de retorno dela
        resp = twilio.messages.create(
            to="+55" + pedido.telefone,
            body=f"Pedido {pedido.id} confirmado",
        )
        if resp.status_code != 201:
            raise RuntimeError(resp.error_message)
```

Três coisas quebram daqui a pouco: trocar de provedor vira busca e substituição no projeto inteiro; testar exige a SDK de verdade; e a regra de negócio passa a ter um motivo a mais para mudar — exatamente o que o Single Responsibility pede para evitar.

<a id="a-solucao"></a>
## A solução

Uma peça no meio, que fala as duas línguas. São sempre quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Alvo | A interface que o seu código espera | `Notificador` |
| Cliente | Quem usa o alvo, sem saber de mais nada | `AvisoDePedido` |
| Adaptado | O que já existe, com a interface errada | A SDK do provedor |
| Adaptador | Implementa o alvo e chama o adaptado | `NotificadorTwilio` |

O ponto é a direção da dependência: quem define a interface é o **seu** lado, não o de fora. O adaptador é a única parte do sistema que conhece a SDK.

<a id="implementacao"></a>
## Implementação

```python
from abc import ABC, abstractmethod

# 1. o alvo: a interface que o seu código escolheu
class Notificador(ABC):
    @abstractmethod
    def enviar(self, destino: str, texto: str) -> None: ...

# 2. o adaptador: traduz, e só
class NotificadorTwilio(Notificador):
    def __init__(self, sdk):
        self._sdk = sdk

    def enviar(self, destino, texto):
        resp = self._sdk.messages.create(to="+55" + destino, body=texto)
        if resp.status_code != 201:
            raise EnvioFalhou(resp.error_message)

# 3. o cliente: não conhece provedor nenhum
class AvisoDePedido:
    def __init__(self, notificador: Notificador):
        self._notificador = notificador

    def confirmar(self, pedido):
        self._notificador.enviar(pedido.telefone, f"Pedido {pedido.id} confirmado")
```

> **Dica.** O teste do cliente agora é uma classe de cinco linhas que implementa `Notificador` e guarda o que recebeu. Nenhuma rede, nenhum mock de biblioteca.

<a id="quando-usar"></a>
## Quando usar

O Adapter vale quando três coisas acontecem ao mesmo tempo: **já existe** algo que faz o que você precisa, a interface dele **não é** a que o seu código quer, e mudar esse algo **não é opção** — porque é de terceiros, é legado ou é de outro time.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Dependência externa no meio da regra de negócio | `import` de SDK em arquivo de domínio; o nome do fornecedor aparece dentro da regra | [Uso #1](uso.md#varios-provedores) |
| Dois fornecedores para a mesma operação, ou um segundo à vista | `if gateway == "stripe"` … `elif` … | [Uso #1](uso.md#varios-provedores) |
| Legado ou código de outro time que você não pode alterar | A mesma conversão de parâmetros e de retorno copiada em vários chamadores | [Uso #2](uso.md#codigo-legado) |
| Dados de fora com os nomes e formatos de fora | Campos do JSON externo (`logradouro`, `localidade`) em telas e regras | [Uso #3](uso.md#payload-externo) |
| Teste difícil por causa da infraestrutura | Para rodar o teste é preciso credencial, rede ou um serviço falso | [Uso #4](uso.md#dependencia-de-infra) |
| Exceções de terceiros capturadas na regra | `except ClientError`, códigos de erro do fornecedor comparados como string | [Uso #4](uso.md#dependencia-de-infra) |
| Estilo de chamada diferente do resto do código | Callback no meio de `async/await`; laço de paginação repetido | [Uso #5](uso.md#callback-promise), [#6](uso.md#paginacao) |
| Um framework pede uma interface específica | Você quer "plugar" algo seu no logging, no storage, no ORM | [Uso #7](uso.md#framework) |

> **Dica.** Repare no que quase todos os sinais têm em comum: o nome de algo de fora aparece onde não deveria. O adaptador é o lugar para onde esse nome se muda — e de onde ele não sai mais.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **Já existe algo pronto que resolve?** Se não, não há o que adaptar: escreva a classe direto, com a interface que você quer.
2. **A interface dele é diferente da que o seu código precisa?** Se é praticamente a mesma, use direto.
3. **Você pode mudar a interface na origem?** Se o código é seu e está ao alcance, mude lá. É mais simples que traduzir para sempre.
4. **A diferença vai aparecer em mais de um lugar, ou atrapalha testar?** Se sim, é Adapter. Se é uma chamada isolada, em um lugar só, ainda dá para esperar.

<a id="quando-nao-usar"></a>
## Quando não usar

O Adapter tem um custo fixo, cobrado todo dia: um arquivo a mais, uma interface a mais e um salto a mais na leitura — o "ir para a definição" cai na interface, não no código que roda. Ele só se paga quando o que protege vale mais que isso.

| Situação | Por que não | Faça isto |
|---|---|---|
| Você controla os dois lados | O adaptador conserta uma diferença que você mesmo pode eliminar | Mude a interface na origem |
| Um fornecedor só, chamado em um lugar só | Não há diferença espalhada para conter; a camada só acrescenta leitura | Chame direto. Extraia o adaptador quando surgir o segundo uso ou o segundo fornecedor |
| Script, protótipo ou código descartável | O código vai embora antes de o custo se pagar | Chame direto |
| A interface alvo seria idêntica à da SDK | Nada é traduzido; o adaptador vira um repasse | Use a SDK, ou redesenhe o alvo nos termos do seu domínio |
| Você quer simplificar um subsistema grande | O objetivo é reduzir a superfície, não converter uma interface em outra | Facade |
| Você quer acrescentar cache, retry ou log mantendo a interface | A interface antes e depois é a mesma | Decorator ou Proxy |

<a id="sinais-de-abuso"></a>
### Sinais de que o adaptador saiu do lugar

- **Ele toma decisões.** Adaptador que valida regra de negócio, repete tentativas ou escolhe caminho deixou de traduzir. Isso é um serviço; dê a ele outro nome e outro lugar.
- **Os tipos do fornecedor vazam pelo retorno.** Se `cobrar()` devolve um `stripe.PaymentIntent`, a interface parece sua, mas o cliente continua dependendo da SDK.
- **O cliente pergunta quem está do outro lado.** Um `isinstance(gateway, GatewayStripe)` na regra mostra que a abstração não está segurando a diferença.
- **Adaptador sobre adaptador.** Duas camadas traduzindo a mesma coisa: uma delas sobra.
- **Um adaptador para cada dependência, "por precaução".** "Vai que um dia trocamos o banco" é abstração especulativa: o custo é cobrado hoje e o dia da troca talvez nunca chegue.

> **Perigo.** O sinal mais comum: a interface alvo cresceu até ficar igual à da SDK, campo por campo. Aí o adaptador não protege de nada — só adiciona um arquivo entre você e o erro.

> **Nota.** Na dúvida, comece sem. Extrair um adaptador de uma chamada direta é uma refatoração pequena, principalmente se a chamada está em um lugar só. O que sai caro é deixar a SDK se espalhar por vinte arquivos antes de decidir.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Facade | Simplifica um subsistema inteiro; o Adapter converte *uma* interface em outra que já existia |
| Decorator | Mantém a mesma interface e acrescenta comportamento; o Adapter muda a interface e não acrescenta nada |
| Bridge | É desenhado antes, para abstração e implementação crescerem separadas; o Adapter entra depois, para consertar um encaixe |
| Proxy | Mesma interface, controlando o acesso (cache, permissão, preguiça) |

Regra prática: se a interface antes e depois é a mesma, não é Adapter.

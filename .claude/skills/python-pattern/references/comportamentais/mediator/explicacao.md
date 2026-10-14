<!-- Gerado de pages/clean-code/comportamentais/mediator/explicacao.html por scripts/sync_references.py. Não edite aqui: edite a página e rode o script. -->

# Mediator — Explicação

*Clean Code / Design Pattern / Mediator*

Como deixar um grupo de objetos trabalhar junto sem que cada um precise conhecer todos os outros, concentrando a conversa entre eles em um único lugar.

<a id="o-problema"></a>
## O problema

O formulário de checkout tem campos que se afetam. Escolher "Pessoa jurídica" mostra o CNPJ e esconde o CPF. Digitar o CEP preenche a rua e a cidade. E o botão Finalizar só habilita quando tudo estiver preenchido, o que depende de todos os campos.

A saída preguiçosa é cada campo guardar uma referência aos outros que ele afeta:

**antes — cada campo conhece os que ele mexe**

```python
class TipoPessoa:
    def __init__(self, cpf, cnpj, botao):
        self.cpf, self.cnpj, self.botao = cpf, cnpj, botao

    def escolher(self, tipo):
        self.valor = tipo
        self.cpf.visivel = tipo == "pf"
        self.cnpj.visivel = tipo == "pj"
        self.botao.habilitado = False          # precisa revalidar tudo

class Cep:
    def __init__(self, rua, cidade, botao):
        self.rua, self.cidade, self.botao = rua, cidade, botao

    def digitar(self, cep):
        self.valor = cep
        endereco = buscar_cep(cep)
        self.rua.valor = endereco.rua
        self.cidade.valor = endereco.cidade
        self.botao.habilitado = bool(self.rua.valor)   # e o documento? o campo não sabe
```

Três coisas quebram daqui a pouco. Cada campo novo (telefone, inscrição estadual) exige mexer em vários campos antigos, para que eles avisem o novo. A regra do botão está espalhada: cada campo decide uma parte, e ninguém tem a visão completa. E nenhum campo serve em outro formulário, porque o `Cep` só funciona se alguém lhe entregar uma rua, uma cidade e um botão.

<a id="a-solucao"></a>
## A solução

Tire a conversa de dentro dos campos e ponha-a em um objeto no meio. Cada campo passa a conhecer só esse objeto: ele avisa "mudei" e não sabe o que acontece depois. O objeto do meio conhece todos os campos e decide a reação. São quatro papéis:

| Papel | Quem é | No exemplo |
|---|---|---|
| Mediador | A interface que os colegas conhecem | `mudou(origem)` |
| Mediador concreto | Conhece todos os colegas e concentra as regras de interação | `FormularioCheckout` |
| Colegas | Os objetos que se afetam; só sabem avisar o mediador | Os campos e o botão |
| Cliente | Cria o mediador, que cria e liga os colegas | A tela de checkout |

O ponto é o que cada lado precisa saber. Os colegas ficam **simples e reutilizáveis**: um campo de CEP não sabe que existe um botão. O custo foi para o mediador, que agora sabe de todos. Em troca, as regras de interação, que antes estavam espalhadas, ficam em um lugar onde podem ser lidas e mudadas.

<a id="implementacao"></a>
## Implementação

```python
# 1. os colegas: só sabem avisar o mediador, nunca falam entre si
class Componente:
    def __init__(self, mediador):
        self._mediador = mediador
        self.valor = ""
        self.visivel = True
        self.habilitado = True

    def alterar(self, valor):
        self.valor = valor
        self._mediador.mudou(self)

# 2. o mediador concreto: conhece todos e concentra as regras
class FormularioCheckout:
    def __init__(self):
        self.tipo = Componente(self)
        self.cpf = Componente(self)
        self.cnpj = Componente(self)
        self.cep = Componente(self)
        self.rua = Componente(self)
        self.cidade = Componente(self)
        self.finalizar = Componente(self)

    def mudou(self, origem):
        if origem is self.tipo:
            self.cpf.visivel = self.tipo.valor == "pf"
            self.cnpj.visivel = self.tipo.valor == "pj"
        elif origem is self.cep:
            endereco = buscar_cep(self.cep.valor)
            self.rua.valor = endereco.rua
            self.cidade.valor = endereco.cidade
        self.finalizar.habilitado = self._valido()

    def _valido(self):
        documento = self.cpf if self.tipo.valor == "pf" else self.cnpj
        return bool(documento.valor and self.rua.valor and self.cidade.valor)

# 3. o cliente: usa o formulário, sem saber quem afeta quem
form = FormularioCheckout()
form.tipo.alterar("pj")       # o CNPJ aparece e o CPF some, sem ninguém ter chamado ninguém
```

> **Dica.** O teste vira uma tabela: crie o formulário, altere um campo, confira o estado dos outros. E o `Componente` funciona em qualquer outro formulário, porque tudo o que ele conhece é a interface `Mediador`, que um teste preenche com uma classe de duas linhas.

<a id="quando-usar"></a>
## Quando usar

O Mediator vale quando três coisas acontecem ao mesmo tempo: um **grupo de objetos** precisa se coordenar; hoje cada um **guarda referências** aos outros, ou sabe o bastante sobre eles para reagir; e as regras da conversa **mudam**, ou os próprios objetos ficam **presos ao grupo** e não servem em outro lugar.

Na prática, isso aparece no código de algumas formas reconhecíveis:

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Objetos de interface que se mostram, preenchem e habilitam uns aos outros | `self.botao.habilitado = …` dentro de um campo; um `onChange` que mexe em três outros elementos | O exemplo desta página |
| Participantes que trocam mensagens entre si | Uma lista `outros` ou `contatos` em cada objeto; para sair, é preciso se remover de todos | [Uso #1](uso.md#sala-de-chat) |
| Serviços que chamam o próximo passo do fluxo | `self.envio.agendar(...)` no fim de outro serviço; imports circulares entre eles | [Uso #2](uso.md#orquestracao-de-pedido) |
| A regra depende do par de objetos que se encontram | `isinstance(outro, X)` dentro de cada classe, com a mesma regra escrita dos dois lados | [Uso #3](uso.md#regras-entre-pares) |
| Uma classe que não dá para usar sozinha | O construtor pede cinco outros objetos só para funcionar, e o teste monta o grupo inteiro | O exemplo desta página |

> **Dica.** O que os sinais têm em comum: a conversa entre os objetos está espalhada dentro deles. Procure a regra "quando A muda, B reage" e veja em quantos arquivos você precisa olhar para encontrá-la inteira.

<a id="teste-rapido"></a>
### Um teste rápido

Na dúvida, responda em ordem. A primeira resposta que manda parar decide.

1. **São mais de dois objetos que se afetam?** Se são só dois, uma chamada direta ou um callback resolve.
2. **Eles guardam referências uns aos outros, ou sabem uns dos outros?** Se cada um age só sobre si, não há conversa a mediar.
3. **As regras ou os participantes mudam?** Se o grupo é fixo e pequeno, deixe-os se falando.
4. **A coordenação cabe em um lugar sem virar um monstro?** Se são dezenas de regras, uma só classe não é a resposta: divida por responsabilidade.

<a id="quando-nao-usar"></a>
## Quando não usar

O Mediator não elimina a complexidade da conversa: ele a muda de lugar. O custo é um objeto que sabe de todos, e esse objeto tende a crescer até virar o "God Object" do sistema. A leitura também fica indireta: para entender o que acontece quando o campo muda, você lê o `mudou` do mediador, e não o campo.

| Situação | Por que não | Faça isto |
|---|---|---|
| Só dois objetos conversam | O intermediário seria uma classe a mais entre duas peças que já se entendem | Chamada direta, ou um callback |
| O objetivo é avisar quem estiver interessado, sem regra nenhuma | Não há lógica de coordenação, só distribuição de avisos | Observer (um emissor de eventos) |
| Simplificar o uso de um subsistema por quem está de fora | A comunicação é de mão única, e os objetos de dentro não conversam entre si | Facade |
| O mediador já tem dezenas de regras | Ele virou o objeto que sabe tudo, e mudar qualquer coisa o quebra | Divida por tema (um mediador por tela ou por fluxo) ou use uma máquina de estados |
| Os objetos só precisam ler um dado em comum | Não há conversa entre eles, só estado compartilhado | Um objeto de estado único, com funções para alterá-lo |

<a id="sinais-de-abuso"></a>
### Sinais de que o Mediator saiu do lugar

- **O mediador é um God Object.** Centenas de linhas e as regras de negócio de todo mundo. O acoplamento não sumiu: mudou de endereço e ganhou um ponto único de risco.
- **Os colegas ainda se falam.** Metade das interações passa pelo mediador, e a outra metade continua por referência direta. Ninguém sabe qual vale onde.
- **O mediador testa tipos.** Uma cadeia de `isinstance` sobre as classes concretas de todos os colegas mostra que ele depende de cada detalhe deles.
- **Um mediador global para o sistema.** Um "barramento de tudo", ao qual todo módulo se conecta, é uma variável global com outro nome.
- **O mediador só repassa.** Sem regra nenhuma, ele é um Observer, e fica mais barato escrito como um.

> **Perigo.** O sinal mais comum: o mediador acumula as regras de todo o sistema. Nenhum colega ficou mais simples; só o acoplamento trocou de lugar, e agora qualquer alteração passa por um arquivo que ninguém quer abrir.

> **Nota.** Na dúvida, deixe os dois objetos conversarem direto. Extraia o mediador quando o terceiro objeto entrar na conversa. Nesse ponto a refatoração ainda é pequena, e o emaranhado ainda não tem forma.

<a id="parecidos"></a>
## Parecidos

| Padrão | Diferença |
|---|---|
| Observer | O emissor não sabe quem escuta e não coordena nada. O Mediator conhece os colegas e tem regras sobre quem reage a quê; nele, a comunicação é nos dois sentidos |
| Facade | Simplifica o uso de um subsistema para quem está de fora, em um sentido só. No Mediator, os objetos de dentro conhecem o mediador e conversam por ele |
| [Command](../command/explicacao.md) | É o pedido transformado em objeto. Combina com o Mediator: o que o mediador recebe e despacha costuma ser um Command |
| [Chain of Responsibility](../chain-of-responsibility/explicacao.md) | Passa o pedido adiante até alguém tratar, sem saber quem. O Mediator conhece todos os colegas e decide diretamente quem é afetado |

Regra prática: se os objetos precisam se conhecer um pouco para trabalhar juntos e você os faz conhecer só o intermediário, é Mediator. Se quem avisa não sabe e não se importa com quem recebe, é Observer.

<!-- Gerado por scripts/sync_references.py a partir de pages/clean-code. Não edite aqui. -->

# Índice de sinais

Use este índice na fase de diagnóstico: procure no código analisado os sinais da coluna "Como reconhecer". Um sinal encontrado é uma **hipótese**, não uma decisão: antes de planejar, abra a página do princípio ou do pattern e confira "Quando não usar" / "Quando não aplicar" e o "Teste rápido".

## Sumário

- [SOLID](#solid)
- [Criacionais](#criacionais)
- [Estruturais](#estruturais)
- [Comportamentais](#comportamentais)

<a id="solid"></a>
## SOLID

### S — [Single Responsibility](single-responsibility.md)

Como evitar que uma classe quebre toda vez que qualquer pessoa da empresa muda de ideia, dando a cada motivo de mudança o seu próprio lugar.

| Sintoma | O que está acontecendo |
|---|---|
| Nome com `Manager`, `Helper`, `Utils` ou "`E`" no meio (`ValidaESalva`) | O nome não consegue dizer uma coisa só porque ela não é uma coisa só |
| Imports de mundos distantes no mesmo arquivo: `sqlalchemy`, `smtplib`, `reportlab` | A classe fala com banco, rede e disco além da regra |
| Grupos de métodos que usam atributos diferentes | Há duas classes escondidas dentro de uma |
| Conflito de merge sempre no mesmo arquivo, por pessoas de áreas diferentes | Vários atores pedem mudança no mesmo lugar |
| Teste unitário que precisa de mock de tudo | O que você quer testar está preso ao que não quer |

Antes de aplicar: [Quando não aplicar](single-responsibility.md#quando-nao-aplicar).

### O — [Open/Closed](open-closed.md)

Como acrescentar um caso novo escrevendo código novo, sem reabrir e retestar o código que já funcionava.

| Sintoma | O que está acontecendo |
|---|---|
| `if tipo == …` / `switch (tipo)` repetido em mais de um lugar | O mesmo eixo de variação está espalhado; cada caso novo toca todos os pontos |
| Histórico do `git` mostrando "adiciona X" sempre editando a mesma função | A função é o ponto de extensão, mas sem abstração nenhuma |
| Enum que cresce junto com cada `switch` que o usa | O enum virou uma lista de casos que ninguém pode esquecer |
| Medo de mexer: "se eu tocar aqui, quebra o outro cliente" | Casos diferentes compartilham código que não deveriam |

Antes de aplicar: [Quando não aplicar](open-closed.md#quando-nao-aplicar).

### L — [Liskov Substitution](liskov-substitution.md)

Como garantir que uma subclasse pode entrar no lugar da classe base sem que quem chama precise perguntar "que tipo você é?".

| Sintoma | O que está acontecendo |
|---|---|
| `raise NotImplementedError` ou `throw new Error("não suportado")` numa sobrescrita | A subclasse recusa parte do contrato que herdou |
| Método sobrescrito vazio, ou que só devolve um valor "neutro" | A promessa foi esvaziada em silêncio, o que é pior que um erro |
| `isinstance` / `instanceof` / `type(x) == …` em quem usa a base | Quem chama já aprendeu que não pode confiar na base |
| Subclasse que valida mais que a base (`if valor > 1000: raise`) | Pré-condição ficou mais forte |
| Classe base com um comentário "não chamar em subclasse X" | A exceção está documentada em vez de modelada |

Antes de aplicar: [Quando não aplicar](liskov-substitution.md#quando-nao-aplicar).

### I — [Interface Segregation](interface-segregation.md)

Como evitar que uma classe seja obrigada a implementar, e quem a usa a conhecer, métodos que não têm nada a ver com o que ela faz.

| Sintoma | O que está acontecendo |
|---|---|
| Implementações com métodos que só lançam `NotImplementedError` ou ficam vazios | A interface pede mais do que a classe consegue honrar |
| Interface com 8 ou 10 métodos, e cada cliente usa dois | Vários papéis foram colados em um nome só |
| Falso de teste enorme, quase todo `pass` | O teste precisa fingir o que não usa |
| Mudança num método que ninguém chama quebra o build de quem implementa | Dependência por conveniência, não por necessidade |
| Parâmetro tipado como o serviço inteiro, usado para um único método | Quem chama depende do mundo para usar um pedaço |

Antes de aplicar: [Quando não aplicar](interface-segregation.md#quando-nao-aplicar).

### D — [Dependency Inversion](dependency-inversion.md)

Como fazer a regra de negócio mandar na infraestrutura, e não o contrário, para trocar banco, e-mail ou relógio sem tocar nas regras.

| Sintoma | O que está acontecendo |
|---|---|
| `import` de driver, SDK ou framework dentro do arquivo da regra | A regra conhece o detalhe pelo nome |
| `new` / construtor de classe concreta dentro de método de negócio | A regra decide qual detalhe usa, e não dá para trocar |
| `datetime.now()`, `random()`, `os.environ` no meio da regra | Até o relógio e o ambiente são dependências escondidas, e tornam o teste instável |
| Teste unitário que usa `patch("módulo.biblioteca")` para tudo | O teste precisa sabotar o código para escapar da dependência |
| Singleton ou variável global acessada de dentro da regra | Dependência escondida: a assinatura diz uma coisa, o corpo precisa de outra |

Antes de aplicar: [Quando não aplicar](dependency-inversion.md#quando-nao-aplicar).

<a id="criacionais"></a>
## Criacionais

### [Abstract Factory](criacionais/abstract-factory/explicacao.md) · uso: média

Como criar um conjunto de objetos que precisam combinar entre si, sem que o código principal escolha cada peça e sem o risco de misturar peças de conjuntos diferentes.

**Regra.** A Abstract Factory vale quando as três coisas acontecem ao mesmo tempo: existem **várias famílias** de variantes (dois ambientes, dois temas, dois países), as peças de uma família **só funcionam bem juntas**, e o cliente precisa criar **várias peças** sem conhecer a família.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Peças escolhidas pelo mesmo critério, uma depois da outra | Dois ou três `if tema == …` ou `if AMBIENTE == …` em sequência, com a mesma condição | [Uso #1](criacionais/abstract-factory/uso.md#pecas-que-combinam) |
| Bugs de "peça de um conjunto com peça de outro" | Texto claro sobre fundo claro; caminho de disco em uma fila de nuvem; um ternário invertido em um dos componentes | [Uso #1](criacionais/abstract-factory/uso.md#pecas-que-combinam) |
| Objetos que precisam do mesmo contexto, criados em lugares separados | Cada repositório ou cliente chama `connect()` por conta própria, e as operações deviam estar na mesma transação | [Uso #2](criacionais/abstract-factory/uso.md#contexto-compartilhado) |
| O mesmo critério repetido em vários arquivos e funções | `if pais == "BR"` em `emitir()`, em `cancelar()`, em `reemitir()`… | [Uso #3](criacionais/abstract-factory/uso.md#familia-por-pedido) |
| Um ambiente novo exige mexer em muitos lugares | Uma busca por `"staging"` devolve 15 arquivos | [Uso #3](criacionais/abstract-factory/uso.md#familia-por-pedido) |

**Teste rápido.**

1. **Você cria mais de um tipo de objeto com o mesmo critério?** Se é um tipo só, use Factory Method ou uma função.
2. **Misturar peças de variantes diferentes é um erro, ou só algo estranho?** Se misturar não faz mal, injete cada peça separada.
3. **Existem pelo menos duas famílias completas?** Se só existe uma, não há o que escolher: crie direto.
4. **A lista de peças é estável?** Se um produto novo aparece toda semana, cada um mexe na interface e em todas as fábricas — pese isso antes de seguir.

Antes de aplicar: [Quando não usar](criacionais/abstract-factory/explicacao.md#quando-nao-usar) · [Parecidos](criacionais/abstract-factory/explicacao.md#parecidos) · [Exemplos](criacionais/abstract-factory/uso.md).

### [Builder](criacionais/builder/explicacao.md) · uso: alta

Como montar um objeto complexo por partes, em etapas, e só entregá-lo quando estiver completo e válido — em vez de deixá-lo circulando pela metade.

**Regra.** O Builder vale quando as três coisas acontecem ao mesmo tempo: o objeto é **montado em etapas** (em mais de um lugar, ou acumulando partes), só é válido **completo**, e você quer que ele **nasça pronto** — imutável, ou com o mesmo roteiro gerando saídas diferentes.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um objeto passa por várias funções que o preenchem | `adicionar_x(obj)`, `anexar_y(obj)`, `aplicar_z(obj)` em sequência, antes de alguém usá-lo | — |
| Validação espalhada por quem usa | `if not obj.assunto` repetido em cada função que recebe o objeto | — |
| O mesmo roteiro com saídas diferentes | `if formato == "html"` dentro de cada passo da geração | [Uso #1](criacionais/builder/uso.md#mesmo-roteiro) |
| Duas coleções mantidas em sincronia | `sql += …` junto de `params.append(…)`, em todo ramo | [Uso #2](criacionais/builder/uso.md#estado-interno) |
| Montar o objeto no teste dá mais trabalho que o teste | Dez linhas de construção para afirmar sobre um único campo | [Uso #3](criacionais/builder/uso.md#dados-de-teste) |

**Teste rápido.**

1. **O objeto tem poucos campos, todos conhecidos de uma vez?** Use o construtor, com argumentos nomeados.
2. **O problema é só "muitos parâmetros opcionais"?** Argumentos nomeados, um dataclass ou um objeto de opções resolvem sem uma classe nova.
3. **Existe montagem em etapas, validação do conjunto, ou mais de uma saída?** Se nenhuma das três, não é caso de Builder.
4. **Alguém pode usar o objeto antes de ele estar pronto?** Se sim, é exatamente o que o Builder resolve.

Antes de aplicar: [Quando não usar](criacionais/builder/explicacao.md#quando-nao-usar) · [Parecidos](criacionais/builder/explicacao.md#parecidos) · [Exemplos](criacionais/builder/uso.md).

### [Factory Method](criacionais/factory-method/explicacao.md) · uso: muito alta

Como deixar o código principal criar um objeto sem saber qual classe exata está criando, entregando essa escolha para as subclasses.

**Regra.** O Factory Method vale quando três coisas acontecem ao mesmo tempo: o código **precisa criar** um objeto cujo tipo exato ele não deveria conhecer; o resto do fluxo é **comum** e só o objeto criado muda; e **subclasses** já existem (ou fazem sentido) porque as variantes diferem em outras coisas além da criação.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um método longo em que só a linha de criação muda entre variantes | `if self.tipo == …` escolhendo qual classe instanciar, no meio de um fluxo que repete igual | [Uso #1](criacionais/factory-method/uso.md#fluxo-fixo) |
| Uma biblioteca ou classe base que outros times estendem | A biblioteca importa as classes concretas de quem a usa; cada necessidade nova vira PR nela | [Uso #2](criacionais/factory-method/uso.md#ponto-de-extensao) |
| A mesma escolha de tipo em vários métodos da mesma classe | A mesma cadeia `if`/`elif` ou `isinstance` copiada em `novo()`, `abrir()` e `duplicar()` | [Uso #3](criacionais/factory-method/uso.md#tipo-em-um-lugar) |
| Teste que precisa trocar um objeto criado no meio de um método | `@patch("modulo.requests.get")`; o objeto é criado dentro do método e o construtor não aceita parâmetros | [Uso #4](criacionais/factory-method/uso.md#costura-de-teste) |

**Teste rápido.**

1. **O tipo criado muda?** Se é sempre a mesma classe, chame `Classe()` direto.
2. **A escolha vem de um dado em tempo de execução** (extensão do arquivo, campo do JSON, string de configuração)? Então use uma função fábrica ou um mapa: o Factory Method pede que a escolha seja feita por *quem é a subclasse*, não por um valor.
3. **As variantes diferem só na criação?** Então não precisa de herança: receba a fábrica (ou o próprio objeto) por parâmetro.
4. **Existe um fluxo comum, e as variantes são subclasses por outros motivos?** Se sim, Factory Method.

Antes de aplicar: [Quando não usar](criacionais/factory-method/explicacao.md#quando-nao-usar) · [Parecidos](criacionais/factory-method/explicacao.md#parecidos) · [Exemplos](criacionais/factory-method/uso.md).

### [Prototype](criacionais/prototype/explicacao.md) · uso: baixa

Como criar um objeto novo copiando um que já existe, deixando a regra da cópia dentro do próprio objeto — para quem copia não precisar conhecer a classe nem os campos.

**Regra.** O Prototype vale quando as três coisas acontecem ao mesmo tempo: você precisa de uma **cópia independente** de um objeto que já existe, o **cliente não deveria conhecer** a classe nem os campos, e **copiar é melhor** que construir de novo — mais barato, mais fiel, ou a única coisa possível.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Uma função de duplicar que reconstrói campo a campo | `Campanha(nome=o.nome, assunto=o.assunto, …)`, com a lista de campos copiada à mão | — |
| Cópia que depende do tipo | `if isinstance(x, A): return A(…)` só para duplicar | — |
| A mesma montagem cara, repetida com o mesmo resultado | A mesma consulta ou o mesmo `parse()` a cada objeto novo; só o final muda | [Uso #1](criacionais/prototype/uso.md#custo-de-criacao) |
| Uma subclasse para cada variante de configuração | Classes que só diferem em valores atribuídos no construtor | [Uso #2](criacionais/prototype/uso.md#modelos-do-usuario) |
| Guardar o "estado anterior" campo a campo | `self._anterior = {"tema": c.tema, …}`, para poder cancelar a edição | [Uso #3](criacionais/prototype/uso.md#rascunho-e-desfazer) |
| "Mexi na cópia e mudou o original" | Uma lista, um dicionário ou um objeto interno compartilhado entre os dois | — |

**Teste rápido.**

1. **Você precisa de uma cópia, ou de um objeto novo com valores novos?** Se é novo, é um construtor.
2. **O objeto é simples, com poucos campos de valor?** Então `dataclasses.replace(obj, nome="…")` (ou o spread `{ ...obj, nome }`) basta.
3. **O objeto guarda algo que não pode ser copiado** — conexão, arquivo, trava, thread? Então a cópia não faz sentido: crie um novo por uma fábrica.
4. **Existe uma regra do que a cópia leva, do que compartilha e do que zera?** Se sim, ela precisa morar em um método. É o Prototype.

Antes de aplicar: [Quando não usar](criacionais/prototype/explicacao.md#quando-nao-usar) · [Parecidos](criacionais/prototype/explicacao.md#parecidos) · [Exemplos](criacionais/prototype/uso.md).

### [Singleton](criacionais/singleton/explicacao.md) · uso: alta

Como garantir que um objeto existe uma vez só e que todo mundo chega nele, em vez de cada parte do sistema criar a sua própria cópia do que deveria ser único.

**Regra.** O Singleton vale quando as três coisas acontecem ao mesmo tempo: ter **duas instâncias é um erro** (ou um custo alto demais), **vários pontos distantes** do código precisam da mesma, e o objeto vive **o processo inteiro**.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Recurso caro criado de novo a cada uso | `connect()` ou `load()` dentro de método de repositório ou de construtor de serviço | [Uso #1](criacionais/singleton/uso.md#recurso-caro) |
| Duas cópias de um estado que deveria ser um só | `new Limitador()` em mais de um arquivo; o bug "só acontece em algumas telas" | [Uso #2](criacionais/singleton/uso.md#estado-compartilhado) |
| Várias partes mexendo no mesmo recurso exclusivo | Ler, somar e gravar no mesmo arquivo; dois números iguais em registros diferentes | [Uso #3](criacionais/singleton/uso.md#recurso-exclusivo) |
| Objeto pesado, nem sempre necessário | `global _modelo` com `if _modelo is None`; carga no `import` que atrasa o início | [Uso #4](criacionais/singleton/uso.md#criacao-concorrente) |
| Unicidade desejada, mas o acesso global atrapalha | Teste que altera `X.instancia()` e contamina os seguintes; `reset()` só para teste | [Uso #5](criacionais/singleton/uso.md#sem-global) |

**Teste rápido.**

1. **Ter duas instâncias quebra algo, ou só desperdiça um pouco?** Se só desperdiça, crie normalmente.
2. **Dá para criar uma na inicialização e passá-la a quem precisa?** Se sim, faça isso: você tem a unicidade sem o acesso global.
3. **Uma variável de módulo resolve?** Em Python e em JavaScript, quase sempre resolve.
4. **Só depois disso:** Singleton, com criação preguiçosa e trava, se houver concorrência.

Antes de aplicar: [Quando não usar](criacionais/singleton/explicacao.md#quando-nao-usar) · [Parecidos](criacionais/singleton/explicacao.md#parecidos) · [Exemplos](criacionais/singleton/uso.md).

<a id="estruturais"></a>
## Estruturais

### [Adapter](estruturais/adapter/explicacao.md) · uso: muito alta

Como encaixar uma interface que você não controla na interface que o seu código espera, sem espalhar a diferença pelo sistema inteiro.

**Regra.** O Adapter vale quando três coisas acontecem ao mesmo tempo: **já existe** algo que faz o que você precisa, a interface dele **não é** a que o seu código quer, e mudar esse algo **não é opção** — porque é de terceiros, é legado ou é de outro time.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Dependência externa no meio da regra de negócio | `import` de SDK em arquivo de domínio; o nome do fornecedor aparece dentro da regra | [Uso #1](estruturais/adapter/uso.md#varios-provedores) |
| Dois fornecedores para a mesma operação, ou um segundo à vista | `if gateway == "stripe"` … `elif` … | [Uso #1](estruturais/adapter/uso.md#varios-provedores) |
| Legado ou código de outro time que você não pode alterar | A mesma conversão de parâmetros e de retorno copiada em vários chamadores | [Uso #2](estruturais/adapter/uso.md#codigo-legado) |
| Dados de fora com os nomes e formatos de fora | Campos do JSON externo (`logradouro`, `localidade`) em telas e regras | [Uso #3](estruturais/adapter/uso.md#payload-externo) |
| Teste difícil por causa da infraestrutura | Para rodar o teste é preciso credencial, rede ou um serviço falso | [Uso #4](estruturais/adapter/uso.md#dependencia-de-infra) |
| Exceções de terceiros capturadas na regra | `except ClientError`, códigos de erro do fornecedor comparados como string | [Uso #4](estruturais/adapter/uso.md#dependencia-de-infra) |
| Estilo de chamada diferente do resto do código | Callback no meio de `async/await`; laço de paginação repetido | [Uso #5](estruturais/adapter/uso.md#callback-promise), [#6](estruturais/adapter/uso.md#paginacao) |
| Um framework pede uma interface específica | Você quer "plugar" algo seu no logging, no storage, no ORM | [Uso #7](estruturais/adapter/uso.md#framework) |

**Teste rápido.**

1. **Já existe algo pronto que resolve?** Se não, não há o que adaptar: escreva a classe direto, com a interface que você quer.
2. **A interface dele é diferente da que o seu código precisa?** Se é praticamente a mesma, use direto.
3. **Você pode mudar a interface na origem?** Se o código é seu e está ao alcance, mude lá. É mais simples que traduzir para sempre.
4. **A diferença vai aparecer em mais de um lugar, ou atrapalha testar?** Se sim, é Adapter. Se é uma chamada isolada, em um lugar só, ainda dá para esperar.

Antes de aplicar: [Quando não usar](estruturais/adapter/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/adapter/explicacao.md#parecidos) · [Exemplos](estruturais/adapter/uso.md).

### [Bridge](estruturais/bridge/explicacao.md) · uso: baixa

Como deixar duas coisas que variam por motivos diferentes crescerem separadas, em vez de multiplicar uma subclasse para cada combinação.

**Regra.** O Bridge vale quando três coisas acontecem ao mesmo tempo: existem **duas dimensões** de variação, cada uma tem **mais de uma variante** (ou a segunda está confirmada), e a escolha em uma **não depende** da escolha na outra.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Nomes de classe que juntam duas ideias | `RelatorioDeVendasCsv`, `CobrancaPorSms`: um "o quê" colado a um "como" | [Uso #1](estruturais/bridge/uso.md#avisos-e-canais) |
| Cada novo X exige uma subclasse por Y | Um pull request para "adicionar WhatsApp" que cria uma classe em cada tipo de aviso | [Uso #1](estruturais/bridge/uso.md#avisos-e-canais) |
| A mesma lógica precisa rodar sobre plataformas diferentes | `if typeof document === "undefined"` ou `if sys.platform == …` dentro de uma regra | [Uso #2](estruturais/bridge/uso.md#mesmo-grafico-varios-ambientes) |
| Implementações escritas por outras pessoas, em número aberto | Uma classe central com `if banco == "postgres"` … `elif banco == "mysql"` em cada método | [Uso #3](estruturais/bridge/uso.md#bancos-de-dados) |
| A mesma lógica de alto nível copiada em cada implementação | `PostgresRelatorio` e `MysqlRelatorio` com o mesmo laço, diferindo em duas linhas | [Uso #3](estruturais/bridge/uso.md#bancos-de-dados) |

**Teste rápido.**

1. **Mais de uma coisa varia, de verdade?** Se só uma dimensão tem variantes, é herança simples, ou Strategy se você escolhe o algoritmo em tempo de execução. Pare.
2. **As duas dimensões são independentes?** Se só alguns pares fazem sentido (estoque nunca sai em PDF), não são eixos: são combinações. Modele as que existem.
3. **Você consegue descrever cada lado sem citar o outro?** "O que entra no relatório" e "como ele é escrito" funcionam. Se para explicar um você precisa do outro, a ponte vai vazar.
4. **Já são mais de 2 × 2, ou o terceiro está a caminho?** Se são 4 classes e vão continuar 4, a herança direta custa menos. Se o terceiro formato ou o terceiro tipo já tem data, é Bridge.

Antes de aplicar: [Quando não usar](estruturais/bridge/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/bridge/explicacao.md#parecidos) · [Exemplos](estruturais/bridge/uso.md).

### [Composite](estruturais/composite/explicacao.md) · uso: média

Como tratar um item e um grupo de itens do mesmo jeito, para que o código que usa a estrutura não precise saber em que profundidade está.

**Regra.** O Composite vale quando três coisas acontecem ao mesmo tempo: os dados formam uma **árvore** (um todo que contém partes), os grupos podem conter outros grupos em uma **profundidade que você não controla**, e quem usa a estrutura quer **tratar um nó e um grupo da mesma forma**.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Quem usa a estrutura pergunta o tipo antes de agir | `isinstance(no, Pasta)` ou `instanceof` no começo de cada função que percorre a árvore | [Uso #1](estruturais/composite/uso.md#pastas-e-arquivos) |
| Várias operações percorrem a mesma árvore | A mesma escada de `for` + `if` reescrita para tamanho, busca, contagem | [Uso #1](estruturais/composite/uso.md#pastas-e-arquivos) |
| Condições que se combinam com E, OU e NÃO | Tipos como `"primeira_compra_e_valor_minimo"`; um `if` novo por combinação pedida | [Uso #2](estruturais/composite/uso.md#regras-combinaveis) |
| Uma função que atende "uma pessoa ou várias" | `if isinstance(destino, list)`; pares `enviar_para_um` e `enviar_para_varios` | [Uso #3](estruturais/composite/uso.md#um-ou-varios-destinatarios) |
| Filtrar uma árvore e depois limpar os pais vazios | Uma segunda passada para remover "grupos sem nada dentro" | [Uso #4](estruturais/composite/uso.md#menu-com-permissoes) |

**Teste rápido.**

1. **Um item contém outros itens do mesmo tipo?** Se é uma lista simples de coisas diferentes (um carrinho com produtos), não é parte-todo. Pare.
2. **A profundidade pode variar?** Se são sempre dois níveis (categoria e produto), duas classes com tipos diferentes dizem mais que uma interface comum.
3. **Folha e grupo respondem à mesma operação?** Se a pergunta só faz sentido em um deles, não há interface comum honesta.
4. **Mais de uma operação percorre a árvore, ou ela vem de dados?** Se é uma única função em um único lugar, uma recursão com `isinstance` é mais simples. Se são várias, ou a árvore é montada em tempo de execução, é Composite.

Antes de aplicar: [Quando não usar](estruturais/composite/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/composite/explicacao.md#parecidos) · [Exemplos](estruturais/composite/uso.md).

### [Decorator](estruturais/decorator/explicacao.md) · uso: alta

Como acrescentar comportamento a um objeto sem mexer nele e sem criar uma subclasse para cada combinação de extras.

**Regra.** O Decorator vale quando três coisas acontecem ao mesmo tempo: você quer **acrescentar** algo a um objeto que já tem uma interface, o acréscimo é **independente** do que está sendo embrulhado (cache vale para qualquer catálogo), e as **combinações variam** conforme o uso, ou você não pode (ou não quer) alterar a classe.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Recursos transversais ligados e desligados por parâmetro | Um construtor com `usar_cache=`, `logar=`, `tentativas=` e um `if self._logar` dentro de cada método | [Implementação, acima](estruturais/decorator/explicacao.md#implementacao) |
| Subclasses cujo nome lista os extras | `IngressoMeiaComCombo`, `IngressoMeiaComComboVip`: um "Com" acumulando | [Uso #1](estruturais/decorator/uso.md#adicionais-no-checkout) |
| Adicionais que o usuário escolhe em tempo de execução | Booleanos na assinatura (`combo=False, vip=False`) e um `if` para cada um, repetido em preço e em descrição | [Uso #1](estruturais/decorator/uso.md#adicionais-no-checkout) |
| Comportamento a acrescentar a um objeto que passa por vários consumidores | Contagem, limite ou hash misturados ao laço que lê; `.read()` chamado duas vezes | [Uso #2](estruturais/decorator/uso.md#upload-com-limite) |
| O mesmo trecho no início e no fim de dezenas de funções | O `try/finally` de métrica ou o `if not permitido` copiado em cada handler | [Uso #3](estruturais/decorator/uso.md#funcoes-de-handler) |

**Teste rápido.**

1. **O acréscimo é independente do que está embrulhado?** Se ele precisa de campos privados ou de detalhes internos, não dá para fazer de fora: é subclasse, ou uma mudança na própria classe. Pare.
2. **A interface pode continuar a mesma?** Se o acréscimo exige que o cliente chame um método novo, deixou de ser decorador: é outra interface, e o nome do que você quer é Adapter ou Facade.
3. **O acréscimo é opcional ou varia por uso?** Se todo uso precisa dele, sempre, e a classe é sua, escreva dentro dela. A camada só custa mais um salto.
4. **Existe mais de um acréscimo, ou ele vai ser usado em mais de um lugar?** Se é um só, em um lugar só, deixe no corpo. Se são dois ou mais, ou o mesmo em vários lugares, é Decorator.

Antes de aplicar: [Quando não usar](estruturais/decorator/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/decorator/explicacao.md#parecidos) · [Exemplos](estruturais/decorator/uso.md).

### [Facade](estruturais/facade/explicacao.md) · uso: muito alta

Como dar uma porta de entrada simples para um conjunto de peças que só funcionam quando chamadas na ordem certa, para que quem usa não precise conhecer cada uma.

**Regra.** O Facade vale quando três coisas acontecem ao mesmo tempo: existe um subsistema com **várias peças**, os chamadores **repetem** a mesma sequência de uso (a ordem, a configuração, o desfazer), e a **maioria** deles só precisa do caminho comum.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um fluxo de vários passos copiado por vários chamadores | A mesma sequência `reservar → autorizar → contratar → emitir` em controller, app e job, com os `except` copiados junto | [Implementação, acima](estruturais/facade/explicacao.md#implementacao) |
| Uma ferramenta ou SDK com muitas opções, e um uso real pequeno | `subprocess.run([...flags...])` ou um cliente com dez parâmetros, repetido com pequenas variações | [Uso #1](estruturais/facade/uso.md#ffmpeg-e-ffprobe) |
| Módulos importando os internos uns dos outros | `from pagamentos.gateway.stripe_adapter import …` por todo o projeto; refatorar por dentro quebra imports distantes | [Uso #2](estruturais/facade/uso.md#fronteira-de-modulo) |
| Subir e derrubar vários componentes em ordem | Blocos de *setup* copiados entre testes e scripts; um `finally` que esquece um dos componentes | [Uso #3](estruturais/facade/uso.md#ambiente-de-teste) |

**Teste rápido.**

1. **O chamador precisa combinar várias peças?** Se o subsistema é uma classe com um método, não há o que simplificar. Pare.
2. **Mais de um chamador repete a mesma combinação?** Se só um usa, uma função com nome já organiza. Se cada um combina de um jeito próprio, uma fachada não serve a nenhum deles.
3. **A maioria dos usos é o caminho comum?** Se a maioria precisa de controle fino sobre cada peça, a fachada vira obstáculo, e as pessoas passam a contorná-la.
4. **Você consegue nomear o método pelo que o chamador quer?** `finalizar` é um bom nome. `executar_fluxo_de_pedido` costuma ser sinal de que o caso de uso ainda não está claro.

Antes de aplicar: [Quando não usar](estruturais/facade/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/facade/explicacao.md#parecidos) · [Exemplos](estruturais/facade/uso.md).

### [Flyweight](estruturais/flyweight/explicacao.md) · uso: rara

Como manter centenas de milhares de objetos na memória sem repetir, em cada um, o que é igual para todos do mesmo tipo.

**Regra.** O Flyweight vale quando quatro coisas acontecem ao mesmo tempo: há **muitos objetos** (dezenas de milhares ou mais), uma parte relevante do estado deles é **igual** entre muitos, essa parte pode ser **imutável**, e a memória (ou o custo de criar) é um problema que você **mediu**.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Muitos objetos, cada um com a mesma cópia de algo pesado | `self.icone = carregar(...)` no `__init__` de algo criado em laço de milhares; a memória cresce com a contagem | [Implementação, acima](estruturais/flyweight/explicacao.md#implementacao) |
| Registros com os mesmos valores repetidos | Colunas de texto de poucos valores (país, status, categoria) em milhões de linhas; `len(set(coluna))` muito menor que o total | [Uso #1](estruturais/flyweight/uso.md#valores-repetidos) |
| Um objeto imutável e caro de construir, criado de novo a cada uso | Um construtor que lê arquivo ou compila regra, chamado dentro de um laço ou de cada requisição | [Uso #2](estruturais/flyweight/uso.md#objeto-caro-de-criar) |
| Uma grade ou uma lista enorme de itens que só variam por tipo | `[[Tile(...) for x in ...] for y in ...]`: um objeto por célula, com os mesmos campos de textura e de custo | [Uso #3](estruturais/flyweight/uso.md#grade-de-tiles) |

**Teste rápido.**

1. **Você mediu, e o problema é memória ou custo de criação?** Se não mediu, pare. O Flyweight troca clareza por economia, e economia hipotética não paga.
2. **Boa parte do estado é igual entre muitos objetos?** Compare o total com `len(set(...))` do campo. Se cada objeto é único, não há o que compartilhar.
3. **Esse estado pode ser imutável?** Se alguém precisa alterar o ícone de *um* marcador, o compartilhamento quebra: a alteração apareceria em todos.
4. **O que varia é fácil de passar como argumento?** Se cada método precisaria de oito argumentos de contexto, o custo em leitura pesa mais que a memória economizada.

Antes de aplicar: [Quando não usar](estruturais/flyweight/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/flyweight/explicacao.md#parecidos) · [Exemplos](estruturais/flyweight/uso.md).

### [Proxy](estruturais/proxy/explicacao.md) · uso: alta

Como pôr um representante no lugar de um objeto, para decidir se, quando ou onde o objeto de verdade é usado, sem que quem o usa perceba a troca.

**Regra.** O Proxy vale quando três coisas acontecem ao mesmo tempo: já existe (ou vai existir) um objeto real com uma interface estável, você precisa controlar **se, quando ou onde** ele é alcançado, e quem o usa **não deve precisar saber** disso.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um objeto caro criado antes de saber se será usado | Consulta, leitura de arquivo ou chamada de rede no `__init__`; N consultas para uma tela que usa uma | [Implementação, acima](estruturais/proxy/explicacao.md#implementacao) |
| A mesma checagem de permissão antes de cada chamada ao mesmo objeto | `if usuario.papel in (...)` repetido em controllers e relatórios; um deles esqueceu | [Uso #1](estruturais/proxy/uso.md#acesso-por-papel) |
| Um serviço foi para outro processo, e o código continua chamando como se fosse local | `requests.get(...)` com URL, *timeout* e parse copiados onde antes havia `estoque.disponivel(sku)` | [Uso #2](estruturais/proxy/uso.md#servico-extraido) |
| Observar o que acontece com um objeto sem mexer na classe dele | `copy.deepcopy` antes e comparação depois; `UPDATE` com todas as colunas | [Uso #3](estruturais/proxy/uso.md#mudancas-de-campos) |

**Teste rápido.**

1. **Você quer controlar *se, quando ou onde* o objeto real é alcançado?** Se o que você quer é acrescentar algo que roda em toda chamada (log, cache, métrica), é Decorator. Pare.
2. **A interface do proxy pode ser exatamente a do real?** Se o chamador precisaria de um método novo para usá-lo, é uma API nova, e o nome do que você quer é Facade ou Adapter.
3. **Há um motivo concreto?** Custo de criar medido, uma regra de acesso ou uma fronteira de processo. Sem isso, o proxy é só uma indireção.
4. **Quem usa o proxy só consegue chegar ao real por ele?** Se o real continua acessível por outro caminho, um proxy de proteção não protege nada.

Antes de aplicar: [Quando não usar](estruturais/proxy/explicacao.md#quando-nao-usar) · [Parecidos](estruturais/proxy/explicacao.md#parecidos) · [Exemplos](estruturais/proxy/uso.md).

<a id="comportamentais"></a>
## Comportamentais

### [Chain of Responsibility](comportamentais/chain-of-responsibility/explicacao.md) · uso: média

Como deixar um pedido percorrer uma sequência de candidatos até alguém tratá-lo, sem que quem pede precise saber quem são eles nem quantos existem.

**Regra.** O Chain of Responsibility vale quando três coisas acontecem ao mesmo tempo: **mais de um** objeto pode tratar o pedido, **qual deles trata** só se sabe na hora, e quem pede **não deve conhecer** os candidatos, ou a lista e a ordem deles mudam.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Uma escada decide quem trata o pedido | `if valor <= X` … `elif valor <= Y` …, ou a mesma escada copiada em dois lugares | [Uso #1](comportamentais/chain-of-responsibility/uso.md#alcada-por-valor) |
| As mesmas verificações no começo de cada handler | Autenticação, limite de requisições e validação repetidos no topo de toda rota, com pequenas diferenças | [Uso #2](comportamentais/chain-of-responsibility/uso.md#middleware) |
| O evento deve ser tratado por quem estiver mais perto | `closest()`, `parent`, ou um `if` global que testa de qual componente o evento veio | [Uso #3](comportamentais/chain-of-responsibility/uso.md#evento-que-sobe) |
| Fontes com custos diferentes, tentadas em ordem | `if x is None: x = outra_fonte()` aninhado, ou `try` dentro de `except` | [Uso #4](comportamentais/chain-of-responsibility/uso.md#fontes-em-camadas) |
| A ordem ou o conjunto de candidatos muda por ambiente | Flags como `if settings.USA_CACHE` espalhadas pelo caminho da chamada | [Uso #4](comportamentais/chain-of-responsibility/uso.md#fontes-em-camadas) |

**Teste rápido.**

1. **Mais de um objeto pode tratar o pedido?** Se só um pode, chame esse direto.
2. **Quem trata depende de algo que só se sabe na hora?** Se você sabe a chave de antemão (um tipo, um nome), escolha por ela com um dicionário.
3. **Os candidatos ou a ordem mudam, ou a escada aparece em mais de um lugar?** Se a lista é fixa, pequena e vive em um lugar só, um `if/elif` basta.
4. **Só o primeiro que pode deve tratar, ou qualquer um pode barrar?** Se sim, é Chain of Responsibility. Se todos devem receber o pedido, é Observer.

Antes de aplicar: [Quando não usar](comportamentais/chain-of-responsibility/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/chain-of-responsibility/explicacao.md#parecidos) · [Exemplos](comportamentais/chain-of-responsibility/uso.md).

### [Command](comportamentais/command/explicacao.md) · uso: alta

Como transformar um pedido de ação em um objeto, para poder guardá-lo, desfazê-lo, enfileirá-lo ou repeti-lo, em vez de apenas executá-lo na hora.

**Regra.** O Command vale quando três coisas acontecem ao mesmo tempo: o pedido precisa existir **separado** de quem o dispara e de quando ele roda; alguém precisa fazer **algo com o pedido** além de executá-lo (guardar, desfazer, enfileirar, repetir, mostrar o nome); e existem **várias ações** desse tipo, ou várias origens para a mesma.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Desfazer e refazer | Um campo como `_ultima_acao` e um `if tipo == …` dentro do `desfazer`; ou uma cópia da tela inteira a cada alteração | [Uso #1](comportamentais/command/uso.md#desfazer-refazer) |
| A ação precisa rodar depois, ou em outro processo | Um dicionário com `"tipo"` e `"dados"` despachado por `if`; ou uma `Thread` com meia dúzia de argumentos que se perde quando o servidor reinicia | [Uso #2](comportamentais/command/uso.md#fila-de-tarefas) |
| O histórico de "o que aconteceu" não pode ser reaplicado | Uma lista de textos de log que ninguém consegue transformar de volta na ação | [Uso #2](comportamentais/command/uso.md#fila-de-tarefas) |
| A mesma ação, vários gatilhos | `salvar(doc)` escrito no botão, no menu e no atalho; a regra de "desabilitado" repetida em cada um | [Uso #3](comportamentais/command/uso.md#varios-gatilhos) |
| Passos que valem por inteiro ou nada | Uma lista "o que já fiz" dentro de um `except`, para desfazer à mão na ordem inversa | [Uso #4](comportamentais/command/uso.md#lote-tudo-ou-nada) |

**Teste rápido.**

1. **Você só precisa chamar a ação agora?** Chame o método. Não há pedido a representar.
2. **Precisa fazer algo com a ação além de executá-la?** Desfazer, guardar, enfileirar, repetir, mostrar o nome. Se não, basta passar uma função.
3. **Há mais de uma ação, ou mais de uma origem para a mesma?** Se é uma ação só, com um gatilho só, um método resolve.
4. **O pedido consegue levar tudo de que precisa?** Se ele depende de estado global ou de um objeto vivo que não viaja, resolva isso primeiro; senão o comando guardado já nasce quebrado.

Antes de aplicar: [Quando não usar](comportamentais/command/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/command/explicacao.md#parecidos) · [Exemplos](comportamentais/command/uso.md).

### [Interpreter](comportamentais/interpreter/explicacao.md) · uso: rara

Como representar regras que mudam com frequência, ou que vêm de fora do código, como uma estrutura que se avalia sozinha, em vez de escrever uma função nova a cada variação.

**Regra.** O Interpreter vale quando três coisas acontecem ao mesmo tempo: as regras formam uma **família pequena** de peças que se combinam e se aninham; as combinações **vêm de fora do código** (de uma pessoa, de uma configuração, do banco) ou mudam mais rápido que os deploys; e a mesma regra precisa ser **avaliada, ou lida de outro jeito, muitas vezes**.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Cada variação da regra é uma função nova | `if campanha == "marco"` … `if campanha == "abril"` …, e o pull request é só para mudar um número | [Uso #1](comportamentais/interpreter/uso.md#regra-configuravel) |
| A regra é guardada como texto e avaliada na execução | `eval(regra)`, ou uma cadeia de `if` sobre um dicionário aninhado, lendo uma coluna de configuração | [Uso #1](comportamentais/interpreter/uso.md#regra-configuravel) |
| O usuário digita um filtro ou uma fórmula | `texto.split(" E ")` e `split("=")`; parênteses e `OU` "ainda não suportados" | [Uso #2](comportamentais/interpreter/uso.md#filtro-digitado) |
| A mesma regra existe em duas implementações | Uma função que filtra em memória e outra que monta um `WHERE`, escritas por pessoas diferentes | [Uso #3](comportamentais/interpreter/uso.md#varias-leituras) |
| A regra precisa ser mostrada em palavras | Uma função que monta o texto "Frete grátis para…" paralela à função que decide | [Uso #3](comportamentais/interpreter/uso.md#varias-leituras) |

**Teste rápido.**

1. **A regra muda mais rápido que o deploy, ou quem a muda não programa?** Se só programadores mudam e o deploy é aceitável, escreva uma função.
2. **Você consegue listar todas as formas que a regra pode tomar?** Se são poucas e fixas, um `enum` com um `if` resolve.
3. **As peças se aninham (um E dentro de um OU dentro de um NÃO)?** Se é só uma lista de condições juntas por E, uma lista de funções com `all()` basta.
4. **A linguagem cabe em meia dúzia de construções?** Se já pede variáveis, laços ou funções, você está construindo uma linguagem de programação. Use uma que já existe.

Antes de aplicar: [Quando não usar](comportamentais/interpreter/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/interpreter/explicacao.md#parecidos) · [Exemplos](comportamentais/interpreter/uso.md).

### [Iterator](comportamentais/iterator/explicacao.md) · uso: muito alta

Como percorrer uma coleção, ou uma fonte de dados, um elemento por vez, sem que quem percorre precise saber como ela guarda os elementos.

**Regra.** O Iterator vale quando três coisas acontecem ao mesmo tempo: existe uma coleção, ou uma fonte, com **estrutura própria**; **vários lugares** precisam percorrê-la; e eles **não devem depender** de como ela guarda os elementos, seja porque a forma pode mudar, seja porque ela é grande ou lenta demais para entregar de uma vez.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Cada chamador reimplementa o percurso | A mesma recursão, ou o mesmo `while pilha:`, copiada em várias funções, mudando só o que fazem com cada nó | [Uso #1](comportamentais/iterator/uso.md#varios-percursos) |
| O código de fora lê o campo interno | `cat.filhos`, `lista._itens` ou `resp["data"]` aparecendo fora da classe que os define | [Uso #1](comportamentais/iterator/uso.md#varios-percursos) |
| Mais de uma ordem de percurso | Funções chamadas `em_profundidade`, `em_largura`, `so_folhas`, cada uma com a própria lógica | [Uso #1](comportamentais/iterator/uso.md#varios-percursos) |
| Carrega tudo para usar só um pedaço | `readlines()` ou `list(...)` seguido de `[:10]`, `if` e `break` | [Uso #2](comportamentais/iterator/uso.md#fonte-grande) |
| Precisa parar e continuar depois | Um `offset` ou `posicao` passado à mão entre chamadas e salvo em algum lugar | [Uso #3](comportamentais/iterator/uso.md#retomar-de-onde-parou) |

**Teste rápido.**

1. **O que você percorre é uma lista, um dicionário ou um conjunto da linguagem?** Use o `for`: eles já são iteráveis.
2. **Mais de um lugar percorre isso?** Se só um, um laço local basta.
3. **Quem percorre precisa conhecer a estrutura, ou ela pode mudar?** Se a estrutura é pública e estável, deixe o laço ler direto.
4. **O percurso precisa ser sob demanda, ter mais de uma ordem ou ser retomado?** Se sim, é Iterator. Se é só "todos os elementos, de uma vez, em uma ordem", devolva uma lista.

Antes de aplicar: [Quando não usar](comportamentais/iterator/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/iterator/explicacao.md#parecidos) · [Exemplos](comportamentais/iterator/uso.md).

### [Mediator](comportamentais/mediator/explicacao.md) · uso: média

Como deixar um grupo de objetos trabalhar junto sem que cada um precise conhecer todos os outros, concentrando a conversa entre eles em um único lugar.

**Regra.** O Mediator vale quando três coisas acontecem ao mesmo tempo: um **grupo de objetos** precisa se coordenar; hoje cada um **guarda referências** aos outros, ou sabe o bastante sobre eles para reagir; e as regras da conversa **mudam**, ou os próprios objetos ficam **presos ao grupo** e não servem em outro lugar.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Objetos de interface que se mostram, preenchem e habilitam uns aos outros | `self.botao.habilitado = …` dentro de um campo; um `onChange` que mexe em três outros elementos | O exemplo desta página |
| Participantes que trocam mensagens entre si | Uma lista `outros` ou `contatos` em cada objeto; para sair, é preciso se remover de todos | [Uso #1](comportamentais/mediator/uso.md#sala-de-chat) |
| Serviços que chamam o próximo passo do fluxo | `self.envio.agendar(...)` no fim de outro serviço; imports circulares entre eles | [Uso #2](comportamentais/mediator/uso.md#orquestracao-de-pedido) |
| A regra depende do par de objetos que se encontram | `isinstance(outro, X)` dentro de cada classe, com a mesma regra escrita dos dois lados | [Uso #3](comportamentais/mediator/uso.md#regras-entre-pares) |
| Uma classe que não dá para usar sozinha | O construtor pede cinco outros objetos só para funcionar, e o teste monta o grupo inteiro | O exemplo desta página |

**Teste rápido.**

1. **São mais de dois objetos que se afetam?** Se são só dois, uma chamada direta ou um callback resolve.
2. **Eles guardam referências uns aos outros, ou sabem uns dos outros?** Se cada um age só sobre si, não há conversa a mediar.
3. **As regras ou os participantes mudam?** Se o grupo é fixo e pequeno, deixe-os se falando.
4. **A coordenação cabe em um lugar sem virar um monstro?** Se são dezenas de regras, uma só classe não é a resposta: divida por responsabilidade.

Antes de aplicar: [Quando não usar](comportamentais/mediator/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/mediator/explicacao.md#parecidos) · [Exemplos](comportamentais/mediator/uso.md).

### [Memento](comportamentais/memento/explicacao.md) · uso: baixa

Como guardar o estado de um objeto para voltar a ele depois, sem deixar quem guarda saber o que tem dentro nem mexer nisso.

**Regra.** O Memento vale quando três coisas acontecem ao mesmo tempo: alguém precisa **voltar** a um estado em que o objeto já esteve; o estado é **interno** do objeto, então quem guarda não deveria conhecê-lo; e guardar a foto inteira é **mais simples** do que escrever o inverso de cada operação.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Desfazer e refazer em um objeto com muito estado | Um `_anterior = {…}` na tela, copiando campo a campo; um `desfazer` que reatribui cada campo; um campo novo que ninguém lembrou de copiar | [Uso #1](comportamentais/memento/uso.md#historico-do-editor) |
| Calcular "e se…" sem alterar de verdade | Um `simular_x()` que repete as regras de `aplicar_x()`; `deepcopy(obj)` espalhado antes de "tentar" | [Uso #2](comportamentais/memento/uso.md#simular-e-decidir) |
| Retomar depois de fechar a tela ou o programa | Uma série de `localStorage.setItem` com um campo por chave; `json.dumps(obj.__dict__)` com os campos listados à mão | [Uso #3](comportamentais/memento/uso.md#rascunho-que-sobrevive) |
| Tentar um caminho e voltar se não der | `pos_salva = self.pos` … `self.pos = pos_salva`, repetido em cada alternativa, e cada vez com um campo a mais | [Uso #4](comportamentais/memento/uso.md#tentar-e-voltar) |
| Código de fora que restaura mexendo no que é privado | `obj._campo = valor` fora da classe; `setattr` em laço sobre o `__dict__` | [Uso #1](comportamentais/memento/uso.md#historico-do-editor) |

**Teste rápido.**

1. **Alguém vai mesmo voltar a esse estado?** Se o que se quer é saber o que aconteceu (auditoria, quem mudou o quê), registre o evento, não o estado.
2. **O estado é um valor pequeno e imutável?** Se o objeto inteiro é uma tupla, um número ou um `dataclass(frozen=True)`, a referência antiga já é a foto. Guarde-a.
3. **O inverso de cada operação é curto e simples de escrever?** Se são três ações e cada uma tem uma volta óbvia, um Command com `desfazer` custa menos que manter fotos.
4. **Quem guarda precisaria conhecer ou editar os campos?** Se sim, é Memento: a foto sai do objeto fechada e volta fechada.

Antes de aplicar: [Quando não usar](comportamentais/memento/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/memento/explicacao.md#parecidos) · [Exemplos](comportamentais/memento/uso.md).

### [Observer](comportamentais/observer/explicacao.md) · uso: muito alta

Como avisar várias partes do sistema de que algo aconteceu, sem que quem avisa precise saber quem são elas, nem quantas.

**Regra.** O Observer vale quando três coisas acontecem ao mesmo tempo: **mais de uma parte** precisa reagir ao mesmo fato; quem o produz **não deveria saber** quem são elas (porque a lista cresce, muda em execução ou pertence a outros); e a reação é uma **consequência**, não parte do trabalho: o assunto está completo mesmo que ninguém ouça.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um fato dispara várias reações independentes | Um método que termina com quatro chamadas a módulos diferentes; um `import` para cada reação nova | [Uso #1](comportamentais/observer/uso.md#varios-interessados) |
| A tela precisa acompanhar o modelo | `atualizarHeader(); atualizarMiniCarrinho();` depois de cada alteração, ou um `setInterval` que pergunta "mudou?" | [Uso #2](comportamentais/observer/uso.md#tela-acompanha-modelo) |
| Quem escuta entra e sai durante a execução | Uma lista com `append` e sem `remove`; widget fechado que continua recebendo dados | [Uso #3](comportamentais/observer/uso.md#entram-e-saem) |
| Código de outros precisa reagir a algo seu | `if config.plugin_x_ativo:` dentro do núcleo; PR em seu repositório para cada extensão | [Uso #4](comportamentais/observer/uso.md#plugins) |
| Código reutilizável precisa reportar o que está fazendo | Parâmetros `barra=None, logger=None, modo_cli=False` em uma função de biblioteca; `print` no meio da regra | [Uso #5](comportamentais/observer/uso.md#progresso) |

**Teste rápido.**

1. **Só uma parte reage, e sempre a mesma?** Receba-a no construtor e chame o método. Uma lista de um item é cerimônia.
2. **A reação é parte da operação?** Se sem ela o pedido não está realmente pago (a baixa de estoque na mesma transação, por exemplo), não é um aviso: é um passo. Chame direto, onde a transação enxerga.
3. **Quem dispara precisa da resposta?** Aprovar, vetar, devolver um valor. O Observer não espera retorno; use uma chamada direta ou uma [Chain of Responsibility](comportamentais/chain-of-responsibility/explicacao.md).
4. **A lista cresce, muda em execução ou é de outros?** Se sim, é Observer. Se é uma lista que você controla e vai mudar uma vez por ano, ainda dá para esperar.

Antes de aplicar: [Quando não usar](comportamentais/observer/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/observer/explicacao.md#parecidos) · [Exemplos](comportamentais/observer/uso.md).

### [State](comportamentais/state/explicacao.md) · uso: média

Como fazer um objeto que se comporta de um jeito em cada fase da vida dele sem encher todos os métodos de `if` sobre em qual fase ele está.

**Regra.** O State vale quando três coisas acontecem ao mesmo tempo: o comportamento do objeto **depende de uma fase** que muda ao longo da vida dele; há **várias fases**, cada uma com comportamento próprio; e a pergunta "em que fase estou?" aparece em **mais de um método**.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| A mesma escada de `if` sobre a fase em vários métodos | `if self.status == …` / `elif` repetido no começo de cada operação, como o `pagar` e o `cancelar` acima | O exemplo desta página |
| O mesmo gesto faz coisas diferentes conforme o modo | `switch (ferramenta)` dentro de cada um dos handlers de mouse ou de teclado | [Uso #1](comportamentais/state/uso.md#ferramenta-ativa) |
| Flags booleanas que juntas descrevem a fase | `self.aberto`, `self.meio_aberto` e `self.falhas`, em que algumas combinações não deveriam existir | [Uso #2](comportamentais/state/uso.md#disjuntor) |
| Algo precisa acontecer toda vez que se entra ou se sai de uma fase | Um `timer.cancel()` ou uma limpeza copiada em cada método que muda `status`, e esquecida em um | [Uso #3](comportamentais/state/uso.md#reserva-com-prazo) |
| As transições não estão escritas em lugar nenhum | Para descobrir de onde se chega a `cancelado`, é preciso ler todos os métodos | O exemplo desta página |

**Teste rápido.**

1. **O objeto muda de comportamento ao longo da vida?** Se ele se comporta sempre do mesmo jeito, não há fase para modelar.
2. **Há mais de duas ou três fases?** Com duas, um booleano e um `if` resolvem, e as classes não se pagam.
3. **A diferença aparece em mais de uma operação, ou há algo a fazer ao entrar e sair?** Se só uma decisão depende da fase, um `if` naquele ponto basta.
4. **Cada fase tem um *comportamento* próprio, e não só "pode" ou "não pode"?** Se a fase só decide quais transições valem, uma tabela de transições é mais curta. O State vale quando há o que fazer.

Antes de aplicar: [Quando não usar](comportamentais/state/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/state/explicacao.md#parecidos) · [Exemplos](comportamentais/state/uso.md).

### [Strategy](comportamentais/strategy/explicacao.md) · uso: muito alta

Como trocar o jeito de fazer uma coisa sem mexer em quem a pede, e sem um `if` novo a cada jeito que aparece.

**Regra.** O Strategy vale quando três coisas acontecem ao mesmo tempo: existe **mais de um jeito** de fazer a mesma coisa, com a mesma entrada e o mesmo tipo de saída; a escolha de qual jeito usar **vem de fora** (usuário, configuração, contexto), e não do tipo do objeto; e quem usa o resultado **não deve saber** qual jeito foi usado.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Um texto ou enum escolhe o algoritmo | `if ordem == "preco"` … `elif ordem == "nota"` …, e cada opção nova da tela é um `elif` | [Uso #1](comportamentais/strategy/uso.md#ordenacao-escolhida) |
| O mesmo resultado, com custos diferentes | `if len(dados) > LIMITE` trocando de implementação dentro da função, ou um booleano como `tempo_real=True` | [Uso #2](comportamentais/strategy/uso.md#custo-diferente) |
| Um laço com uma política dentro | `time.sleep(2 ** tentativa)` e `range(8)` escritos no meio do laço, copiados com números diferentes | [Uso #3](comportamentais/strategy/uso.md#politica-de-retentativa) |
| Teste que dorme, sorteia ou depende do relógio | `time.sleep`, `random` ou `datetime.now()` chamados direto dentro da regra; o teste demora ou falha de vez em quando | [Uso #3](comportamentais/strategy/uso.md#politica-de-retentativa) |
| Regra que muda por cliente e hoje exige deploy | `if cliente.id == 42`, ou um `dict` de parâmetros lido por dentro da regra | [Uso #4](comportamentais/strategy/uso.md#regra-do-cadastro) |
| Uma função cheia de parâmetros de "modo" | `calcular(venda, com_bonus=True, arredondar=False, tabela="2024")` | — |

**Teste rápido.**

1. **Existe mais de um jeito de verdade?** Se há um só hoje e nenhum à vista, escreva a função direto.
2. **Os jeitos recebem as mesmas entradas e devolvem o mesmo tipo de resultado?** Se não, não são intercambiáveis. Provavelmente são coisas diferentes com o mesmo verbo.
3. **A escolha é fixa por tipo, para sempre?** Se um `Boleto` sempre calcula de um jeito e um `Cartao` de outro, é polimorfismo comum: um método em cada classe.
4. **A escolha vem de fora e pode mudar sem mexer na classe?** Usuário, configuração, tamanho dos dados. Se sim, é Strategy.

Antes de aplicar: [Quando não usar](comportamentais/strategy/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/strategy/explicacao.md#parecidos) · [Exemplos](comportamentais/strategy/uso.md).

### [Template Method](comportamentais/template-method/explicacao.md) · uso: alta

Como escrever uma vez só a ordem dos passos de um processo, e deixar cada variação preencher apenas o passo que é diferente dela.

**Regra.** O Template Method vale quando três coisas acontecem ao mesmo tempo: existem **duas ou mais variantes** do mesmo processo; a **ordem** dos passos é a mesma em todas; e o que muda cabe em **poucos passos** bem nomeados, enquanto o resto é igual.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| Funções quase iguais, com um miolo diferente | Duas funções com 80% das linhas iguais; uma correção feita em uma delas e esquecida na outra | [Uso #1](comportamentais/template-method/uso.md#mesmo-roteiro) |
| Um passo que nenhuma variante pode pular | `verificar_assinatura()` repetido em cada handler (e faltando em um); um `try/finally` copiado | [Uso #2](comportamentais/template-method/uso.md#passo-obrigatorio) |
| A política do processo varia pouco, de forma pontual | `if self.ativo:`, parâmetros `antes=None, depois=None` ou comentários "este job pula fim de semana" | [Uso #3](comportamentais/template-method/uso.md#ganchos-opcionais) |
| O mesmo roteiro com um tipo novo à vista | Um `if tipo == …` em cada passo do mesmo processo | [Uso #1](comportamentais/template-method/uso.md#mesmo-roteiro) |

**Teste rápido.**

1. **Existe mais de uma variante do processo?** Se só há uma, escreva uma função. Ainda não há o que separar.
2. **A ordem dos passos é a mesma em todas?** Se a ordem muda de uma variante para outra, o esqueleto não é fixo: escreva cada fluxo, ou componha os passos de fora.
3. **O que varia cabe em um ou três passos?** Se quase tudo muda, sobra um esqueleto fino demais para valer uma classe base.
4. **Dá para passar o passo como função?** Se o que varia é uma ação sem estado, passe uma função como parâmetro. Herança só se paga quando as variantes têm vários passos e dados próprios.

Antes de aplicar: [Quando não usar](comportamentais/template-method/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/template-method/explicacao.md#parecidos) · [Exemplos](comportamentais/template-method/uso.md).

### [Visitor](comportamentais/visitor/explicacao.md) · uso: baixa

Como acrescentar operações novas a uma estrutura de objetos de tipos diferentes, sem abrir cada classe e sem repetir uma escada de `isinstance` em cada operação.

**Regra.** O Visitor vale quando três coisas acontecem ao mesmo tempo: existe uma estrutura de objetos de **tipos diferentes**, em geral uma árvore; as **operações** sobre ela são várias e crescem, ou não pertencem aos objetos; e o conjunto de **tipos muda pouco**. A terceira condição é a que mais se esquece.

| Situação | Como reconhecer no código | Exemplo |
|---|---|---|
| A mesma escada de tipos em cada operação | `if isinstance(item, Livro)` … `if isinstance(item, Kit)` repetido em `calcular_imposto`, `peso_para_frete` e na próxima | O exemplo desta página |
| Classes de domínio com métodos que não são do domínio | `para_pdf()`, `para_csv()` e `validar_fiscal()` no mesmo objeto que representa um livro | O exemplo desta página |
| A operação precisa de antes e depois, ou de estado acumulado | Contadores e níveis passados como argumento extra por uma recursão, `acc=None`, `nivel=0` | [Uso #1](comportamentais/visitor/uso.md#relatorio-de-arquivos) |
| A estrutura é de uma biblioteca, e você não pode mudá-la | Uma análise sobre nós de AST, de XML ou do DOM, em que não há onde pôr um método novo | [Uso #2](comportamentais/visitor/uso.md#ast-nodevisitor) |
| Uma transformação reescreve a árvore | Uma função recursiva que reconstrói cada nó com os filhos já transformados, e se repete para cada regra de reescrita | [Uso #3](comportamentais/visitor/uso.md#simplificar-regras) |

**Teste rápido.**

1. **A estrutura tem tipos diferentes?** Se todos os elementos são do mesmo tipo, um `for` resolve.
2. **Há mais de uma operação, ou ela está crescendo?** Se é uma só, um método polimórfico na própria classe é o mais simples.
3. **O conjunto de tipos é estável?** Se tipos novos aparecem toda hora, cada um obriga a mudar todos os visitantes. Use polimorfismo comum.
4. **A operação pertence ao domínio, e você controla as classes?** Se sim, ela é um método do elemento. O Visitor vale quando a operação não pertence às classes, ou quando as classes não são suas.

Antes de aplicar: [Quando não usar](comportamentais/visitor/explicacao.md#quando-nao-usar) · [Parecidos](comportamentais/visitor/explicacao.md#parecidos) · [Exemplos](comportamentais/visitor/uso.md).

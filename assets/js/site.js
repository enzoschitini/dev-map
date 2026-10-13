/*
 * DevMap — o mapa do site. Fonte única da estrutura.
 *
 * O shell.js lê este arquivo e monta as abas, o menu lateral, a busca e os
 * links de anterior/próxima. Nenhuma página tem navegação escrita à mão.
 *
 * Uma aba
 *   id       a pasta em pages/ — só minúsculas, números e hífen
 *   label    o texto da aba no cabeçalho
 *   icon     o ícone do cartão na página inicial (window.DS.icons lista todos)
 *   summary  uma linha, usada no cartão
 *   pages    os nós da aba, na ordem em que aparecem no menu
 *
 * Dentro de `pages` cabem três tipos de nó:
 *
 *   página   { id: 'overview', label: 'Overview', summary: '...' }
 *            vira o arquivo <id>.html dentro da pasta onde o nó está
 *
 *   sessão   { group: 'SOLID', pages: [ ... ] }
 *            só um título no menu lateral — NÃO vira pasta no disco
 *
 *   pasta    { folder: 'adapter', label: 'Adapter', pages: [ ... ] }
 *            pasta de verdade: o que está dentro mora em adapter/
 *            pastas podem ficar dentro de pastas (estruturais/adapter/)
 *            começa fechada, e abre sozinha quando guarda a página aberta
 *            `open: true` faz ela já começar aberta
 *
 * Opcional em uma página
 *   empty    marca com o selo "vazio" enquanto ela não tem conteúdo
 *
 * Para criar uma página
 *   1. adicione o nó aqui, no lugar certo da árvore
 *   2. copie pages/_template.html para o caminho correspondente
 *   3. no <body>, ajuste data-root, data-tab e data-page
 *      data-page é o caminho dentro da aba, sem .html — ex.: estruturais/adapter/explicacao
 */
window.DEVMAP = {
  name: 'DevMap',
  sub: 'Estudos',
  tagline: 'Meus estudos de programação, documentados em um só lugar.',

  tabs: [
    {
      id: 'clean-code',
      label: 'Clean Code',
      icon: 'code',
      summary: 'Princípios e padrões para escrever código que outra pessoa entende.',
      pages: [
        {
          id: 'overview',
          label: 'Overview',
          summary: 'O que entra nesta aba, como ela está dividida e o formato das páginas.'
        },
        {
          group: 'SOLID',
          pages: [
            {
              id: 'introducao',
              label: 'Introdução',
              summary: 'Os cinco princípios, o que cada um resolve e por onde começar.'
            },
            {
              id: 'single-responsibility',
              label: 'Single Responsibility',
              summary: 'Como dar a cada motivo de mudança a sua própria classe, para uma mudança não arrastar as outras.'
            },
            {
              id: 'open-closed',
              label: 'Open/Closed',
              summary: 'Como acrescentar um caso novo escrevendo código novo, sem reabrir o que já funcionava.'
            },
            {
              id: 'liskov-substitution',
              label: 'Liskov Substitution',
              summary: 'Como garantir que a subclasse entra no lugar da base sem que quem chama precise perguntar o tipo.'
            },
            {
              id: 'interface-segregation',
              label: 'Interface Segregation',
              summary: 'Como evitar interfaces largas que obrigam a implementar, e a conhecer, o que não se usa.'
            },
            {
              id: 'dependency-inversion',
              label: 'Dependency Inversion',
              summary: 'Como fazer a regra de negócio mandar na infraestrutura, e não o contrário.'
            }
          ]
        },
        {
          group: 'Design Pattern',
          pages: [
            {
              id: 'patterns-introducao',
              label: 'Introdução',
              summary: 'O que são os padrões, o que cada grupo resolve e a tabela com os 23 patterns.'
            },
            {
              id: 'patterns-frequencia',
              label: 'Frequência de uso',
              summary: 'Quais padrões aparecem mais no dia a dia e por onde começar a estudar.'
            },
            {
              folder: 'criacionais',
              label: 'Criacionais',
              pages: [
                {
                  folder: 'singleton',
                  label: 'Singleton',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como garantir que um objeto existe uma vez só e que todo mundo chega nele.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Cinco situações reais, com o código antes e depois do Singleton.'
                    }
                  ]
                },
                {
                  folder: 'factory-method',
                  label: 'Factory Method',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como criar um objeto sem saber a classe exata, entregando a escolha às subclasses.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Quatro situações reais, com o código antes e depois do Factory Method.'
                    }
                  ]
                },
                {
                  folder: 'abstract-factory',
                  label: 'Abstract Factory',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como criar um conjunto de objetos que combinam entre si, sem misturar peças de famílias diferentes.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois da Abstract Factory.'
                    }
                  ]
                },
                {
                  folder: 'builder',
                  label: 'Builder',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como montar um objeto complexo por partes e só entregá-lo quando estiver completo e válido.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Builder.'
                    }
                  ]
                },
                {
                  folder: 'prototype',
                  label: 'Prototype',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como criar um objeto copiando outro que já existe, sem conhecer a classe nem os campos.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Prototype.'
                    }
                  ]
                }
              ]
            },
            {
              folder: 'estruturais',
              label: 'Estruturais',
              pages: [
                {
                  folder: 'adapter',
                  label: 'Adapter',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como encaixar uma interface que você não controla na que o seu código espera.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Sete situações reais, com o código antes e depois do Adapter.'
                    }
                  ]
                },
                {
                  folder: 'bridge',
                  label: 'Bridge',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como deixar duas coisas que variam por motivos diferentes crescerem separadas, sem uma subclasse para cada combinação.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Bridge.'
                    }
                  ]
                },
                {
                  folder: 'composite',
                  label: 'Composite',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como tratar um item e um grupo de itens do mesmo jeito, em qualquer profundidade.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Quatro situações reais, com o código antes e depois do Composite.'
                    }
                  ]
                },
                {
                  folder: 'decorator',
                  label: 'Decorator',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como acrescentar comportamento a um objeto sem mexer nele e sem uma subclasse para cada combinação.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Decorator.'
                    }
                  ]
                },
                {
                  folder: 'facade',
                  label: 'Facade',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como dar uma porta de entrada simples para um conjunto de peças que só funcionam na ordem certa.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Facade.'
                    }
                  ]
                },
                {
                  folder: 'flyweight',
                  label: 'Flyweight',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como manter centenas de milhares de objetos sem repetir em cada um o que é igual para todos do mesmo tipo.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Flyweight.'
                    }
                  ]
                },
                {
                  folder: 'proxy',
                  label: 'Proxy',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como pôr um representante no lugar de um objeto, para controlar se, quando ou onde o real é usado.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Proxy.'
                    }
                  ]
                }
              ]
            },
            {
              folder: 'comportamentais',
              label: 'Comportamentais',
              pages: [
                {
                  folder: 'chain-of-responsibility',
                  label: 'Chain of Responsibility',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como passar um pedido por uma sequência de tratadores, sem quem pede saber qual deles responde.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Quatro situações reais, com o código antes e depois do Chain of Responsibility.'
                    }
                  ]
                },
                {
                  folder: 'command',
                  label: 'Command',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como transformar um pedido de ação em um objeto, para guardar, desfazer, enfileirar ou repetir.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Quatro situações reais, com o código antes e depois do Command.'
                    }
                  ]
                },
                {
                  folder: 'interpreter',
                  label: 'Interpreter',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como representar regras que mudam como uma árvore de objetos que se avalia sozinha.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Interpreter.'
                    }
                  ]
                },
                {
                  folder: 'iterator',
                  label: 'Iterator',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como percorrer uma coleção, ou uma fonte de dados, sem depender de como ela guarda os elementos.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Iterator.'
                    }
                  ]
                },
                {
                  folder: 'mediator',
                  label: 'Mediator',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como deixar um grupo de objetos trabalhar junto sem que cada um conheça todos os outros.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Mediator.'
                    }
                  ]
                },
                {
                  folder: 'memento',
                  label: 'Memento',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como guardar o estado de um objeto para voltar a ele depois, sem expor o que tem dentro.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Quatro situações reais, com o código antes e depois do Memento.'
                    }
                  ]
                },
                {
                  folder: 'observer',
                  label: 'Observer',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como avisar várias partes do sistema de que algo aconteceu, sem quem avisa saber quem são elas.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Cinco situações reais, com o código antes e depois do Observer.'
                    }
                  ]
                },
                {
                  folder: 'state',
                  label: 'State',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como fazer um objeto se comportar de um jeito em cada fase da vida, sem um if sobre a fase em cada método.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do State.'
                    }
                  ]
                },
                {
                  folder: 'strategy',
                  label: 'Strategy',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como trocar o jeito de fazer uma coisa sem mexer em quem a pede, e sem um if novo a cada jeito.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Quatro situações reais, com o código antes e depois do Strategy.'
                    }
                  ]
                },
                {
                  folder: 'template-method',
                  label: 'Template Method',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como escrever uma vez a ordem dos passos de um processo, deixando cada variação preencher só o passo que é diferente.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Template Method.'
                    }
                  ]
                },
                {
                  folder: 'visitor',
                  label: 'Visitor',
                  pages: [
                    {
                      id: 'explicacao',
                      label: 'Explicação',
                      summary: 'Como acrescentar operações a uma estrutura de objetos de tipos diferentes sem abrir cada classe.'
                    },
                    {
                      id: 'uso',
                      label: 'Uso',
                      summary: 'Três situações reais, com o código antes e depois do Visitor.'
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
};

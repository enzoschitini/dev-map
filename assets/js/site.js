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
            }
          ]
        },
        {
          group: 'Design Pattern',
          pages: [
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

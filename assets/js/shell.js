/*
 * DevMap — monta a moldura de toda página a partir do window.DEVMAP.
 *
 * Carregue sempre nesta ordem, no fim do <body>:
 *   site.js    o mapa do site
 *   shell.js   este arquivo
 *   ds.js      comportamento dos componentes do design system
 *
 * A página só escreve o seu conteúdo. Tudo abaixo vem daqui, pelos
 * marcadores data-shell:
 *   [data-shell="header"]   marca, busca, tema, abas e barra do celular
 *   [data-shell="side"]     menu lateral da aba atual (no início, o mapa todo)
 *   [data-shell="pager"]    links de anterior e próxima
 *   [data-shell="footer"]   rodapé
 *   [data-shell="areas"]    grade de cartões das abas (só na página inicial)
 *   [data-shell="search"]   diálogo de busca (o ds.js abre e fecha)
 *
 * De onde ele sabe onde está: os atributos do <body>.
 *   data-root   prefixo até a raiz ("" no index, "../../" nas páginas)
 *   data-tab    id da aba atual, vazio na página inicial
 *   data-page   id da página atual
 */
(function () {
  'use strict';

  var MAP = window.DEVMAP || { name: 'DevMap', tabs: [] };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  };

  var D = document.body.dataset;
  var ROOT = D.root || '';
  var TAB = D.tab || '';
  var PAGE = D.page || '';

  var home = ROOT + 'index.html';
  var href = function (tab, path) { return ROOT + 'pages/' + tab.id + '/' + path + '.html'; };

  /* ---------- a árvore, achatada ----------
     Percorre os nós na ordem do menu e devolve só as páginas, cada uma com
     o caminho no disco (dir) e o rastro de sessões e pastas até ela (trail). */
  function walk(nodes, tab, dir, trail, out) {
    (nodes || []).forEach(function (n) {
      if (n.group) { walk(n.pages, tab, dir, trail.concat(n.group), out); return; }
      if (n.folder) { walk(n.pages, tab, dir.concat(n.folder), trail.concat(n.label || n.folder), out); return; }
      var path = dir.concat(n.id).join('/');
      out.push({ tab: tab, page: n, path: path, trail: trail, u: href(tab, path) });
    });
    return out;
  }

  var here = null;
  var flat = [];
  MAP.tabs.forEach(function (t) {
    if (t.id === TAB) here = t;
    walk(t.pages, t, [], [], flat);
  });
  var at = -1;
  flat.forEach(function (r, i) { if (r.tab.id === TAB && r.path === PAGE) at = i; });

  /* a primeira página de uma aba — para onde a aba e o cartão apontam */
  function first(tab) {
    return flat.filter(function (r) { return r.tab.id === tab.id; })[0] || null;
  }
  /* "Clean Code / Design Pattern / Adapter" */
  function where(r) { return [r.tab.label].concat(r.trail).join(' / '); }

  var fill = function (name, html) {
    var el = $('[data-shell="' + name + '"]');
    if (el) el.innerHTML = html;
    return el;
  };

  /* ---------- cabeçalho ---------- */
  function header() {
    var tabs = MAP.tabs.map(function (t) {
      var f = first(t);
      if (!f) return '';
      return '<a class="tab" href="' + f.u + '"' +
        (t.id === TAB ? ' aria-current="page"' : '') + '>' + esc(t.label) + '</a>';
    }).join('');

    var trail = at >= 0
      ? esc(where(flat[at]) + ' / ' + flat[at].page.label)
      : (here ? esc(here.label) : 'Início');

    fill('header',
      '<div class="bar">' +
        '<div class="row1">' +
          '<a class="brand" href="' + home + '">' +
            '<span class="brand-mark"></span>' +
            '<span class="brand-name">' + esc(MAP.name) + '</span>' +
            (MAP.sub ? '<span class="brand-sub">' + esc(MAP.sub) + '</span>' : '') +
          '</a>' +
          '<button class="search-trigger" type="button" data-open-search aria-label="Buscar no ' + esc(MAP.name) + '">' +
            '<i data-ico="search"></i><span>Buscar...</span><kbd>Ctrl K</kbd>' +
          '</button>' +
          '<div class="actions">' +
            '<button class="icon-btn" type="button" data-theme-toggle></button>' +
          '</div>' +
        '</div>' +
        '<nav class="tabs-row" aria-label="Áreas do ' + esc(MAP.name) + '">' +
          '<a class="tab" href="' + home + '"' + (TAB ? '' : ' aria-current="page"') + '>Início</a>' +
          tabs +
        '</nav>' +
        '<div class="subbar">' +
          '<button type="button" data-menu-toggle aria-controls="side" aria-expanded="false">' +
            '<i data-ico="menu"></i><span>Menu</span>' +
          '</button>' +
          '<i data-ico="chevron"></i>' +
          '<span class="here">' + trail + '</span>' +
        '</div>' +
      '</div>' +
      '<div class="header-line"></div>');
  }

  /* ---------- menu lateral ---------- */
  /* um nó vira um <li>: a página, ou a pasta com o que há dentro dela */
  function item(n, tab, dir) {
    if (n.folder) {
      var inside = dir.concat(n.folder);
      /* pasta começa fechada; abre sozinha quando guarda a página atual */
      var mine = tab.id === TAB && PAGE.indexOf(inside.join('/') + '/') === 0;
      var open = mine || n.open === true;
      return '<li>' +
        '<button class="side-link side-folder" type="button" aria-expanded="' + open + '">' +
          '<span>' + esc(n.label || n.folder) + '</span><i class="chev" data-ico="chevron"></i>' +
        '</button>' +
        '<ul class="side-sub"' + (open ? '' : ' hidden') + '>' +
          (n.pages || []).map(function (c) { return item(c, tab, inside); }).join('') +
        '</ul></li>';
    }
    var path = dir.concat(n.id).join('/');
    return '<li><a class="side-link" href="' + href(tab, path) + '"' +
      (tab.id === TAB && path === PAGE ? ' aria-current="page"' : '') + '>' +
      '<span>' + esc(n.label) + '</span>' +
      (n.empty ? '<span class="badge">vazio</span>' : '') + '</a></li>';
  }

  /* os nós de um nível, na ordem do mapa: páginas soltas viram uma lista,
     cada sessão vira um bloco com título */
  function nav(nodes, tab, dir) {
    var out = '', buf = [];
    var flush = function () { if (buf.length) { out += '<ul>' + buf.join('') + '</ul>'; buf = []; } };
    (nodes || []).forEach(function (n) {
      if (!n.group) { buf.push(item(n, tab, dir)); return; }
      flush();
      out += '<div class="side-group"><p class="side-title">' + esc(n.group) + '</p>' +
        nav(n.pages, tab, dir) + '</div>';
    });
    flush();
    return out;
  }

  function side() {
    /* no celular, as abas entram na gaveta (ver responsive.css) */
    var areas = '<div class="side-areas">' +
      '<a href="' + home + '"' + (TAB ? '' : ' aria-current="page"') + '>Início</a>' +
      MAP.tabs.map(function (t) {
        var f = first(t);
        return f
          ? '<a href="' + f.u + '"' + (t.id === TAB ? ' aria-current="page"' : '') + '>' + esc(t.label) + '</a>'
          : '';
      }).join('') +
      '</div>';

    /* dentro de uma aba, o menu mostra só ela; no início, o mapa inteiro */
    var tree = here
      ? nav(here.pages, here, [])
      : MAP.tabs.map(function (t) {
          return '<div class="side-group"><p class="side-title">' + esc(t.label) + '</p>' +
            nav(t.pages, t, []) + '</div>';
        }).join('');

    fill('side', areas + '<nav class="side">' + tree + '</nav>');
  }

  /* ---------- anterior e próxima ---------- */
  function pager() {
    var box = $('[data-shell="pager"]');
    if (!box) return;
    if (at < 0) { box.remove(); return; }

    /* o contexto mais próximo: a pasta ou a sessão, e só a aba na raiz */
    var near = function (r) { return (r.trail[r.trail.length - 1] || r.tab.label) + ' / ' + r.page.label; };
    var prev = flat[at - 1], next = flat[at + 1], out = '';
    if (prev) {
      out += '<a class="pager-link prev" href="' + prev.u + '"><i data-ico="chevron"></i>' +
        '<div><small>Anterior</small><span>' +
        esc(near(prev)) + '</span></div></a>';
    }
    if (next) {
      out += '<a class="pager-link next" href="' + next.u + '">' +
        '<div><small>Próxima</small><span>' +
        esc(near(next)) + '</span></div>' +
        '<i data-ico="chevron"></i></a>';
    }
    if (!out) { box.remove(); return; }
    box.innerHTML = out;
  }

  /* ---------- rodapé ---------- */
  function footer() {
    var areas = MAP.tabs.map(function (t) {
      var f = first(t);
      return f ? '<a href="' + f.u + '">' + esc(t.label) + '</a>' : '';
    }).join('');

    fill('footer',
      '<div class="foot-grid">' +
        '<div class="foot-brand">' +
          '<a class="brand" href="' + home + '">' +
            '<span class="brand-mark"></span>' +
            '<span class="brand-name">' + esc(MAP.name) + '</span>' +
            (MAP.sub ? '<span class="brand-sub">' + esc(MAP.sub) + '</span>' : '') +
          '</a>' +
          '<p>' + esc(MAP.tagline || '') + '</p>' +
        '</div>' +
        '<div class="foot-col"><h2>Áreas</h2>' + areas + '</div>' +
        '<div class="foot-col"><h2>Este site</h2>' +
          '<a href="' + ROOT + '_design-system/index.html">Design System</a>' +
        '</div>' +
      '</div>' +
      '<div class="foot-bottom">' +
        '<span>' + esc(MAP.name) + ' · ' + new Date().getFullYear() + '</span>' +
        '<span>Feito para estudar.</span>' +
      '</div>');
  }

  /* ---------- grade de áreas da página inicial ---------- */
  function areas() {
    var box = $('[data-shell="areas"]');
    if (!box) return;
    var list = MAP.tabs.filter(function (t) { return first(t); });
    /* uma área sozinha fica melhor no cartão em linha; duas ou mais, na grade */
    var solo = list.length === 1;
    box.className = 'cards' + (solo ? ' one' : '');
    box.innerHTML = list.map(function (t) {
      var u = first(t).u;
      var icon = '<span class="card-icon" data-ico="' + esc(t.icon || 'folder') + '"></span>';
      var text = '<span class="card-title">' + esc(t.label) + '</span>' +
        '<span class="card-text">' + esc(t.summary || '') + '</span>';
      return solo
        ? '<a class="card row" href="' + u + '">' + icon + '<span>' + text + '</span>' +
          '<i class="card-go" data-ico="go"></i></a>'
        : '<a class="card" href="' + u + '">' + icon + text + '</a>';
    }).join('');
  }

  /* ---------- índice recolhido do celular ---------- */
  function tocInline() {
    var prose = $('.prose');
    if (!prose || $('.toc-inline')) return;
    prose.insertAdjacentHTML('beforebegin',
      '<details class="toc-inline"><summary>Nesta página</summary><ul></ul></details>');
  }

  /* ---------- busca ---------- */
  function search() {
    var dlg = $('[data-shell="search"]');
    if (!dlg) return;

    dlg.innerHTML =
      '<div class="search-field">' +
        '<i data-ico="search"></i>' +
        '<input type="search" placeholder="Buscar páginas" autocomplete="off" spellcheck="false">' +
        '<kbd>Esc</kbd>' +
      '</div>' +
      '<ul class="results" role="listbox" aria-label="Resultados"></ul>' +
      '<div class="search-foot">' +
        '<span><kbd>↑</kbd><kbd>↓</kbd><span>navegar</span></span>' +
        '<span><kbd>Enter</kbd><span>abrir</span></span>' +
      '</div>';

    var input = $('input', dlg), list = $('.results', dlg), rows = [], sel = -1;

    /* sem diacríticos e em minúsculas; preserva o comprimento, então os
       deslocamentos do <mark> valem também no texto original */
    var fold = function (s) {
      return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
    };

    function mark(text, term) {
      var i = fold(text).indexOf(term);
      if (i < 0) return esc(text);
      return esc(text.slice(0, i)) + '<mark>' + esc(text.slice(i, i + term.length)) +
        '</mark>' + esc(text.slice(i + term.length));
    }

    /* faixas: 0 título começa com, 1 título contém, 2 aba ou resumo contém.
       A ordem do mapa entra dividida por mil, como desempate estável. */
    function rank(term) {
      var out = [];
      flat.forEach(function (r, i) {
        var t = fold(r.page.label), s = -1;
        if (t.indexOf(term) === 0) s = 0;
        else if (t.indexOf(term) >= 0) s = 1;
        else if (fold(where(r) + ' ' + (r.page.summary || '')).indexOf(term) >= 0) s = 2;
        if (s >= 0) out.push({ u: r.u, t: r.page.label, c: where(r), s: s + i / 1000 });
      });
      return out.sort(function (a, b) { return a.s - b.s; }).slice(0, 12);
    }

    function all() {
      return flat.slice(0, 12).map(function (r) {
        return { u: r.u, t: r.page.label, c: where(r) };
      });
    }

    function paint(found, term) {
      rows = found;
      sel = rows.length ? 0 : -1;
      if (!rows.length) {
        list.innerHTML = '<li class="no-results">Nada encontrado para “' + esc(term) + '”.</li>';
        return;
      }
      list.innerHTML =
        (term ? '' : '<li class="results-label" role="presentation">Todas as páginas</li>') +
        rows.map(function (r, i) {
          return '<li class="result" role="option" aria-selected="' + (i === 0) + '">' +
            '<a href="' + r.u + '">' +
            '<span class="r-title">' + (term ? mark(r.t, term) : esc(r.t)) + '</span>' +
            '<span class="r-path">' + esc(r.c) + '</span></a></li>';
        }).join('');
    }

    function run() {
      var q = (input.value || '').trim();
      if (!q) { paint(all(), ''); return; }
      paint(rank(fold(q)), fold(q));
    }
    input.addEventListener('input', run);

    /* o ds.js abre o diálogo; aqui só reagimos à abertura */
    new MutationObserver(function () {
      if (dlg.open) { input.value = ''; paint(all(), ''); }
    }).observe(dlg, { attributes: true, attributeFilter: ['open'] });

    function move(d) {
      if (!rows.length) return;
      sel = (sel + d + rows.length) % rows.length;
      var items = $$('.result', list);
      items.forEach(function (li, i) { li.setAttribute('aria-selected', i === sel); });
      if (items[sel]) items[sel].scrollIntoView({ block: 'nearest' });
    }

    dlg.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { e.preventDefault(); if (rows[sel]) location.href = rows[sel].u; }
    });
  }

  header(); side(); pager(); footer(); areas(); tocInline(); search();
})();

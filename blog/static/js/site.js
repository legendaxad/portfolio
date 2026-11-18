/**
 * Portfolio interactions — vanilla JS + (optional) GSAP/ScrollTrigger.
 * Every feature degrades gracefully: content is fully usable without JS,
 * without GSAP, with reduced motion, and on touch devices.
 */
(function () {
  'use strict';

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  var hasGSAP = function () { return !!(window.gsap && window.ScrollTrigger); };
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  /* ------------------------------------------------------------------ */
  /* Hero entrance                                                       */
  /* ------------------------------------------------------------------ */
  function initHero() {
    var hero = $('[data-hero]');
    if (!hero) return;
    $$('.hero__title .w > span', hero).forEach(function (el, i) { el.style.setProperty('--i', i); });
    $$('[data-hero-in]', hero).forEach(function (el, i) { el.style.setProperty('--d', 450 + i * 120); });
    requestAnimationFrame(function () { requestAnimationFrame(function () { hero.classList.add('is-in'); }); });

    // Hero card 3D tilt follows the pointer
    var card = $('[data-tilt]', hero);
    if (card && finePointer && !reduceMotion) {
      window.addEventListener('pointermove', function (e) {
        var x = e.clientX / window.innerWidth - 0.5;
        var y = e.clientY / window.innerHeight - 0.5;
        card.style.setProperty('--ry', (-14 + x * 16).toFixed(2) + 'deg');
        card.style.setProperty('--rx', (6 - y * 12).toFixed(2) + 'deg');
      }, { passive: true });
    }
  }

  /* ------------------------------------------------------------------ */
  /* Scroll reveals                                                      */
  /* ------------------------------------------------------------------ */
  function initReveals() {
    var els = $$('[data-reveal]');
    if (!('IntersectionObserver' in window) || reduceMotion) {
      els.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }
    // stagger siblings that share a parent
    var groups = new Map();
    els.forEach(function (el) {
      var p = el.parentElement, n = groups.get(p) || 0;
      el.style.setProperty('--stagger', Math.min(n, 6));
      groups.set(p, n + 1);
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------------------------ */
  /* Navigation: state, hide-on-scroll, active indicator, progress        */
  /* ------------------------------------------------------------------ */
  function initNav() {
    var nav = $('[data-nav]');
    if (!nav) return;
    var bar = $('.scroll-progress');
    var links = $$('.nav__links a[data-section]');
    var indicator = $('.nav__indicator');
    var lastY = window.scrollY, ticking = false;

    function moveIndicator(link) {
      if (!indicator) return;
      if (!link) { indicator.style.opacity = 0; return; }
      indicator.style.opacity = 1;
      indicator.style.width = link.offsetWidth + 'px';
      indicator.style.transform = 'translateX(' + link.offsetLeft + 'px)';
    }

    function onScroll() {
      var y = window.scrollY;
      nav.classList.toggle('is-scrolled', y > 24);
      var menuOpen = document.body.classList.contains('menu-open');
      nav.classList.toggle('is-hidden', !menuOpen && y > 400 && y > lastY + 4);
      if (y < lastY - 4) nav.classList.remove('is-hidden');
      lastY = y;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      if (bar) bar.style.setProperty('--p', max > 0 ? (y / max).toFixed(4) : 0);
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
    }, { passive: true });
    onScroll();

    // Active section via IntersectionObserver
    var sections = links.map(function (l) { return document.getElementById(l.dataset.section); }).filter(Boolean);
    if (sections.length && 'IntersectionObserver' in window) {
      var current = null;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) current = en.target.id;
        });
        var active = null;
        links.forEach(function (l) {
          var on = l.dataset.section === current;
          l.classList.toggle('is-active', on);
          if (on) { active = l; l.setAttribute('aria-current', 'true'); } else l.removeAttribute('aria-current');
        });
        moveIndicator(active);
      }, { rootMargin: '-45% 0px -50% 0px' });
      sections.forEach(function (s) { io.observe(s); });
      // Clear when back in hero
      var hero = $('[data-hero]');
      if (hero) new IntersectionObserver(function (e) {
        if (e[0].isIntersecting) { current = null; links.forEach(function (l) { l.classList.remove('is-active'); }); moveIndicator(null); }
      }, { threshold: 0.6 }).observe(hero);
    }
    window.addEventListener('resize', function () { moveIndicator($('.nav__links a.is-active')); });
  }

  /* ------------------------------------------------------------------ */
  /* Mobile menu (focus-trapped, Esc to close)                           */
  /* ------------------------------------------------------------------ */
  function initMenu() {
    var btn = $('.nav__toggle'), menu = $('#mobile-menu');
    if (!btn || !menu) return;
    var links = $$('a', menu);

    function open() {
      menu.hidden = false;
      document.body.classList.add('menu-open');
      btn.setAttribute('aria-expanded', 'true');
      btn.setAttribute('aria-label', 'Close menu');
      $$('.menu__links a', menu).forEach(function (a, i) { a.style.transitionDelay = (80 + i * 45) + 'ms'; });
      requestAnimationFrame(function () { requestAnimationFrame(function () { menu.classList.add('is-open'); }); });
      setTimeout(function () { links[0] && links[0].focus(); }, 60);
    }
    function close(focusBtn) {
      menu.classList.remove('is-open');
      document.body.classList.remove('menu-open');
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('aria-label', 'Open menu');
      setTimeout(function () { menu.hidden = true; }, reduceMotion ? 0 : 250);
      if (focusBtn) btn.focus();
    }
    btn.addEventListener('click', function () {
      btn.getAttribute('aria-expanded') === 'true' ? close(false) : open();
    });
    links.forEach(function (a) { a.addEventListener('click', function () { close(false); }); });
    document.addEventListener('keydown', function (e) {
      if (menu.hidden) return;
      if (e.key === 'Escape') close(true);
      if (e.key === 'Tab') {
        var f = [btn].concat(links), i = f.indexOf(document.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
      }
    });
    window.matchMedia('(min-width: 960px)').addEventListener('change', function (m) { if (m.matches && !menu.hidden) close(false); });
  }

  /* ------------------------------------------------------------------ */
  /* Cursor follower, magnetic buttons, spotlight, soft tilt             */
  /* ------------------------------------------------------------------ */
  function initPointerFX() {
    if (!finePointer || reduceMotion) return;

    // Cursor (native cursor stays visible; this is an accent only)
    var cursor = $('.cursor');
    if (cursor) {
      document.documentElement.classList.add('has-cursor');
      var dot = $('.cursor__dot', cursor), ring = $('.cursor__ring', cursor);
      var x = -100, y = -100, rx = -100, ry = -100;
      window.addEventListener('pointermove', function (e) { x = e.clientX; y = e.clientY; }, { passive: true });
      (function loop() {
        rx += (x - rx) * 0.18; ry += (y - ry) * 0.18;
        dot.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0)';
        ring.style.transform = 'translate3d(' + rx + 'px,' + ry + 'px,0)';
        requestAnimationFrame(loop);
      })();
      document.addEventListener('pointerover', function (e) {
        var t = e.target.closest('a, button, summary, [data-cursor], input, textarea, label');
        cursor.classList.toggle('is-hover', !!t);
        var label = t && t.closest('[data-cursor]');
        cursor.classList.toggle('is-label', !!label);
        ring.textContent = label ? label.getAttribute('data-cursor') : '';
        cursor.classList.toggle('is-hidden', !!(t && t.matches('input, textarea')));
      });
      document.addEventListener('pointerleave', function () { x = y = -100; });
    }

    // Magnetic buttons
    $$('[data-magnetic]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var mx = (e.clientX - r.left - r.width / 2) * 0.25;
        var my = (e.clientY - r.top - r.height / 2) * 0.35;
        el.style.transform = 'translate(' + mx.toFixed(1) + 'px,' + my.toFixed(1) + 'px)';
      });
      el.addEventListener('pointerleave', function () { el.style.transform = ''; });
    });

    // Spotlight: CSS radial gradient follows the pointer
    $$('[data-spotlight], [data-spotlight-section]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        el.style.setProperty('--my', (e.clientY - r.top) + 'px');
      }, { passive: true });
    });

    // Soft 3D tilt on project cards
    $$('[data-tilt-soft]').forEach(function (el) {
      el.addEventListener('pointermove', function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
        el.style.setProperty('--ry', (px * 5).toFixed(2) + 'deg');
        el.style.setProperty('--rx', (-py * 5).toFixed(2) + 'deg');
      });
      el.addEventListener('pointerleave', function () { el.style.setProperty('--rx', '0deg'); el.style.setProperty('--ry', '0deg'); });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Stack tabs                                                           */
  /* ------------------------------------------------------------------ */
  function initStackTabs() {
    var tabs = $('[data-stack-tabs]'), grid = $('[data-stack]');
    if (!tabs || !grid) return;
    var buttons = $$('[role="tab"]', tabs);
    function select(btn) {
      var f = btn.dataset.filter;
      buttons.forEach(function (b) { var on = b === btn; b.setAttribute('aria-selected', on); b.tabIndex = on ? 0 : -1; });
      grid.dataset.active = f;
      $$('.stack-tile', grid).forEach(function (t) { t.classList.toggle('is-match', f !== 'all' && t.dataset.cat === f); });
    }
    buttons.forEach(function (b, i) {
      b.tabIndex = i === 0 ? 0 : -1;
      b.addEventListener('click', function () { select(b); });
      b.addEventListener('keydown', function (e) {
        var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
        if (!d) return;
        e.preventDefault();
        var n = buttons[(i + d + buttons.length) % buttons.length];
        n.focus(); select(n);
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Project filters with FLIP animation                                  */
  /* ------------------------------------------------------------------ */
  function initProjectFilters() {
    var bar = $('[data-project-filters]'), grid = $('[data-project-grid]');
    if (!bar || !grid) return;
    var buttons = $$('button', bar), cards = $$('.pcard', grid);
    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var f = btn.dataset.filter;
        buttons.forEach(function (b) { b.setAttribute('aria-pressed', b === btn); });
        var first = new Map(cards.map(function (c) { return [c, c.getBoundingClientRect()]; }));
        cards.forEach(function (c) {
          var show = f === 'all' || c.dataset.category === f;
          c.classList.toggle('is-hidden', !show);
          c.classList.toggle('pcard--wide', false);
        });
        // first two visible cards get the wide layout again
        cards.filter(function (c) { return !c.classList.contains('is-hidden'); }).slice(0, 2)
          .forEach(function (c) { c.classList.add('pcard--wide'); });
        if (reduceMotion || !grid.animate) return;
        cards.forEach(function (c) {
          if (c.classList.contains('is-hidden')) return;
          c.classList.add('is-visible');
          var a = first.get(c), b = c.getBoundingClientRect();
          if (a.width === 0) {
            c.animate([{ opacity: 0, transform: 'scale(.96)' }, { opacity: 1, transform: 'none' }], { duration: 500, easing: 'cubic-bezier(.16,1,.3,1)' });
          } else {
            var dx = a.left - b.left, dy = a.top - b.top;
            if (dx || dy) c.animate([{ transform: 'translate(' + dx + 'px,' + dy + 'px)' }, { transform: 'none' }], { duration: 600, easing: 'cubic-bezier(.16,1,.3,1)' });
          }
        });
        if (hasGSAP()) ScrollTrigger.refresh();
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Drag-to-scroll helper (mouse only; touch scrolls natively)           */
  /* ------------------------------------------------------------------ */
  function dragScroll(track) {
    var down = false, startX = 0, startLeft = 0, moved = false;
    track.addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      down = true; moved = false; startX = e.clientX; startLeft = track.scrollLeft;
    });
    window.addEventListener('pointermove', function (e) {
      if (!down) return;
      var dx = e.clientX - startX;
      if (Math.abs(dx) > 5 && !moved) { moved = true; track.classList.add('is-dragging'); }
      if (moved) track.scrollLeft = startLeft - dx;
    });
    window.addEventListener('pointerup', function () {
      if (!down) return;
      down = false;
      setTimeout(function () { track.classList.remove('is-dragging'); }, 0);
    });
    track.addEventListener('click', function (e) { if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; } }, true);
  }

  /* ------------------------------------------------------------------ */
  /* Featured reel: pinned horizontal scroll (desktop + GSAP) or native   */
  /* ------------------------------------------------------------------ */
  function initReel() {
    var reel = $('[data-reel]');
    if (!reel) return;
    var track = $('[data-reel-track]', reel), progress = $('[data-reel-progress]', reel);
    var canPin = hasGSAP() && !reduceMotion && window.matchMedia('(min-width: 1024px) and (min-height: 640px)').matches;
    var panels = $$('.reel__panel', track);

    if (canPin && panels.length > 1) {
      gsap.registerPlugin(ScrollTrigger);
      reel.classList.add('is-pinned');
      var distance = function () { return Math.max(0, track.scrollWidth - window.innerWidth); };
      gsap.to(track, {
        x: function () { return -distance(); },
        ease: 'none',
        scrollTrigger: {
          trigger: reel, start: 'top top', end: function () { return '+=' + distance(); },
          pin: true, scrub: 0.8, invalidateOnRefresh: true, anticipatePin: 1,
          onUpdate: function (self) { progress && progress.parentElement.style.setProperty('--p', self.progress.toFixed(3)); }
        }
      });
      // Keyboard users: focusing a link in an off-screen panel scrolls it into view
      panels.forEach(function (panel, i) {
        panel.addEventListener('focusin', function () {
          var st = ScrollTrigger.getAll().filter(function (s) { return s.trigger === reel; })[0];
          if (!st) return;
          var y = st.start + (st.end - st.start) * (i / Math.max(1, panels.length - 1));
          window.scrollTo({ top: y, behavior: 'auto' });
        });
      });
      return;
    }

    dragScroll(track);
    var update = function () {
      var max = track.scrollWidth - track.clientWidth;
      progress && progress.parentElement.style.setProperty('--p', max > 0 ? (track.scrollLeft / max).toFixed(3) : 1);
    };
    track.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ------------------------------------------------------------------ */
  /* Engineering flow tabs (auto-advance while in view)                  */
  /* ------------------------------------------------------------------ */
  function initFlow() {
    var flow = $('[data-flow]');
    if (!flow) return;
    var tabs = $$('.flow__node', flow), rail = $('.flow__rail', flow);
    var idx = 0, timer = null, userTook = false;

    function select(i, focus) {
      idx = (i + tabs.length) % tabs.length;
      tabs.forEach(function (t, j) {
        var on = j === idx;
        t.setAttribute('aria-selected', on);
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute('aria-controls'));
        if (panel) panel.hidden = !on;
      });
      if (focus) tabs[idx].focus();
    }
    function stop() { clearInterval(timer); timer = null; }
    function start() {
      if (timer || userTook || reduceMotion) return;
      timer = setInterval(function () { select(idx + 1); }, 4200);
    }
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { userTook = true; stop(); select(i); });
      t.addEventListener('keydown', function (e) {
        var map = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 };
        if (e.key in map) { e.preventDefault(); userTook = true; stop(); select(idx + map[e.key], true); }
        if (e.key === 'Home') { e.preventDefault(); select(0, true); }
        if (e.key === 'End') { e.preventDefault(); select(tabs.length - 1, true); }
      });
    });
    flow.addEventListener('pointerenter', stop);
    flow.addEventListener('pointerleave', start);
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (e) { e[0].isIntersecting ? start() : stop(); }, { threshold: 0.4 }).observe(flow);
    }
    var setRail = function () { if (rail) rail.style.setProperty('--rail-w', rail.offsetWidth + 'px'); };
    setRail();
    window.addEventListener('resize', setRail);
  }

  /* ------------------------------------------------------------------ */
  /* Scroll-linked lines: timeline + skills path + hero exit              */
  /* ------------------------------------------------------------------ */
  function initScrollLines() {
    var timeline = $('[data-timeline]'), path = $('[data-path] .path__line');
    var hero = $('[data-hero]');

    if (hasGSAP() && !reduceMotion) {
      gsap.registerPlugin(ScrollTrigger);
      if (timeline) {
        timeline.style.setProperty('--p', 0);
        ScrollTrigger.create({
          trigger: timeline, start: 'top 70%', end: 'bottom 60%', scrub: true,
          onUpdate: function (s) { $('.timeline__line', timeline).style.setProperty('--p', s.progress.toFixed(3)); }
        });
        $('.timeline__line', timeline).style.setProperty('--p', 0);
      }
      if (path) {
        path.style.setProperty('--p', 0);
        ScrollTrigger.create({
          trigger: path.parentElement, start: 'top 80%', end: 'bottom 55%', scrub: true,
          onUpdate: function (s) { path.style.setProperty('--p', s.progress.toFixed(3)); }
        });
      }
      if (hero) {
        gsap.to('.hero__inner', {
          yPercent: -12, opacity: 0.15, ease: 'none',
          scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true }
        });
        gsap.to('.hero__card', {
          yPercent: -40, ease: 'none',
          scrollTrigger: { trigger: hero, start: 'top top', end: 'bottom top', scrub: true }
        });
      }
      // section titles: subtle parallax drift for depth
      $$('.section-title').forEach(function (el) {
        gsap.fromTo(el, { y: 24 }, { y: -12, ease: 'none', scrollTrigger: { trigger: el, start: 'top bottom', end: 'bottom top', scrub: true } });
      });
      window.addEventListener('load', function () { ScrollTrigger.refresh(); });
    }
  }

  /* ------------------------------------------------------------------ */
  /* GitHub section                                                       */
  /* ------------------------------------------------------------------ */
  var LANG_COLORS = {
    Python: '#3572A5', TypeScript: '#3178c6', JavaScript: '#f1e05a', HTML: '#e34c26', CSS: '#563d7c',
    SCSS: '#c6538c', Shell: '#89e051', Java: '#b07219', Go: '#00ADD8', EJS: '#a91e50', Dart: '#00B4AB', Vue: '#41b883'
  };
  function esc(s) { var d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
  function ago(iso) {
    if (!iso) return '';
    var d = (Date.now() - new Date(iso).getTime()) / 86400000;
    if (d < 1) return 'today';
    if (d < 2) return 'yesterday';
    if (d < 30) return Math.floor(d) + ' days ago';
    if (d < 365) return Math.floor(d / 30) + ' mo ago';
    return Math.floor(d / 365) + ' yr ago';
  }
  function initGitHub() {
    var sec = $('[data-github]');
    if (!sec) return;
    var loaded = false;
    var load = function () {
      if (loaded) return; loaded = true;
      var wrap = $('.gh', sec);
      fetch(sec.dataset.endpoint, { headers: { Accept: 'application/json' } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data || !data.ok) throw new Error('unavailable');
          render(data);
          wrap.setAttribute('aria-busy', 'false');
        })
        .catch(function () {
          var tpl = $('template[data-gh-fallback]', sec);
          wrap.innerHTML = '';
          wrap.appendChild(tpl.content.cloneNode(true));
          wrap.setAttribute('aria-busy', 'false');
        });
    };
    function render(d) {
      var p = d.profile, total = d.languages.reduce(function (a, l) { return a + l.count; }, 0) || 1;
      $('[data-gh-profile]', sec).innerHTML =
        '<div class="gh-profile">' +
          (p.avatar_url ? '<img src="' + esc(p.avatar_url) + '&s=128" alt="" width="64" height="64" loading="lazy">' : '') +
          '<div><h3>' + esc(p.name || p.login) + '</h3><a href="' + esc(p.html_url) + '" target="_blank" rel="noopener noreferrer">@' + esc(p.login) + ' ↗</a></div>' +
        '</div>' +
        '<div class="gh-stats">' +
          '<div><b>' + esc(p.public_repos) + '</b><span>Public repos</span></div>' +
          '<div><b>' + esc(p.followers) + '</b><span>Followers</span></div>' +
          '<div><b>' + esc(d.total_stars) + '</b><span>Stars</span></div>' +
        '</div>' + (d.stale ? '<p class="empty" style="margin-top:1rem;font-size:.75rem">Showing cached data — GitHub is temporarily unreachable.</p>' : '');
      var bar = d.languages.map(function (l, i) {
        return '<span title="' + esc(l.name) + '" style="width:' + (l.count / total * 100).toFixed(2) + '%;background:' + (LANG_COLORS[l.name] || '#8b93a7') + ';animation-delay:' + (i * 80) + 'ms"></span>';
      }).join('');
      var list = d.languages.map(function (l) {
        return '<li><i style="background:' + (LANG_COLORS[l.name] || '#8b93a7') + '"></i>' + esc(l.name) + '<b>' + l.count + ' repo' + (l.count > 1 ? 's' : '') + '</b></li>';
      }).join('');
      $('[data-gh-langs]', sec).innerHTML =
        '<h3 class="gh-card__title">Languages <small>primary language of ' + total + ' public, non-fork repos</small></h3>' +
        '<div class="langbar" role="img" aria-label="Language distribution">' + bar + '</div><ul class="langlist">' + list + '</ul>';
      $('[data-gh-repos]', sec).innerHTML =
        '<h3 class="gh-card__title">Recently updated <small>public repositories</small></h3><div class="repo-list">' +
        d.repos.map(function (r) {
          return '<a class="repo" href="' + esc(r.html_url) + '" target="_blank" rel="noopener noreferrer"><strong>' + esc(r.name) + '</strong>' +
            '<p>' + esc(r.description || 'No description') + '</p>' +
            '<small>' + (r.language ? '<span><i style="display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;background:' + (LANG_COLORS[r.language] || '#8b93a7') + '"></i>' + esc(r.language) + '</span>' : '') +
            (r.stars ? '<span>★ ' + r.stars + '</span>' : '') + '<span>updated ' + ago(r.pushed_at) + '</span></small></a>';
        }).join('') + '</div>' +
        '<p style="margin-top:1rem"><a class="link" href="' + esc(p.html_url) + '" target="_blank" rel="noopener noreferrer">View all repositories and the contribution graph on GitHub ↗</a></p>';
    }
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (e) { if (e[0].isIntersecting) { io.disconnect(); load(); } }, { rootMargin: '400px' });
      io.observe(sec);
    } else load();
  }

  /* ------------------------------------------------------------------ */
  /* Certificates carousel + lightbox                                    */
  /* ------------------------------------------------------------------ */
  function initCarousel() {
    var track = $('[data-carousel-track]'), ctrl = $('[data-carousel-ctrl]');
    if (!track) return;
    dragScroll(track);
    var prev = ctrl && $('[data-prev]', ctrl), next = ctrl && $('[data-next]', ctrl);
    var step = function () { var c = $('.cert', track); return c ? c.offsetWidth + 20 : 300; };
    var sync = function () {
      if (!ctrl) return;
      var max = track.scrollWidth - track.clientWidth;
      ctrl.hidden = max <= 4;
      prev.disabled = track.scrollLeft <= 4;
      next.disabled = track.scrollLeft >= max - 4;
    };
    if (prev) prev.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: reduceMotion ? 'auto' : 'smooth' }); });
    if (next) next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: reduceMotion ? 'auto' : 'smooth' }); });
    track.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();
  }

  function initLightbox() {
    var dlg = $('[data-lightbox]');
    if (!dlg || typeof dlg.showModal !== 'function') return;
    var opener = null;
    $$('[data-cert-open]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        opener = btn;
        var img = $('[data-lb-img]', dlg);
        img.src = btn.dataset.img;
        img.alt = btn.dataset.title || '';
        $('[data-lb-title]', dlg).textContent = btn.dataset.title || '';
        $('[data-lb-desc]', dlg).textContent = btn.dataset.desc || '';
        $('[data-lb-meta]', dlg).innerHTML = [btn.dataset.issuer, btn.dataset.year].filter(Boolean).map(function (s) { return '<span>' + esc(s) + '</span>'; }).join('');
        var a = $('[data-lb-url]', dlg);
        if (btn.dataset.url) { a.href = btn.dataset.url; a.hidden = false; } else a.hidden = true;
        dlg.showModal();
      });
    });
    $('[data-lightbox-close]', dlg).addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
    dlg.addEventListener('close', function () { if (opener) opener.focus(); });
  }

  /* ------------------------------------------------------------------ */
  /* Contact form: validation + AJAX with progressive enhancement        */
  /* ------------------------------------------------------------------ */
  function initContact() {
    var form = $('[data-contact-form]');
    if (!form || !window.fetch) return;
    var btn = $('[data-send]', form), status = $('[data-form-status]', form);
    var rules = {
      name: function (v) { return v.trim().length >= 2 ? '' : 'Please enter your name.'; },
      email: function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()) ? '' : 'Please enter a valid email address.'; },
      subject: function () { return ''; },
      message: function (v) { return v.trim().length >= 10 ? '' : 'Please write at least a short sentence (10+ characters).'; }
    };
    function setError(name, msg) {
      var input = form.elements[name]; if (!input) return;
      var field = input.closest('.field'), err = $('.field__error', field);
      field.classList.toggle('is-invalid', !!msg);
      field.classList.toggle('is-valid', !msg && input.value.trim() !== '');
      if (err) err.textContent = msg || '';
      input.setAttribute('aria-invalid', msg ? 'true' : 'false');
      if (err) input.setAttribute('aria-describedby', err.id);
    }
    function validate(name) { var m = rules[name](form.elements[name].value); setError(name, m); return !m; }
    Object.keys(rules).forEach(function (n) {
      var el = form.elements[n]; if (!el) return;
      el.addEventListener('blur', function () { if (el.value) validate(n); });
      el.addEventListener('input', function () { if (el.closest('.field').classList.contains('is-invalid')) validate(n); });
    });
    function setStatus(msg, kind) { status.textContent = msg; status.className = 'cform__status' + (kind ? ' is-' + kind : ''); }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var ok = Object.keys(rules).map(validate).every(Boolean);
      if (!ok) {
        setStatus('Please fix the highlighted fields.', 'error');
        btn.classList.remove('is-error'); void btn.offsetWidth; btn.classList.add('is-error');
        var bad = $('.field.is-invalid .field__input', form); bad && bad.focus();
        return;
      }
      btn.classList.remove('is-error', 'is-done');
      btn.classList.add('is-busy');
      btn.setAttribute('aria-busy', 'true');
      setStatus('Sending…');
      fetch(form.action, {
        method: 'POST', body: new FormData(form), credentials: 'same-origin',
        headers: { 'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json' }
      })
        .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, data: j }; }); })
        .then(function (res) {
          btn.classList.remove('is-busy'); btn.removeAttribute('aria-busy');
          if (res.ok && res.data.ok) {
            btn.classList.add('is-done');
            setStatus(res.data.message, 'success');
            form.reset();
            $$('.field', form).forEach(function (f) { f.classList.remove('is-valid', 'is-invalid'); });
            setTimeout(function () { btn.classList.remove('is-done'); }, 4000);
          } else {
            var errs = (res.data && res.data.errors) || {};
            Object.keys(errs).forEach(function (k) { if (rules[k]) setError(k, errs[k][0].message); });
            var nonField = errs.__all__ && errs.__all__[0] && errs.__all__[0].message;
            setStatus(nonField || res.data.message || 'Something went wrong. Please try again.', 'error');
            btn.classList.add('is-error');
          }
        })
        .catch(function () {
          btn.classList.remove('is-busy'); btn.removeAttribute('aria-busy'); btn.classList.add('is-error');
          setStatus('Network error — please try again, or email me directly.', 'error');
        });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Small utilities                                                      */
  /* ------------------------------------------------------------------ */
  function initUtilities() {
    $$('[data-copy]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (!navigator.clipboard) return;
        navigator.clipboard.writeText(btn.dataset.copy).then(function () {
          var use = $('use', btn), prev = use.getAttribute('href');
          use.setAttribute('href', '#i-check'); btn.setAttribute('aria-label', 'Copied!');
          setTimeout(function () { use.setAttribute('href', prev); btn.setAttribute('aria-label', 'Copy email address'); }, 1800);
        });
      });
    });
    $$('[data-scroll-top]').forEach(function (b) {
      b.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
        var m = $('#main'); m && m.focus({ preventScroll: true });
      });
    });
    $$('.toast').forEach(function (t) {
      var close = function () { t.style.opacity = 0; setTimeout(function () { t.remove(); }, 300); };
      $('.toast__close', t).addEventListener('click', close);
      setTimeout(close, 7000);
    });
  }

  function boot() {
    initHero();
    initReveals();
    initNav();
    initMenu();
    initPointerFX();
    initStackTabs();
    initProjectFilters();
    initReel();
    initFlow();
    initScrollLines();
    initGitHub();
    initCarousel();
    initLightbox();
    initContact();
    initUtilities();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();

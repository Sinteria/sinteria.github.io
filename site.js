(() => {
  'use strict';
  const root = document.documentElement;
  root.classList.add('js');
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  const setMenu = (open) => {
    if (!toggle || !nav) return;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    nav.classList.toggle('is-open', open);
    document.body.classList.toggle('menu-open', open);
  };
  toggle?.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && toggle?.getAttribute('aria-expanded') === 'true') {
      setMenu(false);
      toggle.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (toggle?.getAttribute('aria-expanded') === 'true' && !event.target.closest('.site-header')) setMenu(false);
  });
  nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setMenu(false)));
  window.matchMedia('(min-width: 901px)').addEventListener('change', (event) => {
    if (event.matches) setMenu(false);
  });
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const pause = document.querySelector('.motion-toggle');
  let paused = false;
  const applyMotion = () => {
    const enabled = !paused && !reduceMotion.matches;
    root.classList.toggle('animated', enabled);
    root.classList.toggle('motion-paused', !enabled);
    if (!enabled) root.classList.remove('motion');
    if (pause) {
      pause.setAttribute('aria-pressed', String(!enabled));
      pause.textContent = reduceMotion.matches ? 'Movimiento reducido activo' : paused ? 'Activar animaciones' : 'Pausar animaciones';
      pause.disabled = reduceMotion.matches;
    }
  };
  if ('IntersectionObserver' in window && !reduceMotion.matches) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, {threshold: 0.04, rootMargin: '0px 0px 35px 0px'});
    document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
    root.classList.add('motion');
  }
  pause?.addEventListener('click', () => { paused = !paused; applyMotion(); });
  reduceMotion.addEventListener('change', applyMotion);
  applyMotion();
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('.tilt').forEach((element) => {
      let frame = 0;
      element.addEventListener('pointermove', (event) => {
        if (paused || reduceMotion.matches) return;
        const rect = element.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width - 0.5) * 7;
        const y = ((event.clientY - rect.top) / rect.height - 0.5) * -5;
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          element.style.setProperty('--tilt-x', `${x}deg`);
          element.style.setProperty('--tilt-y', `${y}deg`);
        });
      });
      element.addEventListener('pointerleave', () => {
        cancelAnimationFrame(frame);
        element.style.removeProperty('--tilt-x');
        element.style.removeProperty('--tilt-y');
      });
    });
  }
  const dialog = document.getElementById('galeria-ampliada');
  if (!dialog || typeof dialog.showModal !== 'function') return;
  const image = dialog.querySelector('.v-lightbox-image');
  const title = dialog.querySelector('#galeria-titulo');
  const count = dialog.querySelector('.v-lightbox-count');
  const previous = dialog.querySelector('.v-lightbox-prev');
  const next = dialog.querySelector('.v-lightbox-next');
  const close = dialog.querySelector('.v-lightbox-close');
  const links = Array.from(document.querySelectorAll('.image-open'));
  let group = [], current = 0, opener;
  const displayImage = (index) => {
    current = (index + group.length) % group.length;
    const link = group[current];
    image.src = link.dataset.full;
    image.alt = link.querySelector('img')?.alt || link.dataset.caption;
    title.textContent = link.dataset.caption;
    count.textContent = `${current + 1} de ${group.length} · Material visual de Sinteria`;
    previous.hidden = next.hidden = group.length < 2;
  };
  links.forEach((link) => link.addEventListener('click', (event) => {
    event.preventDefault();
    opener = link;
    group = links.filter((candidate) => candidate.dataset.gallery === link.dataset.gallery);
    displayImage(group.indexOf(link));
    dialog.showModal();
    document.body.classList.add('gallery-open');
    close.focus();
  }));
  close.addEventListener('click', () => dialog.close());
  previous.addEventListener('click', () => displayImage(current - 1));
  next.addEventListener('click', () => displayImage(current + 1));
  dialog.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); displayImage(current - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); displayImage(current + 1); }
  });
  dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => { document.body.classList.remove('gallery-open'); opener?.focus(); });
})();

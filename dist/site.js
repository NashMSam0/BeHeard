const navItems = [
  { label: 'Home', href: '/index.html', page: 'home' },
  { label: 'About Us', href: '/about.html', page: 'about', overview: 'About Us', sections: [
    ['Meet Our Founder', 'founder'], ['Our Board and Team', '/board.html']
  ] },
  {
    label: 'Our Programmes', href: '/programmes.html', page: 'programmes',
    overview: 'Our Programmes',
    sections: [
      ['Educational Support', 'education'],
      ['Carlos’ Crusaders Scholarships', 'education'],
      ['Counselling Services', 'counselling'],
      ['Women and Community Empowerment', 'empowerment'],
      ['Child Protection and Welfare', 'child-protection'],
      ['Community Outreach', 'outreach']
    ]
  },
  { label: 'Success Stories', href: '/stories.html', page: 'stories', overview: 'Success Stories', sections: [
    ['Gallery', '/gallery.html'], ['News and Events', 'news']
  ] },
  {
    label: 'Sponsorships', href: '/involved.html', page: 'involved',
    overview: 'Donations and Sponsorships',
    sections: [
      ['Donate', 'donate'],
      ['Volunteer and Partner With Us', 'volunteer'],
      ['Newsletter subscription', 'updates']
    ]
  },
  { label: 'Contact Us', href: '/contact.html', page: 'contact' }
];

const page = document.body.dataset.page;
function navItem(item) {
  const current = item.page === page ? ' aria-current="page"' : '';
  if (!item.sections) return `<a href="${item.href}"${current}>${item.label}</a>`;
  const links = item.sections.map(([label, target]) => {
    const href = target.startsWith('/') ? target : `${item.href}#${target}`;
    return `<a href="${href}">${label}</a>`;
  });
  return `<details class="nav-group">
    <summary>${item.label}</summary>
    <div class="nav-panel"><a href="${item.href}"${current}>${item.overview}</a>${links.join('')}</div>
  </details>`;
}

const header = document.getElementById('site-header');
if (header) {
  header.innerHTML = `<header class="site-header"><div class="nav-wrap">
    <a class="brand" href="/" aria-label="BeHeard Zimbabwe"><img class="brand-logo" src="/beheard-logo.jpg" alt="BeHeard Zimbabwe" width="1080" height="1080" fetchpriority="high"></a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-navigation">Website Pages</button>
    <nav class="nav-links" id="primary-navigation" aria-label="Website Pages">
      ${navItems.map(navItem).join('')}<a class="nav-donate" href="/involved.html#donate">Donate Now</a>
    </nav></div></header>`;

  const toggle = header.querySelector('.menu-toggle');
  const nav = header.querySelector('nav');
  const groups = [...nav.querySelectorAll('details')];
  const hoverNavigation = matchMedia('(min-width: 1001px) and (hover: hover) and (pointer: fine)');
  groups.forEach(group => {
    group.addEventListener('pointerenter', event => {
      if (!hoverNavigation.matches || event.pointerType === 'touch') return;
      groups.forEach(other => { other.open = other === group; });
    });
    group.addEventListener('pointerleave', () => {
      if (hoverNavigation.matches && !group.contains(document.activeElement)) group.open = false;
    });
  });

  function closeNavigation() {
    groups.forEach(group => { group.open = false; });
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }

  toggle.addEventListener('click', () => {
    if (nav.classList.contains('is-open')) return closeNavigation();
    nav.classList.add('is-open');
    toggle.setAttribute('aria-expanded', 'true');

  });
  nav.addEventListener('click', event => {
    if (event.target.closest('a')) return closeNavigation();
    const summary = event.target.closest('summary');
    if (summary) groups.filter(group => group !== summary.parentElement).forEach(group => { group.open = false; });
  });
  document.addEventListener('pointerdown', event => {
    if (!header.contains(event.target)) closeNavigation();
  });
  document.addEventListener('focusin', event => {
    if (!header.contains(event.target)) return closeNavigation();
    groups.forEach(group => { if (!group.contains(event.target)) group.open = false; });
  });
  header.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const group = groups.find(item => item.open);
    if (group) {
      group.open = false;
      group.querySelector('summary').focus();
    } else if (nav.classList.contains('is-open')) {
      closeNavigation();
      toggle.focus();
    }
  });
  window.matchMedia('(max-width: 1000px)').addEventListener('change', closeNavigation);
}
const footer = document.getElementById('site-footer');
if (footer) {
  footer.innerHTML = `<footer class="site-footer"><div class="wrap footer-content">
    <a class="brand" href="/" aria-label="BeHeard Zimbabwe"><img class="brand-logo" src="/beheard-logo.jpg" alt="BeHeard Zimbabwe" width="1080" height="1080" loading="lazy"></a>
    <address>2539 Chinotimba, Victoria Falls, Zimbabwe
      <a href="tel:+263720116342">+263 72 011 6342</a>
      <a href="mailto:info@beheardzim.org">info@beheardzim.org</a>
    </address>
    <nav aria-label="Website Pages">
      <a href="/about.html#founder">Meet Our Founder</a>
      <a href="/involved.html#volunteer">Volunteer and Partner With Us</a>
      <a href="/contact.html">Contact Us</a>
      <a href="/privacy.html">Privacy Policy</a>
    </nav></div></footer>`;
}
const mode = document.createElement('select');
mode.className = 'theme-switch';
mode.setAttribute('aria-label', 'Colour mode');
const systemTheme = matchMedia('(prefers-color-scheme: dark)');
const themeChoices = { light: 'Light mode', dark: 'Dark mode', system: 'System settings' };
for (const [value, label] of Object.entries(themeChoices)) {
  const option = document.createElement('option');
  option.value = value;
  option.textContent = label;
  mode.append(option);
}
function applyTheme() {
  const useDark = mode.value === 'dark' || (mode.value === 'system' && systemTheme.matches);
  document.documentElement.dataset.theme = useDark ? 'dark' : 'light';
}
let savedTheme = null;
try { savedTheme = localStorage.getItem('beheard-theme'); } catch {}
mode.value = Object.hasOwn(themeChoices, savedTheme) ? savedTheme : 'light';
applyTheme();
mode.addEventListener('change', () => {
  applyTheme();
  try { localStorage.setItem('beheard-theme', mode.value); } catch {}
});
systemTheme.addEventListener('change', applyTheme);
document.body.append(mode);


function makeStorySlideshow(grids, label) {
  const items = Array.from(grids).flatMap(grid => Array.from(grid.children));
  if (items.length < 2) return;

  const slideshow = document.createElement('div');
  slideshow.className = 'story-slideshow';
  slideshow.setAttribute('role', 'region');
  slideshow.setAttribute('aria-label', label);
  const controls = document.createElement('div');
  controls.className = 'story-slide-controls';
  const previous = document.createElement('button');
  const next = document.createElement('button');
  const position = document.createElement('span');
  previous.type = next.type = 'button';
  previous.textContent = 'Previous';
  next.textContent = 'Next';
  position.setAttribute('aria-live', 'polite');
  controls.append(previous, position, next);
  grids[0].before(slideshow);

  const slides = items.map(item => {
    const slide = document.createElement('div');
    slide.className = 'story-slide';
    slide.append(item);
    slideshow.append(slide);
    return slide;
  });
  slideshow.append(controls);
  grids.forEach(grid => grid.remove());

  let current = 0;
  let advanceTimer;
  let inView = false;
  const nextIndex = () => (current + 1) % slides.length;

  function startCurrent() {
    clearTimeout(advanceTimer);
    if (!inView || document.hidden) return;
    const video = slides[current].querySelector('video');
    if (video) {
      video.play().catch(() => { /* Native controls remain available if autoplay is blocked. */ });
    } else {
      advanceTimer = setTimeout(() => show(nextIndex()), 3000);
    }
  }

  function show(index) {
    const previousVideo = slides[current].querySelector('video');
    if (previousVideo) {
      previousVideo.pause();
      previousVideo.currentTime = 0;
    }
    current = index;
    slides.forEach((slide, i) => { slide.hidden = i !== current; });
    position.textContent = `${current + 1} / ${slides.length}`;
    startCurrent();
  }
  previous.addEventListener('click', () => show((current + slides.length - 1) % slides.length));
  next.addEventListener('click', () => show(nextIndex()));
  slides.forEach((slide, index) => {
    const video = slide.querySelector('video');
    if (!video) return;
    video.muted = true;
    video.addEventListener('ended', () => {
      if (current === index) show(nextIndex());
    });
  });
  const updatePlayback = () => {
    if (!inView || document.hidden) slides[current].querySelector('video')?.pause();
    startCurrent();
  };
  const observer = new IntersectionObserver(([entry]) => {
    inView = entry.isIntersecting;
    updatePlayback();
  }, { threshold: 0.15 });
  observer.observe(slideshow);
  document.addEventListener('visibilitychange', updatePlayback);
  show(0);
}

makeStorySlideshow(document.querySelectorAll('#sewing-story .impact-media > .impact-grid'),
  'Women and Community Empowerment photos and videos');
makeStorySlideshow(document.querySelectorAll('#assisting-vulnerable-families .prose > .impact-grid'),
  'Assisting Vulnerable Families');
const education = document.querySelector('.education-categories');
if (education) {
  const tablist = document.createElement('div');
  tablist.className = 'education-tablist';
  tablist.setAttribute('role', 'tablist');
  tablist.setAttribute('aria-label', 'Educational Support');
  const panels = [];
  const tabs = Array.from(education.querySelectorAll('details'), (details, index) => {
    const summary = details.querySelector('summary');
    const label = summary.textContent.trim();
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.textContent = label;
    tab.id = `education-tab-${index}`;
    tab.setAttribute('role', 'tab');
    const panel = document.createElement('div');
    panel.className = 'education-panel';
    panel.id = `education-panel-${index}`;
    panel.setAttribute('role', 'tabpanel');
    panel.setAttribute('aria-labelledby', tab.id);
    tab.setAttribute('aria-controls', panel.id);
    const copy = document.createElement('div');
    copy.className = 'education-panel-copy';
    const title = document.createElement('h3');
    title.textContent = label;
    copy.append(title);
    summary.remove();
    const gallery = details.querySelector('.uniform-gallery');
    if (gallery) panel.append(gallery);
    copy.append(...details.childNodes);
    panel.append(copy);
    panels.push(panel);
    tablist.append(tab);
    tab.addEventListener('click', () => select(index));
    return tab;
  });
  function select(index) {
    tabs.forEach((tab, position) => {
      const active = index === position;
      tab.setAttribute('aria-selected', String(active));
      tab.tabIndex = active ? 0 : -1;
      panels[position].hidden = !active;
    });
  }
  tablist.addEventListener('keydown', event => {
    const index = tabs.indexOf(event.target);
    const offsets = { ArrowLeft: -1, ArrowRight: 1 };
    if (!(event.key in offsets)) return;
    event.preventDefault();
    const next = (index + offsets[event.key] + tabs.length) % tabs.length;
    select(next);
    tabs[next].focus();
  });
  education.replaceChildren(tablist, ...panels);
  education.classList.add('education-tabs');
  select(0);
}
document.querySelectorAll('.home-slideshow').forEach(slideshow => {
  const track = slideshow.querySelector('.slide-track');
  const toggle = slideshow.querySelector('.slideshow-toggle');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches;
  let slide = 0;
  const move = direction => {
    slide = (Math.round(track.scrollLeft / track.clientWidth) + direction + track.children.length) % track.children.length;
    track.scrollTo({left: slide * track.clientWidth, behavior: reduced.matches ? 'instant' : 'smooth'});
  };
  if (slideshow.classList.contains('uniform-gallery')) {
    const controls = document.createElement('div');
    controls.className = 'gallery-controls';
    const previous = document.createElement('button');
    previous.type = 'button'; previous.textContent = '←'; previous.setAttribute('aria-label', 'Previous photograph');
    const next = document.createElement('button');
    next.type = 'button'; next.textContent = '→'; next.setAttribute('aria-label', 'Next photograph');
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    toggle?.remove();
    controls.append(previous, next);
    slideshow.append(controls);
    track.tabIndex = 0;
    track.addEventListener('keydown', event => {
      if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
        event.preventDefault(); move(event.key === 'ArrowRight' ? 1 : -1);
      }
    });
    setInterval(() => {
      if (!document.hidden && track.clientWidth && track.children.length > 1) move(1);
    }, 3000);
    return;
  }
  const update = () => { toggle.textContent = paused ? 'Play photographs' : 'Pause photographs'; };
  toggle.addEventListener('click', () => { paused = !paused; update(); });
  reduced.addEventListener('change', () => { paused = reduced.matches; update(); });
  update();
  setInterval(() => {
    if (paused || document.hidden || slideshow.matches(':hover') || slideshow.contains(document.activeElement)) return;
    move(1);
  }, 5500);
});

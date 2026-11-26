const navItems = [
  { label: 'Home', href: '/index.html', page: 'home' },
  { label: 'About Us', href: '/about.html', page: 'about' },
  {
    label: 'Our Programmes', href: '/programmes.html', page: 'programmes',
    overview: 'Our Programmes',
    sections: [
      ['Educational Support', 'education'],
      ['Counselling Services', 'counselling'],
      ['Women and Community Empowerment', 'empowerment'],
      ['Child Protection and Welfare', 'child-protection'],
      ['Community Outreach', 'outreach']
    ]
  },
  { label: 'Success Stories', href: '/stories.html', page: 'stories' },
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
  const links = item.sections.map(([label, id]) => `<a href="${item.href}#${id}">${label}</a>`);
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
const mode = document.createElement('button');
mode.className = 'theme-switch';
mode.type = 'button';
function applyTheme(value) {
  document.documentElement.dataset.theme = value;
  mode.textContent = value === 'dark' ? 'Light mode' : 'Dark mode';
}
let savedTheme;
try { savedTheme = localStorage.getItem('beheard-theme'); } catch {}
applyTheme(savedTheme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
mode.addEventListener('click', () => {
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  try { localStorage.setItem('beheard-theme', document.documentElement.dataset.theme); } catch {}
});
document.body.append(mode);
document.querySelectorAll('.home-slideshow').forEach(slideshow => {
  const track = slideshow.querySelector('.slide-track');
  const toggle = slideshow.querySelector('.slideshow-toggle');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reduced.matches;
  let slide = 0;
  const update = () => { toggle.textContent = paused ? 'Play photographs' : 'Pause photographs'; };
  toggle.addEventListener('click', () => { paused = !paused; update(); });
  reduced.addEventListener('change', () => { paused = reduced.matches; update(); });
  update();
  setInterval(() => {
    if (paused || document.hidden || slideshow.matches(':hover') || slideshow.contains(document.activeElement)) return;
    slide = (Math.round(track.scrollLeft / track.clientWidth) + 1) % track.children.length;
    track.scrollTo({left: slide * track.clientWidth, behavior: reduced.matches ? 'instant' : 'smooth'});
  }, 5500);
});

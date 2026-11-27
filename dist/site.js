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
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-navigation">Categories</button>
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
      <div class="contact-social-links"><a href="mailto:info@beheardzim.org"><svg class="social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor"><rect x="3" y="5" width="18" height="14" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="m4 6 8 7 8-7" fill="none" stroke="currentColor" stroke-width="1.8"/></svg><span>info@beheardzim.org</span></a><a href="https://www.instagram.com/beheard_zimbabwe/"><svg class="social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.5" cy="6.5" r="1.2"/></svg><span>Instagram</span></a><a href="https://www.tiktok.com/@beheard.zimbabwe"><svg class="social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor"><path d="M16.6 2c.3 2.6 1.8 4.2 4.4 4.4v3.5a9 9 0 0 1-4.4-1.3v7.1a6.5 6.5 0 1 1-5.6-6.4v3.6a3 3 0 1 0 2.1 2.8V2z"/></svg><span>TikTok</span></a><a href="https://www.facebook.com/share/16V8PWUCgvc/"><svg class="social-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="currentColor"><path d="M14 22v-9h3l.5-4H14V6.5c0-1.2.4-2 2-2H18V1.2C17.5 1.1 16.4 1 15 1c-3 0-5 1.8-5 5v3H7v4h3v9z"/></svg><span>Facebook</span></a></div>
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
document.querySelectorAll('.education-categories').forEach((education, groupIndex) => {
  const tablist = document.createElement('div');
  tablist.className = 'education-tablist';
  tablist.setAttribute('role', 'tablist');
  tablist.setAttribute('aria-label', education.classList.contains('family-categories') ? 'Assisting Vulnerable Families' : 'Educational Support');
  const panels = [];
  const tabs = Array.from(education.querySelectorAll('details'), (details, index) => {
    const summary = details.querySelector('summary');
    const label = summary.textContent.trim();
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.textContent = label;
    tab.id = `education-tab-${groupIndex}-${index}`;
    tab.setAttribute('role', 'tab');
    const panel = document.createElement('div');
    panel.className = 'education-panel';
    panel.id = `education-panel-${groupIndex}-${index}`;
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
});
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

const donationForm = document.getElementById('donation-chooser');
if (donationForm) {
  const amountInput = donationForm.elements.amount;
  const dialog = document.getElementById('donation-dialog');
  const amountButtons = donationForm.querySelectorAll('[data-amount]');
  amountButtons.forEach(button => {
    button.addEventListener('click', () => {
      amountInput.value = button.dataset.amount;
      amountButtons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    });
    button.setAttribute('aria-pressed', 'false');
  });
  amountInput.addEventListener('input', () => {
    amountButtons.forEach(button => button.setAttribute('aria-pressed',
      String(button.dataset.amount === amountInput.value)));
  });
  donationForm.addEventListener('submit', event => {
    event.preventDefault();
    if (!donationForm.reportValidity()) return;
    const monthly = donationForm.elements.frequency.value === 'monthly';
    const amount = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD'})
      .format(Number(amountInput.value));
    document.getElementById('donation-summary').textContent =
      'Your ' + (monthly ? 'monthly' : 'once-off') + ' donation of US ' + amount;
    const methods = dialog.querySelector('.donation-dialog-methods');
    methods.replaceChildren();
    document.querySelectorAll('#payment-methods > .wrap > .donation-methods .donation-method')
      .forEach(method => {
        if (method.querySelector('h3').textContent === 'PayPal' && !method.querySelector('a')) return;
        const details = document.createElement('details');
        const summary = document.createElement('summary');
        summary.textContent = method.querySelector('h3').textContent;
        details.append(summary);
        Array.from(method.children).filter(child => child.tagName !== 'H3')
          .forEach(child => details.append(child.cloneNode(true)));
        methods.append(details);
      });
    dialog.querySelector('.donation-transfer-note').textContent = monthly
      ? 'Arrange a monthly standing order with your bank, or repeat your EcoCash donation each month. Confirm the available EcoCash currency with the recipient before sending.'
      : 'Confirm the available EcoCash currency with the recipient before sending. Bank transfers use USD.';
    dialog.classList.add('payment-step-active');
    donationForm.hidden = true;
    dialog.querySelector('.donation-payment-step').hidden = false;
    document.getElementById('donation-dialog-title').textContent = 'Choose a payment method';
  });
  dialog.querySelector('.donation-close').addEventListener('click', () => dialog.close());
  function showAmountStep() {
    dialog.classList.remove('payment-step-active');
    donationForm.hidden = false;
    dialog.querySelector('.donation-payment-step').hidden = true;
    document.getElementById('donation-dialog-title').textContent = 'Make a donation';
  }
  dialog.querySelector('.donation-back').addEventListener('click', showAmountStep);
  document.addEventListener('click', event => {
    const link = event.target.closest('a');
    if (!link || !link.href) return;
    const target = new URL(link.href);
    if (target.origin !== location.origin || target.pathname !== '/involved.html' || target.hash !== '#donate') return;
    event.preventDefault();
    showAmountStep();
    dialog.showModal();
  });
}

const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
if (!motionPreference.matches) {
  document.querySelectorAll('main > section').forEach(section => {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.animate([{opacity: .65, transform: 'translateY(12px)'}, {opacity: 1, transform: 'translateY(0)'}],
          {duration: 450, easing: 'ease-out'});
        observer.unobserve(entry.target);
      });
    }, {threshold: .08});
    observer.observe(section);
  });
  if (matchMedia('(hover: hover) and (pointer: fine)').matches) {
    import('/button-effects.js').catch(() => {});
  }
}

if (!motionPreference.matches && matchMedia('(hover: hover) and (pointer: fine)').matches) {
  document.querySelectorAll('main a[href^="/programmes.html#"]').forEach(card => {
    card.classList.add('programme-depth');
    card.addEventListener('pointermove', event => {
      if (motionPreference.matches) return;
      const box = card.getBoundingClientRect();
      const x = (event.clientX - box.left) / box.width - .5;
      const y = (event.clientY - box.top) / box.height - .5;
      card.style.transform = 'perspective(700px) rotateX(' + (-y * 5) + 'deg) rotateY(' + (x * 5) + 'deg) translateY(-2px)';
    });
    card.addEventListener('pointerleave', () => { card.style.transform = ''; });
    motionPreference.addEventListener('change', () => { card.style.transform = ''; });
  });
}
document.querySelectorAll('.gallery-grid img, .home-slideshow img').forEach(image => {
  image.classList.add('gallery-depth-image');
});

import * as THREE from './three.module.min.js';

const button = document.querySelector('.nav-donate');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
if (button && !reduced.matches) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({alpha: true, antialias: true});
  } catch {}
  if (renderer) {
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    renderer.setSize(150, 60);
    const canvas = renderer.domElement;
    canvas.className = 'button-glow';
    canvas.setAttribute('aria-hidden', 'true');
    button.append(canvas);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-2.5, 2.5, 1, -1, .1, 10);
    camera.position.z = 3;
    const geometry = new THREE.TorusGeometry(.65, .035, 8, 48);
    const material = new THREE.MeshBasicMaterial({color: 0xffffff, transparent: true, opacity: .55});
    const ring = new THREE.Mesh(geometry, material);
    scene.add(ring);
    let frame = 0;
    let start = 0;
    function stop() {
      cancelAnimationFrame(frame);
      frame = 0;
      canvas.style.opacity = '0';
    }
    function draw(time) {
      if (document.hidden || reduced.matches) return stop();
      ring.rotation.y = (time - start) * .0015;
      ring.rotation.z = (time - start) * .0006;
      renderer.render(scene, camera);
      frame = requestAnimationFrame(draw);
    }
    button.addEventListener('pointerenter', () => {
      if (frame || reduced.matches) return;
      start = performance.now();
      canvas.style.opacity = '1';
      frame = requestAnimationFrame(draw);
    });
    button.addEventListener('pointerleave', stop);
    document.addEventListener('visibilitychange', stop);
    reduced.addEventListener('change', stop);
    window.addEventListener('pagehide', () => {
      stop();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
    }, {once: true});
  }
}

const hero = document.querySelector('body[data-page="home"] main > section');
if (hero && !reduced.matches) {
  let renderer;
  try { renderer = new THREE.WebGLRenderer({alpha: true, antialias: false}); } catch {}
  if (renderer) {
    const canvas = renderer.domElement;
    canvas.className = 'community-background';
    canvas.setAttribute('aria-hidden', 'true');
    hero.prepend(canvas);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, .1, 50);
    camera.position.z = 12;
    const positions = [];
    for (let i = 0; i < 45; i++) {
      positions.push((Math.random() - .5) * 18, (Math.random() - .5) * 11, (Math.random() - .5) * 2);
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const material = new THREE.PointsMaterial({color: 0xb4d968, size: .07, transparent: true, opacity: .65});
    const points = new THREE.Points(geometry, material);
    scene.add(points);
    const edges = [];
    for (let i = 0; i < positions.length; i += 3) {
      for (let j = i + 3; j < positions.length; j += 3) {
        const distance = Math.hypot(positions[i] - positions[j], positions[i + 1] - positions[j + 1]);
        if (distance < 2.3) edges.push(...positions.slice(i, i + 3), ...positions.slice(j, j + 3));
      }
    }
    const lineGeometry = new THREE.BufferGeometry();
    lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(edges, 3));
    const lineMaterial = new THREE.LineBasicMaterial({color: 0xd3ae56, transparent: true, opacity: .16});
    const lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);
    let visible = true;
    let frame = 0;
    let pointerX = 0;
    let pointerY = 0;
    function resize() {
      renderer.setSize(hero.clientWidth, hero.clientHeight);
      camera.aspect = hero.clientWidth / hero.clientHeight;
      camera.updateProjectionMatrix();
    }
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(hero);
    hero.addEventListener('pointermove', event => {
      const box = hero.getBoundingClientRect();
      pointerX = ((event.clientX - box.left) / box.width - .5) * .12;
      pointerY = ((event.clientY - box.top) / box.height - .5) * .08;
    });
    function animate(time) {
      frame = 0;
      if (!visible || document.hidden || reduced.matches) return;
      points.rotation.y = lines.rotation.y = Math.sin(time * .00008) * .08 + pointerX;
      points.rotation.x = lines.rotation.x = pointerY;
      renderer.render(scene, camera);
      frame = requestAnimationFrame(animate);
    }
    function resume() {
      if (!frame && visible && !document.hidden && !reduced.matches) frame = requestAnimationFrame(animate);
    }
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      if (!visible) { cancelAnimationFrame(frame); frame = 0; }
      else resume();
    });
    observer.observe(hero);
    document.addEventListener('visibilitychange', resume);
    reduced.addEventListener('change', () => {
      canvas.hidden = reduced.matches;
      if (reduced.matches) { cancelAnimationFrame(frame); frame = 0; }
      else resume();
    });
    window.addEventListener('pagehide', () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      resizeObserver.disconnect();
      geometry.dispose();
      material.dispose();
      lineGeometry.dispose();
      lineMaterial.dispose();
      renderer.dispose();
    }, {once: true});
    resize();
    resume();
  }
}

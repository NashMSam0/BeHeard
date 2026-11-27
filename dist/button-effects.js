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

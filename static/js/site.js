/* Campaign site — tiny no-dependency client JS.
   1) Reveal-on-scroll (IntersectionObserver)
   2) Stat counter animation
   3) Election countdown
   4) Mobile nav close-on-click
*/

(function () {
    'use strict';

    const prefersReduced =
        window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    /* ---- Reveal ---- */
    const revealTargets = document.querySelectorAll('.reveal');
    if (revealTargets.length && 'IntersectionObserver' in window && !prefersReduced) {
        const io = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) {
                    e.target.classList.add('is-visible');
                    io.unobserve(e.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
        revealTargets.forEach((el) => io.observe(el));
    } else {
        revealTargets.forEach((el) => el.classList.add('is-visible'));
    }

    /* ---- Stat counters (only when they contain a pure number) ---- */
    function animateNumber(el, target, duration) {
        const start = performance.now();
        const initial = 0;
        function step(now) {
            const t = Math.min(1, (now - start) / duration);
            const eased = 1 - Math.pow(1 - t, 3);
            const v = Math.round(initial + (target - initial) * eased);
            el.textContent = String(v);
            if (t < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }
    const statBs = document.querySelectorAll('.stat [data-count]');
    if (statBs.length && 'IntersectionObserver' in window && !prefersReduced) {
        const io2 = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (!e.isIntersecting) return;
                const el = e.target;
                const raw = el.dataset.count;
                const num = parseInt(raw, 10);
                if (!isNaN(num)) animateNumber(el, num, 1200);
                io2.unobserve(el);
            });
        }, { threshold: 0.3 });
        statBs.forEach((el) => io2.observe(el));
    }

    /* ---- Countdown ---- */
    const cd = document.getElementById('countdown');
    if (cd) {
        const iso = cd.getAttribute('data-target');
        if (iso) {
            const target = new Date(iso + 'T08:00:00').getTime();
            const $ = (k) => cd.querySelector('[data-unit="' + k + '"]');
            const pad = (n) => String(n).padStart(2, '0');
            function tick() {
                const diff = target - Date.now();
                if (diff <= 0) {
                    cd.innerHTML = '<div class="countdown-unit" style="min-width:auto;padding:16px 28px;"><b style="font-size:1.5rem;">اليوم يوم الانتخابات</b></div>';
                    return;
                }
                const d = Math.floor(diff / 86400000);
                const h = Math.floor((diff % 86400000) / 3600000);
                const m = Math.floor((diff % 3600000) / 60000);
                const s = Math.floor((diff % 60000) / 1000);
                const elD = $('d'), elH = $('h'), elM = $('m'), elS = $('s');
                if (elD) elD.textContent = d;
                if (elH) elH.textContent = pad(h);
                if (elM) elM.textContent = pad(m);
                if (elS) elS.textContent = pad(s);
            }
            tick();
            setInterval(tick, 1000);
        }
    }

    /* ---- Close mobile nav on link click ---- */
    const navLinks = document.getElementById('nav-links');
    if (navLinks) {
        navLinks.addEventListener('click', (e) => {
            if (e.target.tagName === 'A') navLinks.classList.remove('open');
        });
    }
})();

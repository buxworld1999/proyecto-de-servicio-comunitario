/**
 * theme-apply.js — PRISMA
 *
 * Se incluye en el <head> de cada módulo (iframe).
 *
 * Hace dos cosas:
 * 1. Al cargar: lee prisma_tema de localStorage y aplica html.dark
 *    ANTES del primer render (sin parpadeo).
 * 2. En tiempo real: escucha mensajes postMessage del padre (menu.html)
 *    para actualizar el tema cuando el usuario hace click en el toggle.
 */

// ── 1. Aplicar tema inicial (síncrono, antes del primer render) ──
(function () {
    try {
        if (localStorage.getItem('prisma_tema') === 'dark') {
            document.documentElement.classList.add('dark');
        }
    } catch (e) { /* localStorage no disponible */ }
})();

// ── 2. Escuchar cambios en tiempo real desde el padre ──
window.addEventListener('message', function (event) {
    try {
        if (event.data && event.data.type === 'prisma_theme') {
            if (event.data.dark) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        }
    } catch (e) { /* no hacer nada */ }
});

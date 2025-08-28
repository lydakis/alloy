/* Initialize Mermaid for MkDocs Material (works with instant navigation) */
(function () {
  function renderMermaid() {
    if (!window.mermaid) return;
    try {
      if (!window.__mermaid_initialized__) {
        window.mermaid.initialize({ startOnLoad: false, securityLevel: 'strict' });
        window.__mermaid_initialized__ = true;
      }
      // Convert <pre><code class="mermaid"> to <div class="mermaid"> for reliability
      document.querySelectorAll('pre > code.mermaid').forEach(function (code) {
        var pre = code.parentElement;
        var div = document.createElement('div');
        div.className = 'mermaid';
        div.textContent = code.textContent;
        pre.parentElement.replaceChild(div, pre);
      });
      if (typeof window.mermaid.run === 'function') {
        window.mermaid.run({ querySelector: '.mermaid' });
      } else if (typeof window.mermaid.init === 'function') {
        window.mermaid.init(undefined, document.querySelectorAll('.mermaid'));
      }
    } catch (e) {
      console.error('Mermaid render error:', e);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderMermaid);
  } else {
    renderMermaid();
  }

  // Re-render on page changes with MkDocs Material
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(renderMermaid);
  }
})();

console.log("focusInput.js загружен");
function setFocusInput(){
    // --- сфокусировать поле ввода и поставить курсор в конец
  function focusMainInput() {
    const container = document.getElementById('main_input');
    if (!container) return;
    // Ищем реальный input/textarea внутри контейнера (или запасные варианты).
    const el =
      container.querySelector('textarea, input') ||
      container.querySelector('[contenteditable="true"]') ||
      document.querySelector('#main_input textarea') ||
      document.querySelector('textarea[placeholder="Введите вопрос..."]');
    if (!el) return;
    // Ставим фокус и переносим курсор в конец
    el.focus();
    try {
      const v = el.value ?? "";
      if (typeof el.setSelectionRange === 'function') {
        el.setSelectionRange(v.length, v.length);
      }
    } catch (_) {}
  }

  // несколько повторов, чтобы попасть после рендеров Gradio, на всякий случай
  // хорошо бы найти способ обойти этот костыль и сделать передачу фокуса гарантированной
  function focusMainInputSoon() {
    [0, 50, 120, 250].forEach((ms) => setTimeout(focusMainInput, ms));
  }

  // 1) фокус при клике на чипы
  document.addEventListener('click', (e) => {
    if (e.target.closest('#chips_row')) focusMainInputSoon();
  });

  // 2) фокус при загрузке
  window.addEventListener('load', () => focusMainInputSoon());

  // 3) Отслеживаем перерисовки DOM через MutationObserver, т.к. градио перерисовывает элементы
  (function observeForFocus() {
    const target = document.body;
    if (!target || !window.MutationObserver) return;
    const observer = new MutationObserver((mutations) => {
      const changed = mutations.some((m) => {
        const added = Array.from(m.addedNodes || []);
        const removed = Array.from(m.removedNodes || []);
        const tid = (m.target && m.target.id) || "";
        return (
          tid === "main_input" || tid === "chips_row" ||
          added.some(n => n.id === "main_input" || n.id === "chips_row") ||
          removed.some(n => n.id === "main_input" || n.id === "chips_row")
        );
      });
      if (changed) focusMainInputSoon();
    });
    // Следим за изменениями структуры и атрибутов
    observer.observe(target, { childList: true, subtree: true, attributes: true });
  })();

  // 4) кнопка «Очистить» — вернуть фокус
  (function wireClearButton() {
    const btn = document.getElementById('clear_chat');
    if (!btn) { setTimeout(wireClearButton, 200); return; }
    let flag = false;
    btn.addEventListener('click', () => {
      btn.style.backgroundColor = flag ? '#000' : '#fff';
      btn.style.color = flag ? '#fff' : '#000';
      flag = !flag;
      focusMainInputSoon();
    });
  })();

  console.info('scripts: focus wiring ready');
}
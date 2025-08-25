// ==== Скрипт приложения с защитой от двойного подключения ====
// Оборачиваем весь код в самовызывающуюся функцию (IIFE), чтобы не засорять глобальную область
(function () {
  // Флаг в window, чтобы не выполнять скрипт повторно (иногда Gradio может вставить скрипт дважды)
  if (window.__customAppScriptLoaded) return;
  window.__customAppScriptLoaded = true;

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

  // === Кастомный вертикальный ресайз для #resizable-chat ===
  (function () {
    // Защита от повторного монтирования ресайзера
    if (window.__chatResizerMounted) return;
    window.__chatResizerMounted = true;

    // Преобразовываем значение вида "320px" в число 320, с запасным значением
    function pxToNum(v, fb) {
      const n = parseFloat(String(v || "").replace("px", ""));
      return Number.isFinite(n) ? n : fb;
    }

    // Основная функция инициализации ресайзера
    function mount() {
      const chat = document.getElementById("resizable-chat");
      if (!chat) return false;

      // Восстанавливаем сохранённую ранее высоту из localStorage (если была)
      const saved = parseFloat(localStorage.getItem("chatHeightPx") || "");
      if (Number.isFinite(saved) && saved > 0) chat.style.height = saved + "px";

      // Создаём ручку под чатом (если ещё нет)
      let handle = document.getElementById("chat-resize-handle");
      if (!handle) {
        handle = document.createElement("div");
        handle.id = "chat-resize-handle";
        chat.insertAdjacentElement("afterend", handle);
      }

      // Считываем CSS-ограничения высоты (min/max) и готовим границы
      const css = getComputedStyle(chat);
      const MIN = pxToNum(css.minHeight, 280);
      const MAX = Math.max(pxToNum(css.maxHeight, window.innerHeight * 0.9), MIN + 100);

      // Локальные переменные для drag-сессии
      let active = false, startY = 0, startH = 0;

      // Обработчик движения указателя: пересчитываем новую высоту чата
      function onMove(e) {
        if (!active) return;
        let h = startH + (e.clientY - startY);
        h = Math.max(MIN, Math.min(MAX, h));
        chat.style.height = h + "px";
      }
      // Завершение перетягивания: снимаем обработчики и сохраняем высоту
      function onUp(e) {
        if (!active) return;
        active = false;
        document.body.classList.remove("resizing-chat");
        handle.releasePointerCapture?.(e.pointerId);
        document.removeEventListener("pointermove", onMove);
        document.removeEventListener("pointerup", onUp);
        const h = chat.getBoundingClientRect().height;
        localStorage.setItem("chatHeightPx", String(Math.round(h)));
      }
      // Старт перетягивания: фиксируем начальные координаты и вешаем обработчики
      handle.addEventListener("pointerdown", (e) => {
        active = true;
        startY = e.clientY;
        startH = chat.getBoundingClientRect().height;
        document.body.classList.add("resizing-chat");
        handle.setPointerCapture?.(e.pointerId);
        document.addEventListener("pointermove", onMove);
        document.addEventListener("pointerup", onUp);
      });

      // Двойной клик по ручке — сбрасываем высоту к значению из CSS
      handle.addEventListener("dblclick", () => {
        chat.style.height = "";           // сброс к 50vh из CSS
        localStorage.removeItem("chatHeightPx");
      });

      console.info("[resizer] mounted");
      return true;
    }

    // Пытаемся смонтировать ресайзер сразу; если чат ещё не отрисован — пробуем позже и следим за DOM
    if (!mount()) {
      setTimeout(mount, 250);
      const t = setInterval(() => { if (mount()) clearInterval(t); }, 400);
      new MutationObserver(() => { mount(); })
        .observe(document.body, { childList: true, subtree: true });
    }
  })();
})();

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
  //=== Симуляция клика по градио элементу  ===
  function simulateClickById(id) {
    const el = document.querySelector("#"+id);
    if (!el) return;
    try {
      el.click();
    } catch (_) {
      el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    }
  }
  // === Скрипт для единого бургер-меню, которое переиспользуется для всех троеточий ===
  (function () {
    // Глобальный синглтон, чтобы защититься от повторного монтирования при двойной вставке скрипта
    window.__verticalEllipsisMenu = window.__verticalEllipsisMenu || {};

    // Создаём (или возвращаем) единый корень меню
    function getMenuRoot() {
      if (window.__verticalEllipsisMenu.root && document.body.contains(window.__verticalEllipsisMenu.root)) {
        return window.__verticalEllipsisMenu.root;
      }
      let root = document.querySelector(".vertical-ellipsis-menu-root");
      if (!root) {
        root = document.createElement("div");
        root.className = "vertical-ellipsis-menu-root";
        Object.assign(root.style, {
          position: "fixed",
          top: "0px",
          left: "0px",
          zIndex: "2147483000",
          pointerEvents: "none",
        });
        document.body.appendChild(root);
      }
      window.__verticalEllipsisMenu.root = root;
      return root;
    }

    // Возвращаем одно общее меню (создаём единожды)
    function getSharedMenu() {
      if (window.__verticalEllipsisMenu.menu && document.body.contains(window.__verticalEllipsisMenu.menu)) {
        return window.__verticalEllipsisMenu.menu;
      }

      const root = getMenuRoot();
      let menu = root.querySelector(".vertical-ellipsis-menu-shared");
      if (!menu) {
        menu = document.createElement("div");
        menu.className = "vertical-ellipsis-menu-shared";
        Object.assign(menu.style, {
          position: "absolute",
          pointerEvents: "auto",
          minWidth: "160px",
          background: "#fff",
          color: "#111",
          borderRadius: "8px",
          boxShadow: "0 6px 18px rgba(0,0,0,0.12)",
          padding: "6px",
          fontSize: "13px",
          transformOrigin: "left center",
          display: "none",
        });

        // Пример пункта меню — Переименовать чат
        const renameBtn = document.createElement("button");
        renameBtn.type = "button";
        renameBtn.textContent = "Переименовать чат";
        renameBtn.id = "rename_chat";
        Object.assign(renameBtn.style, {
          display: "block",
          width: "100%",
          textAlign: "left",
          padding: "8px 10px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          borderRadius: "6px",
        });
        renameBtn.addEventListener("mouseenter", () => renameBtn.style.background = "rgba(0,0,0,0.03)");
        renameBtn.addEventListener("mouseleave", () => renameBtn.style.background = "transparent");
        const deleteBtn = document.createElement("button");
        deleteBtn.type = "button";
        deleteBtn.textContent = "Удалить чат";
        deleteBtn.id = "delete_chat";
        Object.assign(deleteBtn.style, {
          display: "block",
          width: "100%",
          textAlign: "left",
          padding: "8px 10px",
          background: "transparent",
          border: "none",
          cursor: "pointer",
          borderRadius: "6px",
        });
        deleteBtn.addEventListener("mouseenter", () => deleteBtn.style.background = "rgba(0,0,0,0.03)");
        deleteBtn.addEventListener("mouseleave", () => deleteBtn.style.background = "transparent");
        // Запоминаем целевой label при клике на меню
        document.addEventListener('click', (e) => {
          const vBtn = e.target.closest('.vertical-ellipsis-btn');
          if (vBtn) window.__renameTargetLabel = vBtn.closest('label.svelte-1bx8sav') || null;
        }, true);

        window.__currentEditing = null;

        renameBtn.addEventListener("click", () => {
          let label = window.__renameTargetLabel
                  || document.querySelector('label.svelte-1bx8sav.selected')
                  || document.querySelector('label.svelte-1bx8sav');
          if (!label) return hideAllMenus();

          if (window.__currentEditing) {
            const prev = window.__currentEditing;
            document.removeEventListener('keydown', prev.keydownHandler, true);
            document.removeEventListener('click', prev.outsideClickHandler, true);
            prev.input.remove();
            prev.span.style.display = '';
            window.__currentEditing = null;
          }

          const span = label.querySelector('span.svelte-1bx8sav');
          if (!span) return hideAllMenus();

          const originalText = span.textContent;
          const input = document.createElement('input');
          input.type = 'text';
          input.value = originalText;
          input.className = 'inline-rename-input';

          const spanStyle = window.getComputedStyle(span);
          input.style.font = spanStyle.font;
          input.style.fontSize = spanStyle.fontSize;
          input.style.lineHeight = spanStyle.lineHeight;
          input.style.padding = '0 4px';
          input.style.border = '1px solid rgba(0,0,0,0.2)';
          input.style.borderRadius = '4px';
          input.style.background = 'transparent';
          input.style.outline = 'none';
          span.style.display = 'none';
          span.insertAdjacentElement('afterend', input);

          // авто-подгон ширины
          const adjustWidth = () => {
            input.style.width = Math.max(80, input.value.length * 8 + 20) + 'px';
          };
          adjustWidth();

          input.addEventListener('input', adjustWidth);
          input.focus();
          input.setSelectionRange(input.value.length, input.value.length);

          const state = { label, span, input, originalText };
          window.__currentEditing = state;

          function finish(save) {
            document.removeEventListener('keydown', state.keydownHandler, true);
            document.removeEventListener('click', state.outsideClickHandler, true);
            state.span.textContent = save ? state.input.value : state.originalText;
            state.input.remove();
            state.span.style.display = '';
            window.__renameTargetLabel = null;
            window.__currentEditing = null;
            if(save){
              const grInput = document.querySelector("#gr_rename_box textarea, #gr_rename_box input");
              grInput.value = state.input.value;
              grInput.dispatchEvent(new Event('input', { bubbles: true }));
              grInput.dispatchEvent(new Event('change', { bubbles: true }));
              grInput.focus();
              grInput.blur();
              simulateClickById("gr_rename_chat");
            }
            focusMainInput();
          }

          state.keydownHandler = function (e) {
            if (e.key === 'Escape') { e.preventDefault(); finish(false); }
            if (e.key === 'Enter') { e.preventDefault(); finish(true); }
          };

          state.outsideClickHandler = function (e) {
            if (state.input.contains(e.target) || state.label.contains(e.target)) return;
            e.stopPropagation();
            const ok = confirm('Вы не закончили действие');
            if (ok) {
              e.preventDefault();
              state.input.focus();
              state.input.setSelectionRange(state.input.value.length, state.input.value.length);
            } else {
              finish(false); // теперь Cancel сразу завершает редактирование
            }
          };

          document.addEventListener('keydown', state.keydownHandler, true);
          document.addEventListener('click', state.outsideClickHandler, true);
          
          hideAllMenus();
        });
        deleteBtn.addEventListener("click", () => {
            simulateClickById("gr_delete_chat");
            focusMainInput();
        });
        menu.appendChild(renameBtn);
        menu.appendChild(deleteBtn);
        root.appendChild(menu);
      }

      window.__verticalEllipsisMenu.menu = menu;
      return menu;
    }

    // Скрыть меню (не удаляя)
    function hideAllMenus() {
      const menu = getSharedMenu();
      if (!menu) return;
      try { menu._cleanup?.(); } catch (_) {}
      menu._cleanup = null;
      menu.style.display = "none";
      menu._visible = false;
      menu._anchor = null;
    }

    // Позиционируем и показываем общее меню рядом с кнопкой
    function openSharedMenuFor(btn) {
      const menu = getSharedMenu();
      hideAllMenus();
      menu.style.display = "block";
      menu.style.visibility = "hidden"; // чтобы измерить
      menu._anchor = btn;

      const btnRect = btn.getBoundingClientRect();
      const mRect = menu.getBoundingClientRect();
      const margin = 8;
      const GAP = 8;

      let left = btnRect.right + GAP;
      let placeRight = true;
      if (left + mRect.width > window.innerWidth - margin) {
        left = btnRect.left - mRect.width - GAP;
        placeRight = false;
      }
      if (left < margin) left = margin;
      if (left + mRect.width > window.innerWidth - margin) left = Math.max(margin, window.innerWidth - mRect.width - margin);

      let top = btnRect.top + (btnRect.height - mRect.height) / 2;
      if (top < margin) top = margin;
      if (top + mRect.height > window.innerHeight - margin) top = Math.max(margin, window.innerHeight - mRect.height - margin);

      menu.style.left = `${left}px`;
      menu.style.top = `${top}px`;
      menu.style.visibility = "visible";
      menu.style.transformOrigin = placeRight ? "left center" : "right center";
      menu._visible = true;

      function onDocClick(e) { if (!menu.contains(e.target) && e.target !== btn) hideAllMenus(); }
      function onKeyDown(ev) { if (ev.key === "Escape") hideAllMenus(); }
      function onScrollOrResize() { hideAllMenus(); }

      menu._cleanup = function () {
        document.removeEventListener("click", onDocClick);
        document.removeEventListener("keydown", onKeyDown);
        window.removeEventListener("resize", onScrollOrResize);
        window.removeEventListener("scroll", onScrollOrResize, true);
      };

      setTimeout(() => {
        document.addEventListener("click", onDocClick);
        document.addEventListener("keydown", onKeyDown);
        window.addEventListener("resize", onScrollOrResize);
        window.addEventListener("scroll", onScrollOrResize, true);
      }, 0);
    }

    // Создаём кнопку рядом с меткой (если ещё нет)
    function createButtonForLabel(label) {
      // метка уже обработана — не добавляем вторую кнопку
      if (label.dataset.__ellipsisProcessed === "1") return;
      // если внутри уже есть кнопка с таким классом — тоже не добавляем
      if (label.querySelector(".vertical-ellipsis-btn")) {
        label.dataset.__ellipsisProcessed = "1";
        return;
      }

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "vertical-ellipsis-btn";
      btn.setAttribute("aria-label", "Меню");
      btn.title = "Меню";
      btn.style.border = "none";
      btn.style.background = "transparent";
      btn.style.cursor = "pointer";
      btn.style.padding = "4px";
      btn.style.marginLeft = "6px";
      btn.style.fontSize = "18px";
      btn.style.lineHeight = "1";
      btn.textContent = "⋮";
      // Генерируем уникальный id для каждой кнопки
      // Используем crypto.randomUUID() если доступен, иначе простой инкремент + случайная часть
      if (!window.__verticalEllipsisMenu._idCounter) window.__verticalEllipsisMenu._idCounter = 0;
      const counterPart = ++window.__verticalEllipsisMenu._idCounter;
      const randomPart = (typeof crypto !== "undefined" && crypto.randomUUID)
      ? crypto.randomUUID().slice(0, 8)
      : Math.random().toString(36).slice(2, 8);
      btn.id = `vertical-ellipsis-btn-${counterPart}-${randomPart}`;
      
      label.appendChild(btn);
      label.dataset.__ellipsisProcessed = "1";

      btn.addEventListener("click", (e) => {
        //simulateClickById("gr_burger")
        e.stopPropagation();
        const label = btn.closest('.svelte-1bx8sav');
        const radioInput = label.querySelector('input[type="radio"]');
        if (radioInput) {
            radioInput.checked = true;
            
            // Также можно вызвать события для обновления состояния
            radioInput.dispatchEvent(new Event('change', { bubbles: true }));
            radioInput.dispatchEvent(new Event('click', { bubbles: true }));
        }
        const menu = getSharedMenu();
        if (menu && menu._visible && menu._anchor === btn) {
          hideAllMenus();
        } else {
          openSharedMenuFor(btn);
        }
      });
    }

    // Находим целевые метки и прикрепляем кнопку (с маркировкой, чтобы не дублировать)
    function processAllLabels() {
      const labels = document.querySelectorAll("label.svelte-1bx8sav");
      if (!labels || labels.length === 0) return false;
      labels.forEach(createButtonForLabel);
      return true;
    }

    // Начальная попытка, с отложенной пробой
    if (!processAllLabels()) setTimeout(processAllLabels, 200);

    // Наблюдатель — debounce и повторная обработка, но createButtonForLabel защищает от дублей
    let scheduled = null;
    const mo = new MutationObserver(() => {
      if (scheduled) return;
      scheduled = setTimeout(() => {
        scheduled = null;
        processAllLabels();
      }, 120);
    });
    mo.observe(document.body, { childList: true, subtree: true });

    window.addEventListener("beforeunload", () => { hideAllMenus(); });
  })();
  
})();

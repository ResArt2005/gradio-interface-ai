console.log("burgerMenu.js загружен");
function setBurgerMenu(){
  simulateClickById = setSimulateClickById();
  const Btn_Rename = set_Btn_Rename();
  const Btn_Delete = set_Btn_Delete();
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
        menu.appendChild(Btn_Rename);
        menu.appendChild(Btn_Delete);
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
}
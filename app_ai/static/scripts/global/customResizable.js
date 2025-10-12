console.log("CustomResizable.js загружен");
function setCustomResizable(){
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

}
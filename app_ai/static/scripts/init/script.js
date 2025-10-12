// ==== Скрипт приложения с защитой от двойного подключения ====
// Оборачиваем весь код в самовызывающуюся функцию (IIFE), чтобы не засорять глобальную область
(function () {
  // Флаг в window, чтобы не выполнять скрипт повторно (иногда Gradio может вставить скрипт дважды)
  if (window.__customAppScriptLoaded) return;
  window.__customAppScriptLoaded = true;
  console.log("script.js загружен");
  setFocusInput();
  setCustomResizable();
  setBurgerMenu();
})();

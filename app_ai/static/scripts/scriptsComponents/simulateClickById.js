console.log("simulateClickById.js загружен");
//=== Симуляция клика по градио элементу  ===
function setSimulateClickById(){
    function simulateClickById(id) {
        const el = document.querySelector("#"+id);
        if (!el) return;
            el.click();
        try {
        } catch (_) {
            el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        }
  }
  return simulateClickById;
}
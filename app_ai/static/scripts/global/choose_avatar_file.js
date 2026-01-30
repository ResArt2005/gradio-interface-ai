console.log("choose_avatar_file.js загружен");
function set_choose_avatar_file() {
    (function () {
        const fileInput = document.querySelector('#avatar_upload input[type="file"]');
        if (fileInput) {
            // Устанавливаем правильный accept для фильтрации в проводнике
            fileInput.accept = "image/png,image/jpeg,.png,.jpg,.jpeg";
        }
    })();
}

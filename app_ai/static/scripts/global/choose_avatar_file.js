console.log("choose_avatar_file.js загружен");
function set_choose_avatar_file() {
    const observer = new MutationObserver(() => {
    const input = document.querySelector(
        'input[type="file"][data-testid="file-upload"]'
    );

    if (input && input.accept !== ".png,.jpg,.jpeg") {
        input.accept = ".png,.jpg,.jpeg";
        console.log("accept заменён");
    }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
}

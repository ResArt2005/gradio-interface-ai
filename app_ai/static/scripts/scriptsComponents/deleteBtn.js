console.log("deleteBtn.js загружен");
function setDeleteBtn(){
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
        
        deleteBtn.addEventListener("click", () => {
            simulateClickById("gr_delete_chat");
            focusMainInput();
        });
    return deleteBtn;
}
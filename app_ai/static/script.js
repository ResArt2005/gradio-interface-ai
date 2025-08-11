const button = document.getElementById("clear_chat");
flag = false
console.log("Скрипты загружены")
button.addEventListener("click", function() {
    this.style.backgroundColor = flag ? "#000" : "#fff";
    this.style.color = flag ? "#fff" : "#000";
    flag = flag ? false:true;
})
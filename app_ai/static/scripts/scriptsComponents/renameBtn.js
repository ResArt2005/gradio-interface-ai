console.log("renameBtn.js загружен");
function setRenameBtn(){
        // Переименовать чат
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
          function truncateText(text) {
            if (text.length > 50) {
              return text.substring(0, 47) + '...';
            }
            return text;
          }
          function validateAndFinish(save) {
            // Проверка на пустое название или название из пробелов
            if (save && (!state.input.value.trim() || state.input.value.trim() === '')) {
              const shouldContinue = confirm('Пустое название\n\nВы хотите продолжить редактирование?');
              if (shouldContinue) {
                // Пользователь нажал "OK" - возвращаем к редактированию
                state.input.focus();
                state.input.setSelectionRange(0, state.input.value.length);
                return false; // не завершаем редактирование
              } else {
                // Пользователь нажал "Отмена" - отменяем редактирование
                finish(false);
                return true; // завершаем редактирование
              }
            }
            
            // Если проверка пройдена или save=false, завершаем редактирование
            finish(save);
            return true;
          }

          function finish(save) {
            document.removeEventListener('keydown', state.keydownHandler, true);
            document.removeEventListener('click', state.outsideClickHandler, true);            
            state.input.remove();
            state.span.style.display = '';
            window.__renameTargetLabel = null;
            window.__currentEditing = null;
            
            if(save){
              const finalText = truncateText(state.input.value.trim());
              const grInput = document.querySelector("#gr_rename_box textarea, #gr_rename_box input");
              grInput.value = finalText;
              grInput.dispatchEvent(new Event('input', { bubbles: true }));
              grInput.dispatchEvent(new Event('change', { bubbles: true }));
              grInput.focus();
              grInput.blur();
              simulateClickById("gr_rename_chat");
            }
            focusMainInput();
          }

          state.keydownHandler = function (e) {
            if (e.key === 'Escape') { 
              e.preventDefault(); 
              finish(false); 
            }
            if (e.key === 'Enter') { 
              e.preventDefault(); 
              validateAndFinish(true); 
            }
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
              finish(false);
            }
          };

          document.addEventListener('keydown', state.keydownHandler, true);
          document.addEventListener('click', state.outsideClickHandler, true);
          
          hideAllMenus();
        });
        return renameBtn;
}
import gradio as gr
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import uuid

# --- ЛОГИКА ПРИЛОЖЕНИЯ (АДАПТИРОВАНА ПОД НОВЫЙ ФОРМАТ ДАННЫХ) ---
FASTAPI_URL = "http://host.docker.internal:8000/query"

def format_message(content):
    # Упрощаем функцию, так как роль передается отдельно
    return content

def add_user_message(message, chat_id, chat_sessions, chat_titles):
    if not message.strip():
        active_title = next((title for title, cid in chat_titles if cid == chat_id), None)
        history = chat_sessions.get(chat_id, [])
        return "", history, chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles], value=active_title)
    if chat_id not in chat_sessions:
        chat_sessions[chat_id] = []
        title = f"Новый запрос"
        chat_titles.insert(0, (title, chat_id))
    # ИЗМЕНЕНО: Используем формат словаря {'role': 'user', 'content': ...}
    user_msg = {"role": "user", "content": format_message(message)}
    chat_sessions[chat_id].append(user_msg)
    value = None
    if len(chat_sessions[chat_id]) == 1:
        short_title = " ".join(message.strip().split()[:4]) + ("..." if len(message.strip().split()) > 4 else "")
        chat_titles = [(short_title if cid == chat_id else title, cid) for title, cid in chat_titles]
        value = short_title
    active_title = next((title for title, cid in chat_titles if cid == chat_id), None)
    return "", chat_sessions[chat_id], chat_sessions, chat_titles, gr.update(
        choices=[t[0] for t in chat_titles],
        value=value or active_title
    )

def fetch_llm_answer(_, chat_id, chat_sessions):
    if chat_id not in chat_sessions:
        return [{"role": "assistant", "content": "Ошибка: Чат не найден."}], chat_sessions
    history = chat_sessions[chat_id]
    try:
        # ИЗМЕНЕНО: Извлекаем контент из словаря
        last_user_msg = history[-1]['content']
        # Исправляем URL для локального запуска (если нужно)
        api_url = FASTAPI_URL.replace("host.docker.internal", "localhost") if "host.docker.internal" in FASTAPI_URL else FASTAPI_URL
        response = requests.post(api_url, json={'query': last_user_msg}, timeout=180)
        response.raise_for_status()
        data = response.json()
        answer = data.get('answer', 'Ответ не получен')
        sources = data.get('sources', [])
    except requests.exceptions.RequestException as e:
        answer = f'Ошибка сети или сервера: {e}'
        sources = []
    except Exception as e:
        answer = f'Произошла ошибка: {e}'
        sources = []
    formatted_answer = format_message(answer)
    if sources:
        formatted_answer += '<details><summary>📎 <b>Источники</b></summary>'
        for i, src in enumerate(sources, 1):
            title = src.get('doc_title', 'Источник')
            page = src.get('page', '')
            snippet = src.get('snippet', '')
            url = src.get('url', '#')
            formatted_answer += f'• <a href="{url}" target="_blank" rel="noopener noreferrer">{title}, стр. {page}</a>'
            formatted_answer += f'> {snippet.strip()}'
        formatted_answer += '</details>'
    # ИЗМЕНЕНО: Добавляем ответ в формате словаря
    chat_sessions[chat_id].append({'role': 'assistant', 'content': formatted_answer})
    return chat_sessions[chat_id], chat_sessions

def new_chat(chat_sessions, chat_titles):
    new_id = str(uuid.uuid4())
    chat_sessions[new_id] = []
    title = f"Новый запрос"
    chat_titles.insert(0, (title, new_id))
    return new_id, [], chat_sessions, chat_titles, gr.update(choices=[t[0] for t in chat_titles], value=title)

def switch_chat(title, chat_titles, chat_sessions):
    for t, cid in chat_titles:
        if t == title:
            return cid, chat_sessions.get(cid, [])
    return gr.update(), []

def rename_chat(new_title, current_chat_id, chat_titles):
    if not new_title.strip(): return chat_titles, gr.update(), ""
    chat_titles = [(new_title if cid == current_chat_id else title, cid) for title, cid in chat_titles]
    return (
        chat_titles,
        gr.update(choices=[t[0] for t in chat_titles], value=new_title),
        ""
    )

# --- СТИЛИ И ИНТЕРФЕЙС (С ИСПРАВЛЕНИЯМИ) ---
custom_css = """
body, #component-0 { background-color: #f5f5f5 !important; font-family: 'Inter', sans-serif; }
.gradio-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; height: 100vh; overflow: hidden; }
.main-container { display: flex; height: 100vh; width: 100%; margin: 0; padding: 0; gap: 0; }
.sidebar {
    background-color: #f8f9fa; /* Изменен фон */
    padding: 20px 15px !important; 
    color: #333;
    min-width: 280px; 
    max-width: 320px;
    border-right: 1px solid #dee2e6;
    display: flex; 
    flex-direction: column; 
    gap: 15px;
}
/* Стили для кнопки нового запроса */
.sidebar .gradio-button { background-color: #0056b3; color: white; border: 1px solid #0069d9; border-radius: 8px; transition: background-color 0.2s; }
.sidebar .gradio-button:hover { background-color: #0069d9; }
/* Стили для радио кнопок */
.sidebar label.gradio-label { color: #e0e0e0 !important; font-size: 1rem; margin-bottom: 10px; }
.sidebar .gradio-radio .radio-group { display: flex; flex-direction: column; gap: 8px; }
.sidebar .gradio-radio label { display: block; padding: 10px 15px; background-color: #0056b3; border-radius: 8px; cursor: pointer; transition: background-color 0.2s; }
.sidebar .gradio-radio input[type="radio"]:checked + label { background-color: #007bff; font-weight: bold; }
.sidebar .gradio-textbox { background-color: #f8f9fa; border-radius: 8px; }

.chat-area {
    background-color: #f8f9fa; /* Серый фон */
    padding: 0 20px !important; 
    display: flex; 
    flex-direction: column; 
    height: 100vh; 
    box-sizing: border-box;
}

#chatbot {
    flex-grow: 1; 
    overflow-y: auto; 
    background-color: transparent; 
    border: none !important;
    box-shadow: none !important; 
    padding: 20px 0;
}
#chatbot .message-bubble-row { justify-content: flex-start; }
#chatbot .message-bubble { padding: 12px 18px !important; border-radius: 18px !important; max-width: 80%; line-height: 1.5; }
#chatbot .message-bubble.user { background-color: #e9ecef !important; color: #333 !important; align-self: flex-end; }
#chatbot .message-bubble.bot { background-color: #ffffff !important; color: #333 !important; align-self: flex-start; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }

.input-section { flex-shrink: 0; padding: 15px 0; }
.suggestions-container { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; }
.suggestion-btn {
    background-color: #e7f1ff !important; 
    color: #0056b3 !important; 
    border-radius: 20px !important; 
    border: 1px solid #cce0ff !important;
    padding: 6px 14px !important; 
    font-size: 0.9rem !important; 
    font-weight: 500 !important; 
    min-height: 0 !important;
}
.suggestion-btn:hover { background-color: #d0e0ff !important; }

.input-container {
    background-color: white; 
    border-radius: 12px; 
    padding: 8px !important; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border: 1px solid #dee2e6; 
    display: flex; 
    align-items: center;
}
.input-container .gradio-textbox { border: none !important; box-shadow: none !important; background-color: transparent !important; }
.input-container .gradio-button {
    background-color: #007bff !important; 
    color: white !important; 
    min-width: 100px !important;
    border-radius: 8px !important; 
    border: none !important;
}
.input-container .gradio-button:hover { background-color: #0056b3 !important; }

/* Стили для меню настроек */
.gradio-settings-menu {
    top: 60px !important; 
    right: 20px !important; 
    background: #ffffff !important; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
    border-radius: 8px;
}
"""

with gr.Blocks(css=custom_css) as interface:
    chat_sessions = gr.State({})
    current_chat_id = gr.State(str(uuid.uuid4()))
    chat_titles = gr.State([])
    
    with gr.Row(elem_classes="main-container"):
        with gr.Column(scale=1, elem_classes="sidebar"):
            gr.Markdown("## 💬 **Ассистент**")
            new_chat_btn = gr.Button("➕ Новый запрос")
            chat_list = gr.Radio(choices=[], label="История", interactive=True)
            rename_box = gr.Textbox(placeholder="Переименовать запрос...", lines=1, show_label=False)
            rename_btn = gr.Button("Переименовать")
        
        with gr.Column(scale=4, elem_classes="chat-area"):
            gr.Markdown("### Ваш вопрос", elem_classes="question-header")  # Добавлен заголовок
            chatbot = gr.Chatbot(label="Диалог", render_markdown=True, elem_id="chatbot", type="messages")
            
            with gr.Column(elem_classes="input-section"):
                with gr.Row(elem_classes="suggestions-container"):
                    suggestion_1 = gr.Button("Кто итоговый исполнитель...", elem_classes="suggestion-btn")
                    suggestion_2 = gr.Button("Напиши краткое содержание документа...", elem_classes="suggestion-btn")
                    suggestion_3 = gr.Button("На основании какого документа...", elem_classes="suggestion-btn")
                
                with gr.Row(elem_classes="suggestions-container"):
                    suggestion_4 = gr.Button("Покажи все документы связанные с...", elem_classes="suggestion-btn")
                    suggestion_5 = gr.Button("От какого числа...", elem_classes="suggestion-btn")
                    suggestion_6 = gr.Button("Определи из документа...", elem_classes="suggestion-btn")
                
                with gr.Row(elem_classes="input-container"):
                    textbox = gr.Textbox(
                        placeholder="Составьте вопрос с конструктором или напишите свой",
                        lines=1,
                        show_label=False,
                        scale=10
                    )
                    submit_btn = gr.Button("Отправить", scale=1)

    # --- Привязка логики к элементам интерфейса (без изменений) ---
    def fill_textbox(text):
        return gr.update(value=text)
    
    suggestion_1.click(fn=fill_textbox, inputs=[suggestion_1], outputs=[textbox])
    suggestion_2.click(fn=fill_textbox, inputs=[suggestion_2], outputs=[textbox])
    suggestion_3.click(fn=fill_textbox, inputs=[suggestion_3], outputs=[textbox])
    suggestion_4.click(fn=fill_textbox, inputs=[suggestion_4], outputs=[textbox])
    suggestion_5.click(fn=fill_textbox, inputs=[suggestion_5], outputs=[textbox])
    suggestion_6.click(fn=fill_textbox, inputs=[suggestion_6], outputs=[textbox])
    
    textbox.submit(
        add_user_message,
        [textbox, current_chat_id, chat_sessions, chat_titles],
        [textbox, chatbot, chat_sessions, chat_titles, chat_list]
    ).then(
        fetch_llm_answer,
        [textbox, current_chat_id, chat_sessions],
        [chatbot, chat_sessions]
    )
    
    submit_btn.click(
        add_user_message,
        [textbox, current_chat_id, chat_sessions, chat_titles],
        [textbox, chatbot, chat_sessions, chat_titles, chat_list]
    ).then(
        fetch_llm_answer,
        [textbox, current_chat_id, chat_sessions],
        [chatbot, chat_sessions]
    )
    
    new_chat_btn.click(
        new_chat,
        [chat_sessions, chat_titles],
        [current_chat_id, chatbot, chat_sessions, chat_titles, chat_list]
    )
    
    chat_list.change(
        switch_chat,
        [chat_list, chat_titles, chat_sessions],
        [current_chat_id, chatbot]
    )
    
    rename_btn.click(
        rename_chat,
        [rename_box, current_chat_id, chat_titles],
        [chat_titles, chat_list, rename_box]
    )
    
    interface.load(
        lambda: new_chat({}, []),
        None,
        [current_chat_id, chatbot, chat_sessions, chat_titles, chat_list]
    )

if __name__ == "__main__":
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        auth=("user", "password"),  # Раскомментируйте для аутентификации
    )
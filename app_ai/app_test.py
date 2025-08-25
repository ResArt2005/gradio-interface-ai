import gradio as gr
from ui.layout import build_interface

if __name__ == "__main__":
    interface = build_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        # auth=("user", "password")  # при необходимости
    )

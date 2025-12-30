from components.prompt_tree import (
    chip_click
)
import gradio as gr
from ui.UI import UI
def chip_buttons(ui:UI):
    for i, btn in enumerate(ui.chip_buttons):
        btn.click(
            chip_click,
            inputs=[gr.State(i), ui.current_nodes, ui.top_tree_state, ui.suppress_reset, ui.textbox],
            outputs=[ui.textbox, *ui.chip_buttons, ui.current_nodes, ui.suppress_reset]
        )
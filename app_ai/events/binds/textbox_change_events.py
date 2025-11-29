from ui.UI import UI
from events.events import on_textbox_change
def textbox_change_events(ui:UI):
    ui.textbox.change(
        on_textbox_change,
        inputs=[ui.textbox, ui.current_nodes, ui.suppress_reset, ui.top_tree_state],
        outputs=[*ui.chip_buttons, ui.current_nodes, ui.suppress_reset]
    )
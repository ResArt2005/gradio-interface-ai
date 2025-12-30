from layout.layout import build_interface
from tools.debug import logger

if __name__ == "__main__":
    interface = build_interface()
    logger.info("Launching Gradio interface (auth via PostgreSQL)...")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_api=False,
        share=False,
        allowed_paths=["/app/media"]
    )

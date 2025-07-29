import json
import logging
import os

logger = logging.getLogger(__name__)


def save_outputs(output_base: str, markdown_content: str, context_data: dict):
    """Saves generated content to `output/<output_base>/`."""
    try:
        output_dir = os.path.join("output", output_base)
        os.makedirs(output_dir, exist_ok=True)
        md_filename = os.path.join(output_dir, f"{output_base}.md")
        json_filename = os.path.join(output_dir, f"{output_base}_context.json")
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Successfully created content file: {md_filename}")
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully created context file: {json_filename}")
    except IOError as e:
        raise IOError(f"Could not write to output directory '{output_dir}'. Please check permissions. Error: {e}")
    except Exception:
        logger.exception("An unexpected error occurred during file output:")
        raise

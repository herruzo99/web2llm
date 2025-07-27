"""Handles the creation of output files and directories."""

import json
import os
import sys

def save_outputs(output_base: str, markdown_content: str, context_data: dict):
    """
    Saves the generated content to a dedicated output folder.

    Creates a directory `output/<output_base>/` and writes the main
    markdown content and the JSON context file inside it.

    Args:
        output_base: The base name for the output folder and files.
        markdown_content: The string content for the .md file.
        context_data: The dictionary content for the .json file.
    """
    try:
        output_dir = os.path.join("output", output_base)
        os.makedirs(output_dir, exist_ok=True)

        md_filename = os.path.join(output_dir, f"{output_base}.md")
        json_filename = os.path.join(output_dir, f"{output_base}_context.json")

        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Successfully created content file: {md_filename}")

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)
        print(f"Successfully created context file: {json_filename}")

    except IOError as e:
        raise IOError(f"Could not write to output directory '{output_dir}'. Please check permissions. Original error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during file output: {e}", file=sys.stderr)
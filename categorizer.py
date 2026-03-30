"""Use Claude API to categorize files based on name and metadata."""

import anthropic

from config import ANTHROPIC_API_KEY, CATEGORIES


def categorize_files(files: list[dict]) -> dict[str, str]:
    """Categorize a batch of files using Claude.

    Args:
        files: List of file dicts with 'id', 'name', 'mimeType', etc.

    Returns:
        Dict mapping file ID to category name.
    """
    if not files:
        return {}

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    categories_str = ", ".join(CATEGORIES)

    file_descriptions = []
    for f in files:
        desc = f"- {f['name']} (type: {f.get('mimeType', 'unknown')}"
        if f.get("size"):
            desc += f", size: {f['size']} bytes"
        if f.get("path"):
            desc += f", folder: {f['path']}"
        desc += ")"
        file_descriptions.append(desc)

    file_list = "\n".join(file_descriptions)

    # Process in batches to stay within token limits
    results = {}
    batch_size = 50
    for i in range(0, len(files), batch_size):
        batch = files[i : i + batch_size]
        batch_descriptions = file_descriptions[i : i + batch_size]
        batch_list = "\n".join(batch_descriptions)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Categorize each file into exactly one of these categories: {categories_str}\n\n"
                        f"Files:\n{batch_list}\n\n"
                        "Respond with ONLY one line per file in this exact format:\n"
                        "filename.ext|Category\n\n"
                        "Use 'Other' if a file doesn't clearly fit any category."
                    ),
                }
            ],
        )

        response_text = message.content[0].text
        for line in response_text.strip().splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            filename, category = line.rsplit("|", 1)
            filename = filename.strip()
            category = category.strip()

            if category not in CATEGORIES:
                category = "Other"

            for f in batch:
                if f["name"] == filename:
                    results[f["id"]] = category
                    break

    # Ensure every file has a category
    for f in files:
        if f["id"] not in results:
            results[f["id"]] = "Other"

    return results

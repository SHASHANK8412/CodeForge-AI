import re


def optimize_prompt(prompt: str) -> str:
    """
    Optimizes the prompt content before sending it to Ollama.
    - Trims unnecessary whitespace and consecutive blank lines.
    - Identifies and filters out empty sections.
    - Deduplicates identical sections.
    - Preserves system prompts as they are not passed to this function.
    """
    if not prompt or not prompt.strip():
        return ""

    # Split prompt into sections using common dividers/headers
    section_pattern = re.compile(
        r"(^(?:Project Context|Conversation History|Project Status|Project Snapshot|"
        r"Relevant Memory|Current Task|Current Prompt|Planner Output|Architect Output|"
        r"Previous Messages|Previous Agent Output|Recent History|=== [A-Z ]+ ===|### [a-zA-Z0-9_ ]+)\b:?\s*\n)",
        re.MULTILINE
    )

    parts = section_pattern.split(prompt)
    
    # If no headers detected, clean up lines and return
    if len(parts) <= 1:
        lines = [line.strip() for line in prompt.splitlines()]
        cleaned_lines = []
        for line in lines:
            if line:
                cleaned_lines.append(line)
            elif cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
        return "\n".join(cleaned_lines).strip()

    optimized_sections: list[tuple[str, str]] = []
    seen_section_contents: set[str] = set()

    # The first part is text before any heading
    initial_text = parts[0].strip()
    if initial_text:
        optimized_sections.append(("", initial_text))

    # Iterate through heading and body pairs
    for i in range(1, len(parts), 2):
        heading = parts[i].strip()
        body = parts[i+1].strip() if i+1 < len(parts) else ""
        
        body_lines = [line.strip() for line in body.splitlines()]
        cleaned_body_lines = []
        for line in body_lines:
            if line:
                cleaned_body_lines.append(line)
            elif cleaned_body_lines and cleaned_body_lines[-1] != "":
                cleaned_body_lines.append("")
        cleaned_body = "\n".join(cleaned_body_lines).strip()

        # Filter empty sections, or sections containing only placeholders
        is_empty_marker = cleaned_body.lower() in {
            "none",
            "no relevant memory found.",
            "no previous conversation history.",
            "not set",
        }
        
        if not cleaned_body or is_empty_marker:
            continue

        # Deduplicate identical section contents to save tokens
        norm_body = re.sub(r"\s+", "", cleaned_body).lower()
        if norm_body in seen_section_contents:
            continue
        seen_section_contents.add(norm_body)

        optimized_sections.append((heading, cleaned_body))

    # Reconstruct the optimized prompt
    result_parts = []
    for heading, body in optimized_sections:
        if heading:
            result_parts.append(f"{heading}\n{body}")
        else:
            result_parts.append(body)

    return "\n\n".join(result_parts).strip()

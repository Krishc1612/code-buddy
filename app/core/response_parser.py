import re
from typing import Optional
from pydantic import BaseModel


# ============================================================
# SECTION 1: THE DATA MODEL
# ============================================================
# ParsedResponse is a Pydantic model — think of it as a
# structured container that holds each section of the LLM's
# response as a separate field instead of one big string.
#
# Why Pydantic?
# - You already use it in chat.py, messages.py, user.py
# - It validates types automatically
# - It converts directly to JSON for your API responses
# - Frontend gets clean structured data, not a markdown blob
#
# Why Optional[str] for everything?
# - Teaching mode (no code given) won't have bug_analysis etc.
# - Code review mode won't have teaching_content
# - Parser should never crash if a section is missing
# ============================================================

class ParsedResponse(BaseModel):

    # --- Code review fields (present when user sends code) ---
    bug_analysis: Optional[str] = None
    # example: "The recursive call uses n instead of n-1..."

    complexity: Optional[str] = None
    # example: "Time: O(n), Space: O(n) due to call stack"

    code_improvements: Optional[str] = None
    # example: "Add a check for negative numbers..."

    knowledge_gaps: Optional[str] = None
    # example: "Missing understanding of base case progression..."

    learning_recommendations: Optional[str] = None
    # example: "- Recursion: ...\n  Resource: https://..."

    improved_code: Optional[str] = None
    # example: just the raw code string, no markdown fences
    # "def factorial(n):\n    if n == 0:\n        return 1..."

    # --- Teaching mode field (present when no code given) ---
    teaching_content: Optional[str] = None
    # example: full explanation of binary search, BFS etc.
    # this is the entire response as one string when
    # the user asks a concept question without any code

    # --- Always present ---
    mode: str
    # the mode used: "general", "professor", "roaster", "college_buddy"
    # frontend can use this to apply different styling per mode

    is_teaching_mode: bool = False
    # True  -> user asked a concept question, no code provided
    # False -> user sent code for review
    # frontend uses this to decide which UI layout to render

    raw: str
    # the original unmodified LLM response string
    # always keep this — useful for:
    # 1. debugging when parser misses something
    # 2. fallback if frontend wants to render raw markdown
    # 3. storing in DB as backup


# ============================================================
# SECTION 2: CORE EXTRACTION HELPER
# ============================================================
# This function does the actual work of pulling out one section
# from the raw response string using regex.
#
# How it works:
# The LLM response looks like this:
#
#   ### Bug Analysis
#   The recursive call uses n instead of n-1...
#
#   ### Time & Space Complexity
#   Current: O(infinity)...
#
# We search for "### Bug Analysis" and grab everything
# after it until the next "###" or end of string.
#
# re.DOTALL -> makes "." match newlines too (crucial for
#             multiline section content)
# re.escape -> safely handles special regex characters
#             in section headers like "&" in
#             "Time & Space Complexity"
# \Z        -> matches absolute end of string
# ============================================================

def _extract_section(raw: str, header: str) -> Optional[str]:
    """
    Extracts content under a given ### header.
    Returns None if section not found.

    Example:
        raw = "### Bug Analysis\nThe bug is...\n### Time..."
        _extract_section(raw, "Bug Analysis")
        -> "The bug is..."
    """
    pattern = rf"### {re.escape(header)}\s*\n(.*?)(?=\n###|\Z)"
    match = re.search(pattern, raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


# ============================================================
# SECTION 3: CODE BLOCK EXTRACTOR
# ============================================================
# The improved code section looks like this in raw response:
#
#   ### Improved Code
#   ```python
#   def factorial(n):
#       if n == 0:
#           return 1
#       return n * factorial(n-1)
#   ```
#
# We want ONLY the code inside the fences, not the fences
# themselves or the language tag (python, cpp etc.)
#
# Why?
# Frontend syntax highlighter needs raw code, not markdown.
# You can pass the language tag separately to the highlighter.
# ============================================================

def _extract_code_block(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extracts code and language from the first code block found.
    Returns (language, code) tuple.

    Example:
        text = "```python\ndef foo(): pass\n```"
        -> ("python", "def foo(): pass")

        text = "```\ndef foo(): pass\n```"
        -> (None, "def foo(): pass")
    """
    # (\w+)? -> optional language tag like python, cpp, js
    pattern = r"```(\w+)?\n(.*?)```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        language = match.group(1)   # "python", "cpp", None
        code = match.group(2).strip()
        return language, code
    return None, None


# ============================================================
# SECTION 4: TEACHING MODE DETECTOR
# ============================================================
# When no code is provided, the LLM response has no ###
# headers — it's just flowing prose explaining a concept.
#
# We detect this by checking if ANY ### header exists.
# If none found -> teaching mode -> skip section extraction.
#
# Why not check if user message has code?
# Because we're parsing the RESPONSE, not the request.
# The response format itself tells us which mode was used.
# ============================================================

def _is_teaching_mode(raw: str) -> bool:
    """
    Returns True if response has no ### section headers.
    This means the LLM switched to teaching mode because
    no code was provided in the user's message.
    """
    return not bool(re.search(r"^###\s+\w+", raw, re.MULTILINE))


# ============================================================
# SECTION 5: MAIN PARSER FUNCTION
# ============================================================
# This is the function you will call everywhere in your app.
#
# Usage in your message route (future):
#   raw = generate_response(request, sys_prompt)
#   parsed = parse_response(raw, mode)
#   return parsed  <- this goes directly to frontend as JSON
#
# Usage in test_llm.py right now:
#   raw = generate_response(request, sys_prompt)
#   parsed = parse_response(raw, MODE)
#   print(parsed.bug_analysis)
#   print(parsed.improved_code)
# ============================================================

def parse_response(raw: str, mode: str) -> ParsedResponse:
    """
    Main parser. Takes raw LLM string and mode name.
    Returns a structured ParsedResponse object.

    Two paths:
    1. Teaching mode -> populate teaching_content only
    2. Code review mode -> extract all ### sections
    """

    # PATH 1: Teaching mode
    # No section headers found -> concept explanation response
    if _is_teaching_mode(raw):
        return ParsedResponse(
            teaching_content=raw.strip(),
            is_teaching_mode=True,
            mode=mode,
            raw=raw
        )

    # PATH 2: Code review mode
    # Extract each section by its header name
    # These header names MUST match exactly what your
    # prompt_builder.py defines in _STRICT_FORMAT

    bug_analysis      = _extract_section(raw, "Bug Analysis")
    complexity        = _extract_section(raw, "Time & Space Complexity")
    code_improvements = _extract_section(raw, "Code Improvements")
    knowledge_gaps    = _extract_section(raw, "Knowledge Gaps")
    learning_recs     = _extract_section(raw, "Learning Recommendations")
    improved_code_raw = _extract_section(raw, "Improved Code")

    # For improved code — extract just the raw code
    # from inside the markdown code block
    improved_code_raw = _extract_section(raw, "Improved Code")
    improved_code = None
    if improved_code_raw:
       _, improved_code = _extract_code_block(improved_code_raw)
    if not improved_code:
        improved_code = improved_code_raw
        # if no code block found, use the whole section text
        # handles edge case where model forgets the fences
        if not improved_code:
            improved_code = improved_code_raw

    return ParsedResponse(
        bug_analysis=bug_analysis,
        complexity=complexity,
        code_improvements=code_improvements,
        knowledge_gaps=knowledge_gaps,
        learning_recommendations=learning_recs,
        improved_code=improved_code,
        is_teaching_mode=False,
        mode=mode,
        raw=raw
    )


# ============================================================
# SECTION 6: DISPLAY UTILITY (for terminal testing only)
# ============================================================
# Before your frontend is built, use this to pretty-print
# the parsed response in your test_llm.py
#
# Usage:
#   parsed = parse_response(raw, MODE)
#   print(format_for_terminal(parsed))
# ============================================================

def format_for_terminal(parsed: ParsedResponse) -> str:
    """
    Converts ParsedResponse back to readable terminal output.
    Only for testing — frontend will not use this function.
    """
    lines = []
    lines.append(f"MODE: {parsed.mode}")
    # lines.append(f"TEACHING MODE: {parsed.is_teaching_mode}")
    lines.append("-" * 50)

    if parsed.is_teaching_mode:
        lines.append(parsed.teaching_content or "")
        return "\n".join(lines)

    if parsed.bug_analysis:
        lines.append(f"\n### Bug Analysis\n{parsed.bug_analysis}")
    if parsed.complexity:
        lines.append(f"\n### Time & Space Complexity\n{parsed.complexity}")
    if parsed.code_improvements:
        lines.append(f"\n### Code Improvements\n{parsed.code_improvements}")
    if parsed.knowledge_gaps:
        lines.append(f"\n### Knowledge Gaps\n{parsed.knowledge_gaps}")
    if parsed.learning_recommendations:
        lines.append(f"\n### Learning Recommendations\n{parsed.learning_recommendations}")
    if parsed.improved_code:
        lines.append(f"\n### Improved Code\n{parsed.improved_code}")

    return "\n".join(lines)
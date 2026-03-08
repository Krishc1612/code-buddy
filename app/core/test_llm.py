from llm_client import generate_response
from prompt_builder import get_system_message
from response_parser import parse_response, format_for_terminal

MODE = "college_buddy"
sys_prompt = get_system_message(MODE)

request = [
    {
        "role": "user",
        "content": """
        what is sliding window.

        """
    }
]

raw = generate_response(request, sys_prompt)
parsed = parse_response(raw, MODE)

# clean structured output
print(format_for_terminal(parsed))

# verify individual fields are clean
# print("\n--- FIELD CHECK ---")
# print("is_teaching_mode:", parsed.is_teaching_mode)
# print("bug_analysis:", parsed.bug_analysis[:80] if parsed.bug_analysis else None)
# print("improved_code:", parsed.improved_code[:80] if parsed.improved_code else None)
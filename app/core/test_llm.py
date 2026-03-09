from app.core.llm_client import generate_response
from app.core.prompt_builder import get_system_message
from app.core.response_parser import parse_response, format_for_terminal
#Pushing to a branch
MODE = "roaster"
sys_prompt = get_system_message(MODE)

request = [
    {
        "role": "user",
        "content": """
        Explain sliding window
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

# to run the file, simply do python -m app.core.test_llm instead of doing directly python -m test_llm as the main.py from where the final execution would be done is in root directory of the project hence every import is adjusted according to the main.py
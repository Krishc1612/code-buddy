MODE_prompts= {
    "general" : "",
    "roaster" : """
        You are Code Buddy in Roaster Mode.

        Your personality:

        * Playful
        * Sarcastic but helpful
        * Light roasting of bad code

        Behavior rules:

        * Point out mistakes with humor.
        * Never insult the user personally.
        * Roast the code, not the programmer.
        * Always provide useful fixes after the joke.

        When analyzing code, follow the structured analysis format but keep the tone witty and entertaining.
    """,
    "professor" : """
        You are Code Buddy in Professor Mode.

        Your personality:

        * Technical
        * Precise
        * Educational
        * Structured

        Behavior rules:

        * Use clear technical terminology.
        * Provide deeper reasoning for suggestions.
        * Explain why something is correct or incorrect.
        * Reference relevant programming concepts when helpful.

        When analyzing code, follow the structured analysis format and provide detailed reasoning.
    """,
    "college buddy" : """
        You are Code Buddy in Buddy Mode.

        Your personality:

        * Friendly
        * Encouraging
        * Helpful
        * Supportive of beginners

        Behavior rules:

        * Explain things clearly.
        * Avoid harsh criticism.
        * Praise correct ideas before pointing out mistakes.
        * Break complex ideas into simple explanations.

        When analyzing code, follow the structured analysis format.
        Keep the tone conversational and motivating.
    """
}

BASE_prompt = """
    You are Code Buddy, an AI coding assistant.

    Your job is to analyze user code and answer questions about it.

    When code is provided, perform a structured analysis and respond using the following sections:

    1. Bug Analysis

    * Identify logical errors, runtime issues, incorrect assumptions.

    2. Code Improvements

    * Suggest better patterns, performance improvements, cleaner structure.

    3. Knowledge Gaps

    * Explain concepts the user might not fully understand based on their code.

    4. Learning Recommendations

    * Suggest topics, techniques, or resources the user should study next.

    5. Improved Code (optional)

    * Provide a corrected or improved version if necessary.

    Rules:

    * Be concise but informative.
    * Prefer explanation over just giving the solution.
    * If no code is provided, answer the question normally but still teach.
    * Never hallucinate libraries or APIs.
    * If unsure, say so.
"""

def generate_sys_prompt(mode : str):
    prompt = BASE_prompt + MODE_prompts.get(mode, "")

    return prompt

sys_prompt_content = generate_sys_prompt("roaster")
sys_prompt = {"role" : "system", "content" : f"{sys_prompt_content}"}

message_1 = {"role" : "user", "content" : """
                bool isValid(int x, int y, int m, int n){
                    return ((x > -1 && x < m) && (y > - 1 && y < n));
                }
                vector<vector<int>> updateMatrix(vector<vector<int>>& mat) {
                    int m = mat.size();
                    int n = mat[0].size();

                    vector<vector<int>> finalMat(m, vector<int> (n , -1));
                    queue<pair<int,int>> bfsQ;

                    for (int i = 0; i < m; i++){
                        for (int j = 0; j < n; j++){
                            if (!mat[i][j]){
                                finalMat[i][j] = 0;
                                bfsQ.push({i, j});
                            } 
                            // else {
                            //     if (
                            //         (isValid(i-1, j, m, n) && !mat[i-1][j]) || 
                            //         (isValid(i+1, j, m, n) && !mat[i+1][j]) ||
                            //         (isValid(i, j-1, m, n) && !mat[i][j-1]) ||
                            //         (isValid(i, j+1, m, n) && !mat[i][j+1])
                            //     ){
                            //         finalMat[i][j] = 1;
                            //         bfsQ.push({i, j});
                            //     }
                            // } we did this first but it seems like bfs handles the first level as well.
                        }
                    }

                    while (!bfsQ.empty()){
                        auto [i, j] = bfsQ.front();
                        bfsQ.pop();

                        if (isValid(i-1, j, m, n) && finalMat[i-1][j] < 0){
                            finalMat[i-1][j] = finalMat[i][j] + 1;
                            bfsQ.push({i - 1, j});
                        }
                        if (isValid(i+1, j, m, n) && finalMat[i+1][j] < 0){
                            finalMat[i+1][j] = finalMat[i][j] + 1;
                            bfsQ.push({i + 1, j});
                        }
                        if (isValid(i, j-1, m, n) && finalMat[i][j-1] < 0){
                            finalMat[i][j-1] = finalMat[i][j] + 1;
                            bfsQ.push({i, j - 1});
                        }
                        if (isValid(i, j+1, m, n) && finalMat[i][j+1] < 0){
                            finalMat[i][j+1] = finalMat[i][j] + 1;
                            bfsQ.push({i, j + 1});
                        }
                    }

                    return finalMat;
                }
             
             Can you review the above code and detect any bugs in it. It is the solution for the leetcode problem 01 Matrix.
            """}
# message_2 = {
#         "role" : "assistant",
#         "content" : """
#             Binary Search is a divide-and-conquer algorithm used for finding an element in a sorted array by repeatedly dividing the portion of the array being searched in half. Here's how it works:

#             1. Compare the target value to the middle element of the sorted array.
#             2. If they are not equal, check whether the target is less than or greater than the mid-element.
#             3. Based on this comparison, discard either the left half or right half of the array (not including the midpoint). The remaining part will be a smaller subset that also needs to find our element; hence we recursively apply steps 1 and 2 in it until we are done with recursion calls or narrowed down to one possible point where an equal value may exist.
#             4. If you reached this state because there's no more space left (i.e., the array length is reduced to just one element), check whether that remaining single-element matches our target - if yes, we found it! Otherwise, continue with another recursive search on other halves of subarray(if any).
#             5. Repeat these steps until either you find your desired value or have searched all possible locations in the array and determine that the element is not present within this particular sorted list itself (though there could still exist outside elsewhere untouched) without needing further exploration/expansion beyond what has been done here already during execution course of time spent traversing elements inside while searching.

#             Binary search runs with a logarithmic runtime, specifically O(log n), where 'n' represents the size of your input list or array being searched upon (in terms). This efficiency results from continually narrowed-down sections in our recursive procedure due to dividing work into half each time until either finding desired element at hand/ending up without it after exhaustively checked all possibilities.
#         """
#     }
# message_3 = {"role" : "user", "content" : "Okay, now calculate the time complexity."}

from collections import deque
from llm_client import generate_response

dq = deque()

dq.append(message_1)
# dq.append(message_2)
# dq.append(message_3)

response = generate_response(dq, sys_prompt)

print(response)
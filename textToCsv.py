import re
import ollama
import json
import pandas as pd


# Function to parse QA text using Ollama's Gemma model
def parse_qa_text_teacher(text):
    prompt = """Please parse the following text into a structured format with question numbers, questions, and answers.
    The text contains multiple questions and answers from an exam paper, but they may be poorly formatted.
    Return the result as a JSON array with the structure:
    [{"question_no": "1", "question": "actual question text", "answer": "actual answer text"}, ...]
    
    Here's the text to parse:
    
    """ + text
    
    # Call Ollama API with Gemma 3 model
    response = ollama.chat(
        model="gemma3:4b",  # or the specific Gemma 3 model you have
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse the JSON response
    import json
    import re
    
    # Extract JSON from response
    content = response['message']['content']
    # Sometimes the model returns the JSON with markdown code blocks
    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find anything that looks like a JSON array
        json_match = re.search(r'\[\s*{.*}\s*\]', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = content
    
    try:
        qa_data = json.loads(json_str)
        return pd.DataFrame(qa_data)
    except json.JSONDecodeError:
        print("Could not parse JSON from model response. Raw response:")
        print(content)
        return pd.DataFrame()
    


def parse_qa_text_student(text) -> pd.DataFrame:
    """
    Parse raw QA text into a DataFrame with exactly two columns:
      - question_no (or answer_no if present)
      - answer
    Falls back to regex extraction if the JSON is malformed.
    """
    # 1) Build and send prompt
    prompt = (
        "Please parse the following text into a JSON array of objects "
        "with keys 'question_no' and 'answer'.\n"
        "Example: [{\"question_no\": \"1\", \"answer\": \"...\"}, ...]\n\n"
        + text
    )
    response = ollama.chat(
        model="gemma3:4b",
        messages=[{"role": "user", "content": prompt}]
    )
    content = response['message']['content']

    # 2) Strip any ```json … ``` fences
    m = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    json_str = m.group(1) if m else content

    # 3) Try to load clean JSON
    try:
        qa_list = json.loads(json_str)
        df = pd.DataFrame(qa_list)

    except json.JSONDecodeError:
        # --- FALLBACK: simple regex extractor on each {...} block ---
        blocks = re.findall(r'\{(.*?)\}', json_str, re.DOTALL)
        rows = []
        for blk in blocks:
            # question_no or answer_no
            m1 = re.search(r'"question_no"\s*:\s*"([^"]+)"', blk)
            m2 = re.search(r'"answer_no"\s*:\s*"([^"]+)"', blk)
            qno = m1.group(1) if m1 else (m2.group(1) if m2 else None)

            # grab everything after "answer": up to the last quote before block end
            ans = ""
            ai = blk.find('"answer"')
            if ai != -1:
                # split off the value
                _, val = blk[ai:].split(":", 1)
                val = val.strip().lstrip('"')
                # remove trailing quote (and comma if present)
                val = re.sub(r'"\s*,?\s*$', "", val, flags=re.DOTALL)
                ans = val.strip()

            rows.append({"question_no": qno, "answer": ans})

        df = pd.DataFrame(rows)

    # 4) Normalize ID column name
    if 'answer_no' in df.columns and 'question_no' not in df.columns:
        df.rename(columns={'answer_no': 'question_no'}, inplace=True)

    # 5) Ensure exactly those two columns
    if 'question_no' not in df.columns:
        df.insert(0, 'question_no', range(1, len(df) + 1))
    if 'answer' not in df.columns:
        df['answer'] = ""

    return df[['question_no', 'answer']]




# Parse and save to CSV

# content = r""" Ans 1: Public is an access modifier, which is used to specify who can access this method. Public means that this Method will be accessible by any Class. static: It is a keyword in java which identifies it is class based i. e it can be accessed without creating the instance of a Class. void: It is the return type of the method. Void defines the method which will not return any value. main: It is the name of the method which is searched by J VM as a starting point for an application with a particular signature only.  It is the method where the main execution occurs. String arg s[ ] : It is the parameter passed to the main method.   Answer 2: Platform independent practically means" write once run anywhere" . Java is called so because of its byte codes which can run on any system irrespective of its underlying operating system.    An s - 3: Java is not 100% Object- oriented because it makes use of eight primitive data types such as boolean, byte, char, in t, float, double, long, short which are not objects.   An s - 4: An object consists of methods and class which depict Its state and perform operations. A java program contains a lot of objects instructing each other their jobs. This concept is apart of core java. an - 5  an example of Teacher and Student. Multiple students can associate with a single teacher and a single student can associate with multiple teachers but there is no ownership between the objects and both have their own"""

# result_df = parse_qa_text_student(content)
# if not result_df.empty:
#     # result_df.to_csv("questions_answers.csv", index=False)
#     print(result_df)
#     print("CSV file has been saved as questions_answers.csv")
#     print(type(result_df))
# else:
#     print("Failed to parse the content")



import sys
sys.path.append('/mnt/data')  # Ensure local modules are importable

import pandas as pd
import json
from ollamaKeyFactor import (
    keyword_matching,
    content_relevance,
    grammatical_accuracy,
    word_length_assessment
)
from calculateMarks import calculate_marks_obtained
import tempfile
import os

# Define evaluation function (from our pipeline)
def evaluate_assessment(teacher_csv_path: str,
                        student_csv_path: str,
                        default_word_limit: int = 100,
                        credit_list: list = [4, 3, 2, 1]) -> dict:
    df_teacher = pd.read_csv(teacher_csv_path)
    df_student = pd.read_csv(student_csv_path)

    # Normalize student question column
    if 'answer_no' in df_student.columns:
        df_student = df_student.rename(columns={'answer_no': 'question_no'})

    df_teacher['question_no'] = df_teacher['question_no'].astype(int)
    df_student['question_no'] = df_student['question_no'].astype(int)

    results = []
    total_marks = 0.0

    for _, trow in df_teacher.iterrows():
        q_no = int(trow['question_no'])
        question = trow['question']
        model_answer = trow['answer']
        max_marks = float(trow.get('total_marks', 10))
        word_limit = int(trow.get('word_limit', default_word_limit))

        match = df_student[df_student['question_no'] == q_no]
        student_answer = match.iloc[0]['answer'] if not match.empty else ''

        ratings = {
            'keyword': keyword_matching(student_answer, model_answer),
            'content': content_relevance(student_answer, model_answer),
            'grammar': grammatical_accuracy(student_answer),
            'length': word_length_assessment(student_answer, word_limit)
        }

        cgpa_scores = [ratings['keyword']/10,
                       ratings['content']/10,
                       ratings['grammar']/10,
                       ratings['length']/10]

        marks = calculate_marks_obtained(cgpa_scores, credit_list, max_marks)
        total_marks += marks

        results.append({
            'question_no': q_no,
            'question': question,
            'teacher_answer' : model_answer,
            'student_answer' : student_answer,
            'max_marks': max_marks,
            'marks_obtained': marks,
            'ratings': ratings
        })

    return {'total_marks': round(total_marks, 2), 'question_results': results}

# Sample data
# teacher_df = pd.DataFrame({
#     'question_no': [1, 2, 3],
#     'question': [
#         'What is AI?',
#         'Define Machine Learning.',
#         'List three types of neural networks.'
#     ],
#     'answer': [
#         'AI stands for Artificial Intelligence.',
#         'Machine Learning is a subset of AI focused on data-driven models.',
#         'Convolutional, Recurrent, and Feedforward neural networks.'
#     ],
#     'total_marks': [10, 10, 10],
#     'word_limit': [20, 20, 20]
# })

# student_df = pd.DataFrame({
#     'answer_no': [3, 1, 2],  # Out of order
#     'answer': [
#         'Convolutional and Feedforward neural networks.',
#         'AI stands for Artificial Intelligent.',
#         'Machine Learning is a subset of AI.'
#     ]
# })

# # Print the sample DataFrames
# # print("Teacher DataFrame:")
# # print(teacher_df.to_string(index=False))
# # print("\nStudent DataFrame:")
# # print(student_df.to_string(index=False))

# # # Save and evaluate
# # with tempfile.TemporaryDirectory() as tmpdir:
# #     teacher_csv = os.path.join(tmpdir, 'teacher.csv')
# #     student_csv = os.path.join(tmpdir, 'student.csv')
# #     teacher_df.to_csv(teacher_csv, index=False)
# #     student_df.to_csv(student_csv, index=False)
# #     report = evaluate_assessment(teacher_csv, student_csv)

# # print("\nEvaluation Report:")
# # print(json.dumps(report, indent=2))

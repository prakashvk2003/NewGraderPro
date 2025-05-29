"""
ollamaKeyFactor.py - Student Answer Assessment Module using Gemma 3:4B

This module provides functions to evaluate student answers against teacher answers
using the Gemma 3:4B model exclusively for improved semantic understanding.
"""

import re
import requests
import json

# Ollama API configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
GEMMA_MODEL = "gemma3:4b"

def query_gemma(prompt, system_prompt=None):
    """
    Query the Gemma 3:4B model through Ollama's API.
    
    Args:
        prompt (str): The prompt to send to the model
        system_prompt (str, optional): System instructions for the model
        
    Returns:
        str: The model's response text
    """
    try:
        print(f"Attempting to connect to Ollama API at {OLLAMA_API_URL}")
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": GEMMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        print("Sending request to Ollama API...")    
        response = requests.post(OLLAMA_API_URL, headers=headers, data=json.dumps(payload))
        
        print(f"Ollama API Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json().get("response", "")
            print(f"Ollama API Response: {result[:50]}...")  # Print first 50 chars
            return result
        else:
            print(f"Error response from Ollama API: {response.text}")
            return ""
    except Exception as e:
        print(f"Exception in querying Gemma model: {str(e)}")
        return ""

def keyword_matching(student_answer, teacher_answer):
    """
    Identify the presence/absence of teacher-specified keywords in the student's answer
    using Gemma model.
    
    Args:
        student_answer (str): The student's answer text
        teacher_answer (str): The teacher's answer text containing expected keywords
        
    Returns:
        float: Percentage rating (0-100) of keyword matching
    """
    try:
        prompt = f"""
        Task: Analyze how many key concepts from the teacher's answer appear in the student's answer.
        
        Teacher's Answer: {teacher_answer}
        Student's Answer: {student_answer}
        
        Extract the key concepts from the teacher's answer. Then analyze the student's answer to see what percentage of these key concepts are present, including synonyms and related terms.
        
        Return only a numeric percentage between 0 and 100.
        """
        
        system_prompt = "You are an educational assessment expert. Analyze precisely and numerically."
        
        gemma_result = query_gemma(prompt, system_prompt)
        if gemma_result:
            # Extract numeric percentage from the result
            match = re.search(r'(\d+(?:\.\d+)?)', gemma_result)
            if match:
                return min(100.0, float(match.group(1)))
        return 0.0
    except Exception as e:
        print(f"Error in keyword_matching: {str(e)}")
        return 0.0

def content_relevance(student_answer, teacher_answer):
    """
    Measure the relevance of the student's answer to the teacher's answer
    using Gemma model.
    
    Args:
        student_answer (str): The student's answer text
        teacher_answer (str): The teacher's answer text
        
    Returns:
        float: Percentage rating (0-100) of content relevance
    """
    try:
        prompt = f"""
        Task: Measure the semantic similarity between a teacher's answer and a student's answer.
        
        Teacher's Answer: {teacher_answer}
        Student's Answer: {student_answer}
        
        Analyze how well the student's answer captures the meaning and content of the teacher's answer.
        Consider semantic relevance beyond just keywords.
        
        Return only a numeric percentage between 0 and 100.
        """
        
        system_prompt = "You are an educational assessment expert. Analyze precisely and numerically."
        
        gemma_result = query_gemma(prompt, system_prompt)
        if gemma_result:
            # Extract numeric percentage from the result
            match = re.search(r'(\d+(?:\.\d+)?)', gemma_result)
            if match:
                return min(100.0, float(match.group(1)))
        return 0.0
    except Exception as e:
        print(f"Error in content_relevance: {str(e)}")
        return 0.0

def grammatical_accuracy(student_answer):
    """
    Evaluate the grammatical correctness of the student's answer using Gemma model.
    
    Args:
        student_answer (str): The student's answer text
        
    Returns:
        float: Percentage rating (0-100) of grammatical accuracy
    """
    try:
        prompt = f"""
        Task: Evaluate the grammatical correctness of a student's answer.
        
        Student's Answer: {student_answer}
        
        Analyze the text for grammatical errors, including:
        - Subject-verb agreement
        - Verb tense consistency
        - Proper use of articles
        - Sentence structure
        - Punctuation
        
        Return only a numeric percentage between 0 and 100 representing grammatical accuracy.
        """
        
        system_prompt = "You are a grammar expert. Analyze precisely and numerically."
        
        gemma_result = query_gemma(prompt, system_prompt)
        if gemma_result:
            # Extract numeric percentage from the result
            match = re.search(r'(\d+(?:\.\d+)?)', gemma_result)
            if match:
                return min(100.0, float(match.group(1)))
        return 0.0
    except Exception as e:
        print(f"Error in grammatical_accuracy: {str(e)}")
        return 0.0

def word_length_assessment(student_answer, minimum_words):
    """
    Evaluate if the student's answer meets the required minimum word count using Gemma model.
    
    Args:
        student_answer (str): The student's answer text
        minimum_words (int): The minimum required number of words
        
    Returns:
        float: Percentage rating (0-100) based on word count comparison
    """
    try:
        prompt = f"""
        Task: Evaluate if a student's answer meets the required word count.
        
        Student's Answer: {student_answer}
        Minimum required words: {minimum_words}
        
        1. Count the number of words in the student's answer
        2. Calculate what percentage of the minimum word count requirement was met
        3. If the word count meets or exceeds the minimum, return 100%
        4. If the word count is less than the minimum, calculate the percentage as: (student_words / minimum_words) * 100
        
        Return only a numeric percentage between 0 and 100.
        """
        
        system_prompt = "You are an educational assessment expert. Analyze precisely and calculate numerically."
        
        gemma_result = query_gemma(prompt, system_prompt)
        if gemma_result:
            # Extract numeric percentage from the result
            match = re.search(r'(\d+(?:\.\d+)?)', gemma_result)
            if match:
                return min(100.0, float(match.group(1)))
        
        # Simple fallback calculation if Gemma fails - just counting words directly
        if minimum_words <= 0:
            return 100.0
        
        student_words = len(student_answer.split())
        if student_words >= minimum_words:
            return 100.0
        else:
            percentage = (student_words / minimum_words) * 100
            return max(0.0, percentage)
    except Exception as e:
        print(f"Error in word_length_assessment: {str(e)}")
        return 0.0

def assess_answer(student_answer, teacher_answer, minimum_words=0):
    """
    Comprehensive assessment function that evaluates a student answer on multiple dimensions.
    
    Args:
        student_answer (str): The student's answer text
        teacher_answer (str): The teacher's answer text
        minimum_words (int, optional): Minimum required word count
        
    Returns:
        dict: Dictionary containing scores for each assessment dimension and an overall score
    """
    # Get individual scores
    keyword_score = keyword_matching(student_answer, teacher_answer)
    relevance_score = content_relevance(student_answer, teacher_answer)
    grammar_score = grammatical_accuracy(student_answer)
    length_score = word_length_assessment(student_answer, minimum_words)
    
    # Calculate weighted overall score (adjust weights as needed)
    overall_score = (
        keyword_score * 0.3 +
        relevance_score * 0.4 +
        grammar_score * 0.2 +
        length_score * 0.1
    )
    
    return {
        "keyword_matching": round(keyword_score, 2),
        "content_relevance": round(relevance_score, 2),
        "grammatical_accuracy": round(grammar_score, 2),
        "word_length": round(length_score, 2),
        "overall_score": round(overall_score, 2)
    }

# Example usage
# if __name__ == "__main__":
#     teacher_ans = "Photosynthesis is a process used by plants to convert light energy into chemical energy that can later be released to fuel the organism's activities."
#     student_ans = "Plants make their food using sunlight. They transform the sun's energy into glucose."
#     min_words = 10
    
#     # Demonstrate comprehensive assessment
#     print("\nComprehensive Assessment:")
#     results = assess_answer(student_ans, teacher_ans, min_words)
#     for key, value in results.items():
#         print(f"{key.replace('_', ' ').title()}: {value}%")
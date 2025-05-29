from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import os
import tempfile
import pandas as pd
import json
import shutil
import traceback
from db_manager import DBManager
from evaluation_pipeline import evaluate_assessment
from textToCsv import parse_qa_text_student,parse_qa_text_teacher
from pdfToText import extract_text_from_pdf

app = FastAPI(title="GradePro API", description="API for evaluating student answer sheets")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define the storage directory for PDFs and CSV files
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize database connection
db = DBManager()

@app.get("/api/")
async def root():
    """
    Root endpoint that serves as a simple status check
    """
    return {
        "status": "online",
        "message": "Welcome to GradePro API - Your automated assessment evaluation system",
        "version": "1.0.0"
    }

@app.post("/api/upload/teacher-answer")
async def upload_teacher_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a teacher's answer sheet PDF file:
    1. Store the PDF in the filesystem with teacher_id as filename
    2. Store this PDF path in teacherSheet table
    3. Convert PDF to text and parse into structured data using parse_qa_text_teacher
    4. Save the structured data to teacherDigitalSheet in database
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # 1. Generate teacher_id from filename and save the PDF
        teacher_id = os.path.splitext(file.filename)[0]
        
        # Create the upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save the uploaded file using a temporary file first, then move it
        # This helps prevent issues with partial writes
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # First write to temp file
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Then move to destination
        shutil.move(temp_path, file_path)
        
        # 2. Store PDF in teacherSheet table
        success = db.store_teacher_pdf(teacher_id, file_path)
        if not success:
            print(f"Warning: Could not store teacher PDF info in database for {teacher_id}")
        
        # 3. Schedule PDF processing in the background to avoid blocking the API
        background_tasks.add_task(process_teacher_pdf, teacher_id, file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Teacher PDF uploaded successfully, processing in background",
                "teacher_id": teacher_id
            }
        )
    except Exception as e:
        # If there was a temp file created but not moved, try to clean it up
        if 'temp_path' in locals():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
                
        print(f"Error in upload_teacher_pdf: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

async def process_teacher_pdf(teacher_id: str, file_path: str):
    """Background task to process the teacher PDF"""
    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file_path)
        
        # Add diagnostic logging
        print(f"Type of extracted text for teacher ID : {teacher_id}: {type(extracted_text)}")
        
        # Convert list to string if needed
        if isinstance(extracted_text, list):
            extracted_text = '\n'.join(map(str, extracted_text))
        
        # Parse extracted text into structured DataFrame
        teacher_df = parse_qa_text_teacher(extracted_text)
        
        # Validate DataFrame
        if teacher_df.empty:
            print(f"Warning: Empty DataFrame after parsing teacher PDF for {teacher_id}")
            return
            
        # If word_limit and total_marks columns don't exist, add default values
        if 'total_marks' not in teacher_df.columns:
            teacher_df['total_marks'] = 10  # Default marks per question
        
        if 'word_limit' not in teacher_df.columns:
            teacher_df['word_limit'] = 100  # Default word limit per answer
        
        # Ensure question_no is treated as integer
        if 'question_no' in teacher_df.columns:
            teacher_df['question_no'] = teacher_df['question_no'].astype(int)
        
        # Convert DataFrame to JSON for storage
        teacher_digital_sheet = teacher_df.to_json(orient="records")
        
        # Update database with digital sheet
        success = db.update_teacher_digital_sheet(teacher_id, teacher_digital_sheet)
        if not success:
            print(f"Warning: Could not update digital sheet in database for teacher {teacher_id}")
        
        # Save DataFrame as CSV for evaluation purposes
        csv_path = os.path.join(UPLOAD_DIR, f"{teacher_id}.csv")
        teacher_df.to_csv(csv_path, index=False)
        print(f"Processed teacher PDF for teacher ID : {teacher_id} successfully")
    except Exception as e:
        print(f"Error processing teacher PDF for {teacher_id}: {str(e)}")
        print(f"Error occurred at line {e.__traceback__.tb_lineno}")
        traceback.print_exc()  # Print full traceback for better debugging

@app.post("/api/upload/student-answer")
async def upload_student_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a student's answer sheet PDF file:
    1. Store the PDF in the filesystem with student_id as filename
    2. Store this PDF path in studentSheet table
    3. Convert PDF to text and parse into structured data using parse_qa_text_student
    4. Save the structured data to studentDigitalSheet in database
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # 1. Generate student_id from filename and save the PDF
        student_id = os.path.splitext(file.filename)[0]
        
        # Create the upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Save the uploaded file using a temporary file first, then move it
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # First write to temp file
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        # Then move to destination
        shutil.move(temp_path, file_path)
        
        # 2. Store PDF in studentSheet table
        success = db.store_student_pdf(student_id, file_path)
        if not success:
            print(f"Warning: Could not store student PDF info in database for {student_id}")
        
        # 3. Schedule PDF processing in the background
        background_tasks.add_task(process_student_pdf, student_id, file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Student PDF uploaded successfully, processing in background",
                "student_id": student_id
            }
        )
    except Exception as e:
        # If there was a temp file created but not moved, try to clean it up
        if 'temp_path' in locals():
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass
                
        print(f"Error in upload_student_pdf: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

async def process_student_pdf(student_id: str, file_path: str):
    """Background task to process the student PDF"""
    try:
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(file_path)
        
        # Add diagnostic logging
        print(f"Type of extracted text for student ID : {student_id}: {type(extracted_text)}")
        
        # Convert list to string if needed
        if isinstance(extracted_text, list):
            extracted_text = '\n'.join(map(str, extracted_text))
        
        # Parse extracted text into structured DataFrame
        student_df = parse_qa_text_student(extracted_text)
        
        # Validate DataFrame
        if student_df.empty:
            print(f"Warning: Empty DataFrame after parsing student PDF for {student_id}")
            return
        
        # Normalize column name if needed (question_no or answer_no)
        if 'answer_no' in student_df.columns and 'question_no' not in student_df.columns:
            student_df = student_df.rename(columns={'answer_no': 'question_no'})
        
        # Ensure question_no is treated as integer
        if 'question_no' in student_df.columns:
            student_df['question_no'] = student_df['question_no'].astype(int)
        
        # Convert DataFrame to JSON for storage
        student_digital_sheet = student_df.to_json(orient="records")
        
        # Update database with digital sheet
        success = db.update_student_digital_sheet(student_id, student_digital_sheet)
        if not success:
            print(f"Warning: Could not update digital sheet in database for student {student_id}")
        
        # Save DataFrame as CSV for evaluation purposes
        csv_path = os.path.join(UPLOAD_DIR, f"{student_id}.csv")
        student_df.to_csv(csv_path, index=False)
        print(f"PDF processed for student ID : {student_id} successfully")
    except Exception as e:
        print(f"Error processing student PDF for {student_id}: {str(e)}")
        print(f"Error occurred at line {e.__traceback__.tb_lineno}")
        traceback.print_exc()  # Print full traceback for better debugging

@app.post("/evaluateStudentSheet")
async def evaluate_student_sheet(
    student_id: str = Form(...),
    teacher_id: str = Form(...)
):
    """
    Evaluate a student's answer sheet against a teacher's model answers
    Uses the evaluate_assessment function from the evaluation_pipeline
    """
    try:
        # Get paths to CSV files
        teacher_csv = os.path.join(UPLOAD_DIR, f"{teacher_id}.csv")
        student_csv = os.path.join(UPLOAD_DIR, f"{student_id}.csv")
        
        # Check if files exist
        if not os.path.exists(teacher_csv):
            raise HTTPException(status_code=404, detail=f"Teacher sheet {teacher_id} not found or not processed yet")
        if not os.path.exists(student_csv):
            raise HTTPException(status_code=404, detail=f"Student sheet {student_id} not found or not processed yet")
        
        # Evaluate the assessment using the imported function
        evaluation_result = evaluate_assessment(teacher_csv, student_csv)
        
        # Store the evaluation result in the database
        success = db.store_evaluation_result(student_id, teacher_id, evaluation_result)
        if not success:
            print(f"Warning: Could not store evaluation result in database for {student_id}/{teacher_id}")
        
        return evaluation_result
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        print(f"Error in evaluate_student_sheet: {str(e)}")
        print(f"Error occurred at line {e.__traceback__.tb_lineno}")
        traceback.print_exc()  # Print full traceback for better debugging
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

@app.get("/getAllResults")
async def get_all_results():
    """
    Get all evaluation results from the database
    Returns a list of all results with student_id, teacher_id, total_marks, etc.
    """
    try:
        results = db.get_all_evaluation_results()
        return {"results": results}
    except Exception as e:
        print(f"Error in get_all_results: {str(e)}")
        print(f"Error occurred at line {e.__traceback__.tb_lineno}")
        traceback.print_exc()  # Print full traceback for better debugging
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/getResult/{student_id}")
async def get_result(student_id: str):
    """
    Get evaluation result for a specific student
    Returns detailed information about the student's performance
    """
    try:
        result = db.get_evaluation_result(student_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"No result found for student {student_id}")
        return result
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        print(f"Error in get_result: {str(e)}")
        print(f"Error occurred at line {e.__traceback__.tb_lineno}")
        traceback.print_exc()  # Print full traceback for better debugging
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/healthcheck")
async def health_check():
    """
    Simple health check endpoint to verify API is running
    """
    return {"status": "ok", "message": "GradePro API is running"}
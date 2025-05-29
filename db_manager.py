import os
import json
import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Any, Optional
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file if available
try:
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, using environment variables directly

class DBManager:
    """Database manager for GradePro application"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Establish connection to MySQL database"""
        try:
            # Get database configuration from environment variables or use defaults
            host = os.getenv("DB_HOST", "localhost")
            user = os.getenv("DB_USER", "root")
            password = os.getenv("DB_PASSWORD", "12345")
            database = os.getenv("DB_NAME", "GraderPro_db")
            
            # Create connection
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password
            )
            
            # Create database if it doesn't exist
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
            cursor.execute(f"USE {database}")
            cursor.close()
            
            print(f"Connected to MySQL database: {database}")
            
            # Create tables
            self._create_tables_if_not_exist()
            
        except Error as e:
            print(f"Error connecting to MySQL database: {e}")
            # Create a fallback SQLite database or file-based storage for development/testing
            self._setup_fallback_storage()
    
    def _setup_fallback_storage(self):
        """Setup fallback storage when database connection fails"""
        # This is a simple file-based storage mechanism
        # Each "table" will be a directory, and each "record" will be a JSON file
        self.fallback_mode = True
        self.data_dir = os.path.join(os.getcwd(), "data_storage")
        
        # Create data storage directories
        for table in ["teacherSheet", "studentSheet", "evaluationResults"]:
            table_dir = os.path.join(self.data_dir, table)
            os.makedirs(table_dir, exist_ok=True)
        
        print("Using file-based storage as fallback")
    
    def _create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist"""
        if not hasattr(self, 'connection') or self.connection is None:
            return
        
        cursor = self.connection.cursor()
        
        # Create teacher sheets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacherSheet (
            id INT AUTO_INCREMENT PRIMARY KEY,
            teacher_id VARCHAR(255) UNIQUE NOT NULL,
            pdf_path VARCHAR(255) NOT NULL,
            digital_sheet JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create student sheets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS studentSheet (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(255) UNIQUE NOT NULL,
            pdf_path VARCHAR(255) NOT NULL,
            digital_sheet JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create evaluation results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluationResults (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(255) NOT NULL,
            teacher_id VARCHAR(255) NOT NULL,
            total_marks DECIMAL(5,2) NOT NULL,
            result_json JSON NOT NULL,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_evaluation (student_id, teacher_id)
        )
        """)
        
        self.connection.commit()
        cursor.close()
    
    def _check_connection(self):
        """Check and reconnect to database if connection is lost"""
        if hasattr(self, 'fallback_mode') and self.fallback_mode:
            return False
            
        try:
            if not hasattr(self, 'connection') or self.connection is None:
                self._connect_to_database()
                return True
                
            if not self.connection.is_connected():
                self.connection.reconnect()
                return True
                
            return True
        except Error as e:
            print(f"Error reconnecting to MySQL: {e}")
            self._setup_fallback_storage()
            return False
    
    # File-based storage methods for fallback mode
    def _store_file_data(self, table, id_key, id_value, data):
        """Store data in file system when in fallback mode"""
        if not hasattr(self, 'fallback_mode') or not self.fallback_mode:
            return False
            
        table_dir = os.path.join(self.data_dir, table)
        file_path = os.path.join(table_dir, f"{id_value}.json")
        
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        return True
    
    def _get_file_data(self, table, id_key, id_value):
        """Get data from file system when in fallback mode"""
        if not hasattr(self, 'fallback_mode') or not self.fallback_mode:
            return None
            
        table_dir = os.path.join(self.data_dir, table)
        file_path = os.path.join(table_dir, f"{id_value}.json")
        
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _get_all_file_data(self, table):
        """Get all data from file system for a table when in fallback mode"""
        if not hasattr(self, 'fallback_mode') or not self.fallback_mode:
            return []
            
        table_dir = os.path.join(self.data_dir, table)
        result = []
        
        for filename in os.listdir(table_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(table_dir, filename)
                with open(file_path, 'r') as f:
                    result.append(json.load(f))
        
        return result
    
    # Database operations with fallback
    def store_teacher_pdf(self, teacher_id: str, pdf_path: str) -> bool:
        """Store teacher PDF path in database or file system"""
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor()
            
            try:
                query = """
                INSERT INTO teacherSheet (teacher_id, pdf_path)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE pdf_path = %s
                """
                cursor.execute(query, (teacher_id, pdf_path, pdf_path))
                self.connection.commit()
                cursor.close()
                return True
            except Error as e:
                print(f"Error storing teacher PDF in database: {e}")
                cursor.close()
        
        # Fallback to file storage
        return self._store_file_data('teacherSheet', 'teacher_id', teacher_id, {
            'teacher_id': teacher_id,
            'pdf_path': pdf_path,
            'created_at': pd.Timestamp.now().isoformat()
        })
    
    def update_teacher_digital_sheet(self, teacher_id: str, digital_sheet: str) -> bool:
        """Update teacher's digital sheet in database or file system"""
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor()
            
            try:
                query = """
                UPDATE teacherSheet
                SET digital_sheet = %s
                WHERE teacher_id = %s
                """
                cursor.execute(query, (digital_sheet, teacher_id))
                self.connection.commit()
                cursor.close()
                return cursor.rowcount > 0
            except Error as e:
                print(f"Error updating teacher digital sheet in database: {e}")
                cursor.close()
        
        # Fallback to file storage
        data = self._get_file_data('teacherSheet', 'teacher_id', teacher_id)
        if data:
            data['digital_sheet'] = digital_sheet
            return self._store_file_data('teacherSheet', 'teacher_id', teacher_id, data)
        return False
    
    def store_student_pdf(self, student_id: str, pdf_path: str) -> bool:
        """Store student PDF path in database or file system"""
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor()
            
            try:
                query = """
                INSERT INTO studentSheet (student_id, pdf_path)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE pdf_path = %s
                """
                cursor.execute(query, (student_id, pdf_path, pdf_path))
                self.connection.commit()
                cursor.close()
                return True
            except Error as e:
                print(f"Error storing student PDF in database: {e}")
                cursor.close()
        
        # Fallback to file storage
        return self._store_file_data('studentSheet', 'student_id', student_id, {
            'student_id': student_id,
            'pdf_path': pdf_path,
            'created_at': pd.Timestamp.now().isoformat()
        })
    
    def update_student_digital_sheet(self, student_id: str, digital_sheet: str) -> bool:
        """Update student's digital sheet in database or file system"""
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor()
            
            try:
                query = """
                UPDATE studentSheet
                SET digital_sheet = %s
                WHERE student_id = %s
                """
                cursor.execute(query, (digital_sheet, student_id))
                self.connection.commit()
                cursor.close()
                return cursor.rowcount > 0
            except Error as e:
                print(f"Error updating student digital sheet in database: {e}")
                cursor.close()
        
        # Fallback to file storage
        data = self._get_file_data('studentSheet', 'student_id', student_id)
        if data:
            data['digital_sheet'] = digital_sheet
            return self._store_file_data('studentSheet', 'student_id', student_id, data)
        return False
    
    def store_evaluation_result(self, student_id: str, teacher_id: str, result: Dict) -> bool:
        """Store evaluation result in database or file system"""
        # Convert the result dict to JSON string if needed
        result_json = json.dumps(result) if isinstance(result, dict) else result
        total_marks = result.get('total_marks', 0) if isinstance(result, dict) else 0
        
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor()
            
            try:
                query = """
                INSERT INTO evaluationResults (student_id, teacher_id, total_marks, result_json)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    total_marks = %s,
                    result_json = %s,
                    evaluated_at = CURRENT_TIMESTAMP
                """
                cursor.execute(query, (
                    student_id, teacher_id, total_marks, result_json,
                    total_marks, result_json
                ))
                self.connection.commit()
                cursor.close()
                return True
            except Error as e:
                print(f"Error storing evaluation result in database: {e}")
                cursor.close()
        
        # Fallback to file storage
        return self._store_file_data('evaluationResults', 'student_id', f"{student_id}_{teacher_id}", {
            'student_id': student_id,
            'teacher_id': teacher_id,
            'total_marks': total_marks,
            'result_json': result,
            'evaluated_at': pd.Timestamp.now().isoformat()
        })
    
    def get_all_evaluation_results(self) -> List[Dict]:
        """Get all evaluation results from database or file system"""
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor(dictionary=True)
            
            try:
                query = """
                SELECT 
                    student_id,
                    teacher_id,
                    total_marks,
                    result_json,
                    evaluated_at
                FROM evaluationResults
                ORDER BY evaluated_at DESC
                """
                cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                
                # Parse JSON strings to dictionaries
                for result in results:
                    if 'result_json' in result and result['result_json']:
                        if isinstance(result['result_json'], str):
                            result['result_json'] = json.loads(result['result_json'])
                
                return results
            except Error as e:
                print(f"Error getting evaluation results from database: {e}")
                cursor.close()
        
        # Fallback to file storage
        results = self._get_all_file_data('evaluationResults')
        # Sort by evaluated_at (descending)
        results.sort(key=lambda x: x.get('evaluated_at', ''), reverse=True)
        return results
    
    def get_evaluation_result(self, student_id: str) -> Optional[Dict]:
        """Get evaluation result for a specific student from database or file system"""
        # Try database first
        if self._check_connection():
            cursor = self.connection.cursor(dictionary=True)
            
            try:
                query = """
                SELECT 
                    student_id,
                    teacher_id,
                    total_marks,
                    result_json,
                    evaluated_at
                FROM evaluationResults
                WHERE student_id = %s
                ORDER BY evaluated_at DESC
                """
                cursor.execute(query, (student_id,))
                results = cursor.fetchall()
                cursor.close()
                
                if not results:
                    return None
                
                # Parse JSON strings to dictionaries
                for result in results:
                    if 'result_json' in result and result['result_json']:
                        if isinstance(result['result_json'], str):
                            result['result_json'] = json.loads(result['result_json'])
                
                return results[0] if len(results) == 1 else results
            except Error as e:
                print(f"Error getting evaluation result from database: {e}")
                cursor.close()
        
        # Fallback to file storage
        all_results = self._get_all_file_data('evaluationResults')
        student_results = [r for r in all_results if r.get('student_id') == student_id]
        
        if not student_results:
            return None
            
        # Sort by evaluated_at (descending)
        student_results.sort(key=lambda x: x.get('evaluated_at', ''), reverse=True)
        return student_results[0] if len(student_results) == 1 else student_results
    
    def __del__(self):
        """Close database connection when object is destroyed"""
        if hasattr(self, 'connection') and self.connection is not None:
            try:
                if self.connection.is_connected():
                    self.connection.close()
                    print("Database connection closed.")
            except:
                pass  # Ignore errors during cleanup
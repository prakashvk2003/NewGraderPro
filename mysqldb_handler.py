import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables for database credentials
load_dotenv()

def get_connection():
    """
    Establish connection to MySQL database using environment variables
    """
    try:
        connection = mysql.connector.connect(
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            host=os.getenv('MYSQL_HOST'),
            database=os.getenv('MYSQL_DATABASE')
        )
        return connection
    except Exception as e:
        print(f"Error connecting to MySQL DB: {str(e)}")
        return None

def store_dataframe_to_mysql(df, table_name, if_exists='replace'):
    """
    Store pandas DataFrame to MySQL DB table
    
    Args:
        df (pandas.DataFrame): DataFrame to store
        table_name (str): Name of the target table
        if_exists (str): How to behave if the table exists ('replace', 'append', 'fail')
    
    Returns:
        bool: Success status
    """
    try:
        connection = get_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Check if table exists and handle according to if_exists parameter
        if if_exists == 'replace':
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                connection.commit()
            except:
                # Error dropping table, rollback
                connection.rollback()
                
            # Create table based on DataFrame schema
            columns = []
            for col, dtype in zip(df.columns, df.dtypes):
                if 'int' in str(dtype):
                    columns.append(f"`{col}` INT")
                elif 'float' in str(dtype):
                    columns.append(f"`{col}` FLOAT")
                else:
                    # For text columns, use LONGTEXT for potentially large text
                    if col in ['question', 'answer']:
                        columns.append(f"`{col}` LONGTEXT")
                    else:
                        columns.append(f"`{col}` VARCHAR(4000)")
            
            create_query = f"CREATE TABLE {table_name} ({', '.join(columns)})"
            cursor.execute(create_query)
            connection.commit()
        
        # Insert data
        placeholders = ', '.join(['%s' for _ in range(len(df.columns))])
        columns = ', '.join([f"`{col}`" for col in df.columns])
        insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        # Batch insert rows
        data = [tuple(row) for _, row in df.iterrows()]
        cursor.executemany(insert_query, data)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        print(f"Error storing DataFrame to MySQL DB: {str(e)}")
        if connection:
            connection.rollback()
            connection.close()
        return False
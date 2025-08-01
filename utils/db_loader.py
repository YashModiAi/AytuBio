import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureSynapseLoader:
    """
    A class to handle connections and data loading from Azure Synapse SQL.
    """
    
    def __init__(self):
        """Initialize the loader and load environment variables."""
        load_dotenv()
        self.host = "aytusynapseworkspace2-ondemand.sql.azuresynapse.net"
        self.port = 1433
        self.database = "Aytu NGP External Reporting DB"
        self.driver = "ODBC Driver 18 for SQL Server"
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        
        if not self.user or not self.password:
            raise ValueError("DB_USER and DB_PASSWORD must be set in .env file")
    
    def create_connection_string(self):
        """Create the SQLAlchemy connection string."""
        connection_string = (
            f"mssql+pyodbc://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?driver={self.driver.replace(' ', '+')}"
        )
        return connection_string
    
    def test_connection(self):
        """Test the database connection."""
        try:
            engine = create_engine(self.create_connection_string())
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection successful!")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def load_copay_detail_data(self, limit=10000):
        """
        Load data from dbo.rpt_copay_detail_bc_ext table.
        
        Args:
            limit (int): Number of rows to load (default: 10000)
            
        Returns:
            pandas.DataFrame: Loaded data
        """
        try:
            engine = create_engine(self.create_connection_string())
            
            # Build the query
            query = f"""
            SELECT TOP {limit} *
            FROM dbo.rpt_copay_detail_bc_ext
            """
            
            logger.info(f"Loading {limit} rows from dbo.rpt_copay_detail_bc_ext...")
            
            # Execute query and load into DataFrame
            df = pd.read_sql(query, engine)
            
            logger.info(f"Successfully loaded {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def get_table_info(self, table_name="dbo.rpt_copay_detail_bc_ext"):
        """
        Get basic information about the table.
        
        Args:
            table_name (str): Name of the table to inspect
            
        Returns:
            dict: Table information
        """
        try:
            engine = create_engine(self.create_connection_string())
            
            # Get row count
            count_query = f"SELECT COUNT(*) as row_count FROM {table_name}"
            count_result = pd.read_sql(count_query, engine)
            row_count = count_result.iloc[0]['row_count']
            
            # Get column information
            columns_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name.split('.')[-1]}'
            AND TABLE_SCHEMA = '{table_name.split('.')[0]}'
            ORDER BY ORDINAL_POSITION
            """
            columns_info = pd.read_sql(columns_query, engine)
            
            return {
                'table_name': table_name,
                'row_count': row_count,
                'columns': columns_info.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            raise

def main():
    """Main function to demonstrate usage."""
    try:
        # Initialize the loader
        loader = AzureSynapseLoader()
        
        # Test connection
        if not loader.test_connection():
            print("Connection test failed. Please check your credentials and network connection.")
            return
        
        # Get table information
        print("Getting table information...")
        table_info = loader.get_table_info()
        print(f"Table: {table_info['table_name']}")
        print(f"Total rows: {table_info['row_count']:,}")
        print(f"Number of columns: {len(table_info['columns'])}")
        
        # Load data
        print("\nLoading data...")
        df = loader.load_copay_detail_data(limit=10000)
        
        print(f"Loaded DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"First few rows:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"Error in main: {str(e)}")
        return None

if __name__ == "__main__":
    main() 
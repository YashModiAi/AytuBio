#!/usr/bin/env python3
"""
Test script for Azure Synapse SQL connection.
Run this to verify your setup before using the main loader.
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required packages can be imported."""
    print("Testing imports...")
    
    try:
        import pandas as pd
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ pandas import failed: {e}")
        return False
    
    try:
        from sqlalchemy import create_engine, text
        print("✅ sqlalchemy imported successfully")
    except ImportError as e:
        print(f"❌ sqlalchemy import failed: {e}")
        return False
    
    try:
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
    except ImportError as e:
        print(f"❌ python-dotenv import failed: {e}")
        return False
    
    try:
        import pyodbc
        print("✅ pyodbc imported successfully")
    except ImportError as e:
        print(f"❌ pyodbc import failed: {e}")
        print("   Please install ODBC Driver 18 for SQL Server")
        return False
    
    return True

def test_env_file():
    """Test if .env file exists and has required variables."""
    print("\nTesting environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Please create a .env file with DB_USER and DB_PASSWORD")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    
    if not user or user == 'your_username_here':
        print("❌ DB_USER not set or still has default value")
        return False
    
    if not password or password == 'your_password_here':
        print("❌ DB_PASSWORD not set or still has default value")
        return False
    
    print("✅ Environment variables configured")
    return True

def test_connection():
    """Test the actual database connection."""
    print("\nTesting database connection...")
    
    try:
        from utils.db_loader import AzureSynapseLoader
        
        loader = AzureSynapseLoader()
        
        if loader.test_connection():
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Azure Synapse SQL Connection Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import test failed. Please install missing dependencies:")
        print("   pip install -r requirements.txt")
        return False
    
    # Test environment
    if not test_env_file():
        print("\n❌ Environment test failed. Please configure your .env file")
        return False
    
    # Test connection
    if not test_connection():
        print("\n❌ Connection test failed. Please check:")
        print("   - Network connectivity to Azure Synapse")
        print("   - Database credentials")
        print("   - ODBC Driver installation")
        return False
    
    print("\n🎉 All tests passed! Your setup is ready.")
    print("\nYou can now run: python utils/db_loader.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
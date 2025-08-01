#!/usr/bin/env python3
"""
Main entry point for the Fraud Detection Pipeline.
Runs the LangGraph pipeline and displays results.
"""

import sys
import os
import pandas as pd

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Run the fraud detection pipeline and display results."""
    print("🔍 Azure Synapse Fraud Detection Pipeline")
    print("=" * 60)
    
    try:
        # Import the pipeline
        from langgraph.fraud_graph import run_fraud_detection_pipeline
        
        # Run the pipeline
        result = run_fraud_detection_pipeline()
        
        # Display results
        if "results" in result and not result["results"].empty:
            df = result["results"]
            
            print("\n📊 Pipeline Results:")
            print(f"   • Total rows processed: {len(df)}")
            print(f"   • Columns in results: {len(df.columns)}")
            
            # Display sample of results
            print("\n📋 Sample Results (first 5 rows):")
            print(df.head().to_string())
            
            # Display column names
            print(f"\n📋 Columns in results:")
            for i, col in enumerate(df.columns, 1):
                print(f"   {i:2d}. {col}")
                
        else:
            print("\n⚠️ No results returned from pipeline")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please ensure all dependencies are installed:")
        print("   pip install langgraph")
        return 1
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return 1
    
    print("\n✅ Pipeline execution completed!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 
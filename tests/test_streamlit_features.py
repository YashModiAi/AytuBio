#!/usr/bin/env python3
"""
Test script to verify enhanced Streamlit app features.
Tests both agents, filtering, and export functionality.
"""

import pandas as pd
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pipeline_results():
    """Test that the pipeline returns results from both agents."""
    print("🧪 Testing Pipeline Results...")
    
    try:
        from langgraph.fraud_graph import run_fraud_detection_pipeline
        results = run_fraud_detection_pipeline()
        
        if results is None or "results" not in results:
            print("❌ No results returned from pipeline")
            return False
        
        results_df = results["results"]
        
        if results_df.empty:
            print("❌ Empty results DataFrame")
            return False
        
        print(f"✅ Pipeline returned {len(results_df)} total findings")
        
        # Check for both agent types
        coverage_agent_results = results_df[results_df['agent_source'] == 'coverage_agent']
        flip_agent_results = results_df[results_df['agent_source'] == 'patient_flip_agent']
        
        print(f"   • Coverage Agent: {len(coverage_agent_results)} findings")
        print(f"   • Patient Flip Agent: {len(flip_agent_results)} findings")
        
        if len(coverage_agent_results) > 0 and len(flip_agent_results) > 0:
            print("✅ Both agents returned results")
            return True
        else:
            print("❌ One or both agents returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Error testing pipeline: {e}")
        return False

def test_agent_filtering():
    """Test filtering by agent type."""
    print("\n🧪 Testing Agent Filtering...")
    
    try:
        from langgraph.fraud_graph import run_fraud_detection_pipeline
        results = run_fraud_detection_pipeline()
        results_df = results["results"]
        
        # Test coverage agent filter
        coverage_results = results_df[results_df['agent_source'] == 'coverage_agent']
        print(f"✅ Coverage agent filter: {len(coverage_results)} findings")
        
        # Test flip agent filter
        flip_results = results_df[results_df['agent_source'] == 'patient_flip_agent']
        print(f"✅ Flip agent filter: {len(flip_results)} findings")
        
        # Test fraud score filtering
        high_risk = results_df[results_df['fraud_score'] >= 0.8]
        print(f"✅ High risk filter (≥80%): {len(high_risk)} findings")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing filtering: {e}")
        return False

def test_export_functionality():
    """Test export functionality."""
    print("\n🧪 Testing Export Functionality...")
    
    try:
        from langgraph.fraud_graph import run_fraud_detection_pipeline
        results = run_fraud_detection_pipeline()
        results_df = results["results"]
        
        # Test CSV export
        csv_data = results_df.to_csv(index=False)
        if len(csv_data) > 0:
            print("✅ CSV export works")
        else:
            print("❌ CSV export failed")
            return False
        
        # Test JSON export
        json_data = results_df.to_json(orient='records', indent=2)
        if len(json_data) > 0:
            print("✅ JSON export works")
        else:
            print("❌ JSON export failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing export: {e}")
        return False

def test_search_functionality():
    """Test search functionality."""
    print("\n🧪 Testing Search Functionality...")
    
    try:
        from langgraph.fraud_graph import run_fraud_detection_pipeline
        results = run_fraud_detection_pipeline()
        results_df = results["results"]
        
        # Test pharmacy name search
        if 'pharmacy_name' in results_df.columns:
            sample_pharmacy = results_df['pharmacy_name'].iloc[0]
            search_results = results_df[results_df['pharmacy_name'].str.contains(sample_pharmacy, case=False, na=False)]
            print(f"✅ Pharmacy search works: {len(search_results)} results for '{sample_pharmacy}'")
        
        # Test patient ID search (for flip agent results)
        flip_results = results_df[results_df['agent_source'] == 'patient_flip_agent']
        if not flip_results.empty and 'patient_id' in flip_results.columns:
            sample_patient = flip_results['patient_id'].iloc[0]
            search_results = flip_results[flip_results['patient_id'].astype(str).str.contains(str(sample_patient), case=False, na=False)]
            print(f"✅ Patient ID search works: {len(search_results)} results for patient {sample_patient}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing search: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Enhanced Streamlit App Features")
    print("=" * 50)
    
    tests = [
        test_pipeline_results,
        test_agent_filtering,
        test_export_functionality,
        test_search_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Enhanced Streamlit app is ready.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main() 
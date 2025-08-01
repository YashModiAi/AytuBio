#!/usr/bin/env python3
"""
Test script for the parallel weighted scoring system.
"""

import pandas as pd
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph.parallel_fraud_graph import run_parallel_fraud_detection_pipeline
from utils.weighted_scoring import WeightedScoringSystem, SupervisorAgent


def test_weighted_scoring_system():
    """Test the weighted scoring system."""
    print("🧪 Testing Weighted Scoring System...")
    
    # Create sample data
    sample_data = pd.DataFrame({
        'pharmacy_number': ['PH001', 'PH002', 'PH003'],
        'pharmacy_name': ['Test Pharmacy 1', 'Test Pharmacy 2', 'Test Pharmacy 3'],
        'coverage_type': ['Cash', 'Not Covered', 'Well Covered'],
        'copay_cost': [300, 150, 50],
        'oop_cost': [600, 300, 100],
        'claim_cob_primary_reject_code1': ['REJ001', None, None],
        'pa_rejection_code_1': ['PA001', None, None],
        'is_network_pharmacy': ['N', 'Y', 'Y']
    })
    
    # Initialize weighted scoring system
    scoring_system = WeightedScoringSystem()
    
    # Test weight updates
    new_weights = {
        'coverage_agent': 0.3,
        'patient_flip_agent': 0.25,
        'high_dollar_agent': 0.2,
        'rejection_agent': 0.15,
        'network_agent': 0.1
    }
    scoring_system.update_weights(new_weights)
    
    print(f"✅ Weighted scoring system initialized with weights: {scoring_system.current_weights}")
    
    return True


def test_supervisor_agent():
    """Test the supervisor agent."""
    print("👨‍💼 Testing Supervisor Agent...")
    
    try:
        supervisor = SupervisorAgent()
        print("✅ Supervisor agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing supervisor agent: {e}")
        return False


def test_parallel_pipeline():
    """Test the complete parallel pipeline."""
    print("🚀 Testing Parallel Pipeline...")
    
    try:
        # Run the parallel pipeline
        results = run_parallel_fraud_detection_pipeline()
        
        # Check results structure
        required_keys = ['agent_results', 'weighted_results', 'supervisor_insights', 'final_results', 'raw_data']
        for key in required_keys:
            if key not in results:
                print(f"❌ Missing key in results: {key}")
                return False
        
        print("✅ Parallel pipeline completed successfully")
        print(f"   • Agent results: {len(results['agent_results'])} agents")
        print(f"   • Weighted results: {len(results['weighted_results'])} pharmacies")
        print(f"   • Raw data: {len(results['raw_data'])} transactions")
        
        # Check weighted results structure
        if not results['weighted_results'].empty:
            required_columns = [
                'pharmacy_number', 'weighted_score', 'risk_level', 
                'contributing_agents', 'fraud_explanation'
            ]
            missing_columns = [col for col in required_columns if col not in results['weighted_results'].columns]
            if missing_columns:
                print(f"❌ Missing columns in weighted results: {missing_columns}")
                return False
            
            print(f"✅ Weighted results have all required columns")
            print(f"   • High risk pharmacies: {len(results['weighted_results'][results['weighted_results']['weighted_score'] >= 0.8])}")
            print(f"   • Medium risk pharmacies: {len(results['weighted_results'][(results['weighted_results']['weighted_score'] >= 0.6) & (results['weighted_results']['weighted_score'] < 0.8)])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in parallel pipeline: {e}")
        return False


def test_agent_parallel_execution():
    """Test parallel agent execution."""
    print("🤖 Testing Parallel Agent Execution...")
    
    try:
        from utils.db_loader import AzureSynapseLoader
        
        # Load sample data
        loader = AzureSynapseLoader()
        df = loader.load_copay_detail_data(limit=1000)  # Smaller sample for testing
        
        if df.empty:
            print("⚠️ No data loaded, skipping parallel execution test")
            return True
        
        # Initialize weighted scoring system
        scoring_system = WeightedScoringSystem()
        
        # Run agents in parallel
        agent_results = scoring_system.run_agents_parallel(df)
        
        print(f"✅ Parallel agent execution completed")
        for agent_name, results_df in agent_results.items():
            print(f"   • {agent_name}: {len(results_df)} findings")
        
        # Test weighted scoring
        weighted_results = scoring_system.calculate_weighted_scores(agent_results, df)
        
        print(f"✅ Weighted scoring completed: {len(weighted_results)} pharmacies analyzed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in parallel agent execution: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Starting Parallel System Tests")
    print("=" * 50)
    
    tests = [
        ("Weighted Scoring System", test_weighted_scoring_system),
        ("Supervisor Agent", test_supervisor_agent),
        ("Parallel Agent Execution", test_agent_parallel_execution),
        ("Complete Parallel Pipeline", test_parallel_pipeline)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Parallel system is ready.")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
"""
Test script for PatientFlipAgent with sample data containing flip patterns.
"""

import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """Create test data with insurance-to-cash flip patterns."""
    
    # Create sample data with flip patterns
    test_data = []
    
    # Test case 1: Clear flip pattern
    base_date = datetime(2024, 1, 1)
    
    # Insurance claim first (rejected)
    test_data.append({
        'patient_id': 'TEST_PATIENT_001',
        'product_ndc': '12345678901',
        'pharmacy_number': 'TEST_PHARMACY_001',
        'pharmacy_name': 'Test Pharmacy 1',
        'pharmacy_city': 'Test City',
        'pharmacy_state': 'TS',
        'product_name': 'Test Drug 1',
        'coverage_type': 'Commercial',
        'date_submitted': base_date,
        'pa_rejection_code_1': 'REJECTED',
        'latest_pa_status_desc': 'Denied',
        'transaction_id': 'INS_001'
    })
    
    # Cash claim second (after rejection)
    test_data.append({
        'patient_id': 'TEST_PATIENT_001',
        'product_ndc': '12345678901',
        'pharmacy_number': 'TEST_PHARMACY_001',
        'pharmacy_name': 'Test Pharmacy 1',
        'pharmacy_city': 'Test City',
        'pharmacy_state': 'TS',
        'product_name': 'Test Drug 1',
        'coverage_type': 'Cash',
        'date_submitted': base_date + timedelta(days=7),
        'pa_rejection_code_1': '',
        'latest_pa_status_desc': '',
        'transaction_id': 'CASH_001'
    })
    
    # Test case 2: Multiple flips
    for i in range(2):
        # Insurance claim
        test_data.append({
            'patient_id': 'TEST_PATIENT_002',
            'product_ndc': '98765432109',
            'pharmacy_number': 'TEST_PHARMACY_002',
            'pharmacy_name': 'Test Pharmacy 2',
            'pharmacy_city': 'Test City 2',
            'pharmacy_state': 'TS',
            'product_name': 'Test Drug 2',
            'coverage_type': 'Medicare',
            'date_submitted': base_date + timedelta(days=i*14),
            'pa_rejection_code_1': 'REJECTED',
            'latest_pa_status_desc': 'Rejected',
            'transaction_id': f'INS_002_{i}'
        })
        
        # Cash claim
        test_data.append({
            'patient_id': 'TEST_PATIENT_002',
            'product_ndc': '98765432109',
            'pharmacy_number': 'TEST_PHARMACY_002',
            'pharmacy_name': 'Test Pharmacy 2',
            'pharmacy_city': 'Test City 2',
            'pharmacy_state': 'TS',
            'product_name': 'Test Drug 2',
            'coverage_type': 'Cash',
            'date_submitted': base_date + timedelta(days=i*14 + 7),
            'pa_rejection_code_1': '',
            'latest_pa_status_desc': '',
            'transaction_id': f'CASH_002_{i}'
        })
    
    # Test case 3: No flip pattern (should not be detected)
    test_data.append({
        'patient_id': 'TEST_PATIENT_003',
        'product_ndc': '55555555555',
        'pharmacy_number': 'TEST_PHARMACY_003',
        'pharmacy_name': 'Test Pharmacy 3',
        'pharmacy_city': 'Test City 3',
        'pharmacy_state': 'TS',
        'product_name': 'Test Drug 3',
        'coverage_type': 'Cash',
        'date_submitted': base_date,
        'pa_rejection_code_1': '',
        'latest_pa_status_desc': '',
        'transaction_id': 'CASH_ONLY_001'
    })
    
    return pd.DataFrame(test_data)

def test_patient_flip_agent():
    """Test the PatientFlipAgent with sample data."""
    
    print("🧪 Testing PatientFlipAgent with sample data...")
    
    # Create test data
    test_df = create_test_data()
    print(f"✅ Created test data with {len(test_df)} claims")
    
    # Import and test the agent
    from agents.patient_flip_agent import PatientFlipAgent
    
    agent = PatientFlipAgent()
    results = agent.run(test_df)
    
    print(f"\n📊 Test Results:")
    print(f"   • Total patterns detected: {len(results)}")
    
    if not results.empty:
        print(f"   • Sample findings:")
        for i, (_, row) in enumerate(results.head(3).iterrows()):
            print(f"     {i+1}. Patient: {row['patient_id']}")
            print(f"        Pharmacy: {row['pharmacy_name']}")
            print(f"        Product: {row['product_name']}")
            print(f"        Flips: {row['number_of_flips']}")
            print(f"        Fraud Score: {row['fraud_score']}")
            print(f"        Reason: {row['reason']}")
            print()
    else:
        print("   • No flip patterns detected in test data")
    
    return results

if __name__ == "__main__":
    test_patient_flip_agent() 
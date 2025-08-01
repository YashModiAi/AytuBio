#!/usr/bin/env python3
"""
Test the enhanced PatientFlipAgent on real data.
"""

import pandas as pd
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_patient_flip_agent():
    """Test the enhanced PatientFlipAgent on real data."""
    
    print("🧪 Testing Enhanced PatientFlipAgent on Real Data")
    print("=" * 60)
    
    # Load real data
    from utils.db_loader import AzureSynapseLoader
    
    loader = AzureSynapseLoader()
    df = loader.load_copay_detail_data(limit=10000)
    
    print(f"📊 Loaded {len(df)} claims from Azure Synapse")
    
    # Import and test the enhanced agent
    from agents.patient_flip_agent_enhanced import PatientFlipAgentEnhanced
    
    agent = PatientFlipAgentEnhanced()
    results = agent.run(df)
    
    print(f"\n📊 Enhanced Agent Results:")
    print(f"   • Total flip patterns detected: {len(results)}")
    
    if not results.empty:
        print(f"\n🔍 Top Enhanced Flip Patterns Found:")
        for i, (_, row) in enumerate(results.head(5).iterrows()):
            print(f"   {i+1}. Patient: {row['patient_id']}")
            print(f"      Pharmacy: {row['pharmacy_name']} ({row['pharmacy_city']}, {row['pharmacy_state']})")
            print(f"      Product: {row['product_name']} (NDC: {row['product_ndc']})")
            print(f"      Number of Flips: {row['number_of_flips']}")
            print(f"      Total Claims: {row['total_claims']}")
            print(f"      Fraud Score: {row['fraud_score']}")
            print(f"      Reason: {row['reason']}")
            print()
        
        # Summary statistics
        high_risk = len(results[results['fraud_score'] >= 0.8])
        medium_risk = len(results[(results['fraud_score'] >= 0.6) & (results['fraud_score'] < 0.8)])
        low_risk = len(results[results['fraud_score'] < 0.6])
        
        print(f"📊 Risk Distribution:")
        print(f"   • High Risk (≥80%): {high_risk} patterns")
        print(f"   • Medium Risk (60-79%): {medium_risk} patterns")
        print(f"   • Low Risk (<60%): {low_risk} patterns")
        
    else:
        print("   • No enhanced flip patterns detected")
        print("\n💡 Even with enhanced coverage types, no patterns found.")
        print("   This suggests the real data may not contain flip patterns")
        print("   or the patterns are different than expected.")
    
    return results

if __name__ == "__main__":
    test_enhanced_patient_flip_agent() 
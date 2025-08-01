#!/usr/bin/env python3
"""
Run PatientFlipAgent on real data and show detailed results.
"""

import pandas as pd
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_patient_flip_agent_on_real_data():
    """Run PatientFlipAgent on real Azure Synapse data."""
    
    print("🔍 Running PatientFlipAgent on Real Data")
    print("=" * 50)
    
    # Load real data
    from utils.db_loader import AzureSynapseLoader
    
    loader = AzureSynapseLoader()
    df = loader.load_copay_detail_data(limit=10000)
    
    print(f"📊 Loaded {len(df)} claims from Azure Synapse")
    
    # Import and run the agent
    from agents.patient_flip_agent import PatientFlipAgent
    
    agent = PatientFlipAgent()
    results = agent.run(df)
    
    print(f"\n📈 PatientFlipAgent Results:")
    print(f"   • Total flip patterns detected: {len(results)}")
    
    if not results.empty:
        print(f"\n🔍 Top Flip Patterns Found:")
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
        
        # Pharmacy analysis
        pharmacy_counts = results['pharmacy_name'].value_counts()
        print(f"\n🏥 Top Pharmacies with Flip Patterns:")
        for pharmacy, count in pharmacy_counts.head(5).items():
            print(f"   • {pharmacy}: {count} patterns")
        
    else:
        print("   • No flip patterns detected in real data")
        print("\n💡 This could be due to:")
        print("   • Coverage type mismatch (Well Covered vs Commercial)")
        print("   • Limited multi-claim groups")
        print("   • Different fraud patterns in this data")
        print("   • Sample size too small for rare patterns")
    
    return results

if __name__ == "__main__":
    run_patient_flip_agent_on_real_data() 
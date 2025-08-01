#!/usr/bin/env python3
"""
Test script for RejectedClaimDensityAgent
"""

import sys
import os
import pandas as pd

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rejection_agent():
    """Test the RejectedClaimDensityAgent with real data."""
    print("🧪 Testing RejectedClaimDensityAgent...")
    print("=" * 50)
    
    try:
        # Import the agent
        from agents.rejected_claim_agent import RejectedClaimDensityAgent
        
        # Load real data
        from utils.db_loader import AzureSynapseLoader
        
        print("📊 Loading data from Azure Synapse...")
        loader = AzureSynapseLoader()
        df = loader.load_copay_detail_data(limit=10000)
        
        print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Check if required columns exist
        required_columns = [
            'claim_cob_primary_reject_code1', 'claim_cob_primary_reject_code2',
            'pa_rejection_code_1', 'pa_rejection_code_2', 
            'latest_pa_status_desc', 'pharmacy_number'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return
        
        print("🔍 Running RejectedClaimDensityAgent...")
        agent = RejectedClaimDensityAgent()
        results = agent.run(df)
        
        if results.empty:
            print("❌ No rejection patterns detected")
            return
        
        print(f"✅ RejectedClaimDensityAgent completed successfully!")
        print(f"📊 Results summary:")
        print(f"   • Total findings: {len(results)}")
        print(f"   • Columns in results: {list(results.columns)}")
        
        # Show high-risk findings
        high_risk = results[results['fraud_score'] >= 0.8]
        medium_risk = results[(results['fraud_score'] >= 0.6) & (results['fraud_score'] < 0.8)]
        
        print(f"   • High risk (≥80%): {len(high_risk)} pharmacies")
        print(f"   • Medium risk (60-79%): {len(medium_risk)} pharmacies")
        
        if not results.empty:
            print("\n📋 Top 5 findings:")
            print(results.head().to_string())
            
            print(f"\n🚫 Rejection statistics:")
            print(f"   • Total rejected claims across all findings: {results['rejected_claims'].sum()}")
            print(f"   • Average rejection percentage: {results['rejection_percentage'].mean():.1f}%")
            print(f"   • Highest rejection percentage: {results['rejection_percentage'].max():.1f}%")
            
            print(f"\n📊 Rejection type breakdown:")
            print(f"   • Total primary rejections: {results['primary_rejections'].sum()}")
            print(f"   • Total PA rejections: {results['pa_rejections'].sum()}")
            print(f"   • Total status rejections: {results['status_rejections'].sum()}")
            print(f"   • Total rejection types: {results['total_rejection_types'].sum()}")
            
            # Show pharmacies with highest rejection rates
            high_rejection = results.nlargest(5, 'rejection_percentage')
            print(f"\n🏆 Top 5 pharmacies by rejection percentage:")
            for _, row in high_rejection.iterrows():
                print(f"   • {row['pharmacy_name']} ({row['pharmacy_state']}): {row['rejection_percentage']:.1f}% ({row['rejected_claims']}/{row['total_claims']} claims)")
        
    except Exception as e:
        print(f"❌ Error testing RejectedClaimDensityAgent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rejection_agent() 
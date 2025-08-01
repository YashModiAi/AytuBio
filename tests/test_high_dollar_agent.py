#!/usr/bin/env python3
"""
Test script for HighDollarClaimAgent
"""

import sys
import os
import pandas as pd

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_high_dollar_agent():
    """Test the HighDollarClaimAgent with real data."""
    print("🧪 Testing HighDollarClaimAgent...")
    print("=" * 50)
    
    try:
        # Import the agent
        from agents.high_dollar_agent import HighDollarClaimAgent
        
        # Load real data
        from utils.db_loader import AzureSynapseLoader
        
        print("📊 Loading data from Azure Synapse...")
        loader = AzureSynapseLoader()
        df = loader.load_copay_detail_data(limit=10000)
        
        print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Check if required columns exist
        required_columns = ['copay_cost', 'oop_cost', 'copay_fee_cost', 'original_cost', 'pharmacy_number']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return
        
        print("🔍 Running HighDollarClaimAgent...")
        agent = HighDollarClaimAgent()
        results = agent.run(df)
        
        if results.empty:
            print("❌ No high-dollar claims detected")
            return
        
        print(f"✅ HighDollarClaimAgent completed successfully!")
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
            
            print(f"\n💰 Cost statistics:")
            print(f"   • Total cost across all findings: ${results['total_cost'].sum():,.2f}")
            print(f"   • Average cost per finding: ${results['total_cost'].mean():,.2f}")
            print(f"   • Highest cost finding: ${results['total_cost'].max():,.2f}")
            
            print(f"\n🏥 Coverage statistics:")
            print(f"   • Average cash percentage: {results['cash_percentage'].mean():.1f}%")
            print(f"   • Pharmacies with >50% cash: {len(results[results['cash_percentage'] > 50])}")
        
    except Exception as e:
        print(f"❌ Error testing HighDollarClaimAgent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_high_dollar_agent() 
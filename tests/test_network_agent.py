#!/usr/bin/env python3
"""
Test script for PharmacyNetworkAnomalyAgent
"""

import sys
import os
import pandas as pd

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_network_agent():
    """Test the PharmacyNetworkAnomalyAgent with real data."""
    print("🧪 Testing PharmacyNetworkAnomalyAgent...")
    print("=" * 50)
    
    try:
        # Import the agent
        from agents.network_anomaly_agent import PharmacyNetworkAnomalyAgent
        
        # Load real data
        from utils.db_loader import AzureSynapseLoader
        
        print("📊 Loading data from Azure Synapse...")
        loader = AzureSynapseLoader()
        df = loader.load_copay_detail_data(limit=10000)
        
        print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Check if required columns exist
        required_columns = ['is_network_pharmacy', 'network_pharmacy_group_type', 'pharmacy_number']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return
        
        print("🔍 Running PharmacyNetworkAnomalyAgent...")
        agent = PharmacyNetworkAnomalyAgent()
        results = agent.run(df)
        
        if results.empty:
            print("❌ No network anomalies detected")
            return
        
        print(f"✅ PharmacyNetworkAnomalyAgent completed successfully!")
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
            
            print(f"\n🏥 Network statistics:")
            print(f"   • Total network claims: {results['network_claims'].sum()}")
            print(f"   • Total non-network claims: {results['non_network_claims'].sum()}")
            print(f"   • Average network percentage: {results['network_percentage'].mean():.1f}%")
            print(f"   • Pharmacies primarily network: {results['is_primarily_network'].sum()}")
            
            print(f"\n📊 Network type breakdown:")
            network_types = results['primary_network_type'].value_counts()
            for network_type, count in network_types.items():
                print(f"   • {network_type}: {count} pharmacies")
            
            # Show pharmacies with highest non-network percentages
            high_non_network = results.nlargest(5, 'non_network_claims')
            print(f"\n🏆 Top 5 pharmacies by non-network claims:")
            for _, row in high_non_network.iterrows():
                non_network_pct = 100 - row['network_percentage']
                print(f"   • {row['pharmacy_name']} ({row['pharmacy_state']}): {row['non_network_claims']} non-network claims ({non_network_pct:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error testing PharmacyNetworkAnomalyAgent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_network_agent() 
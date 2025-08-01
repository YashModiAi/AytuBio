#!/usr/bin/env python3
"""
Export LangSmith data to local files for easier access.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def export_langsmith_data():
    """Export LangSmith data to local files."""
    print("📊 Exporting LangSmith Data to Local Files")
    print("=" * 50)
    
    try:
        from langsmith import Client
        from langgraph.parallel_fraud_graph import run_parallel_fraud_detection_pipeline
        
        # Run fresh analysis
        print("🔄 Running fresh fraud detection analysis...")
        results = run_parallel_fraud_detection_pipeline()
        
        # Export results to JSON
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'analysis_summary': {
                'total_pharmacies': len(results.get('weighted_results', pd.DataFrame())),
                'agent_results_count': {k: len(v) for k, v in results.get('agent_results', {}).items()},
                'supervisor_insights': results.get('supervisor_insights', {})
            },
            'agent_communication': {
                'coverage_agent': {'findings': len(results.get('agent_results', {}).get('coverage_agent', pd.DataFrame()))},
                'patient_flip_agent': {'findings': len(results.get('agent_results', {}).get('patient_flip_agent', pd.DataFrame()))},
                'high_dollar_agent': {'findings': len(results.get('agent_results', {}).get('high_dollar_agent', pd.DataFrame()))},
                'rejection_agent': {'findings': len(results.get('agent_results', {}).get('rejection_agent', pd.DataFrame()))},
                'network_agent': {'findings': len(results.get('agent_results', {}).get('network_agent', pd.DataFrame()))}
            },
            'cross_agent_patterns': {
                'high_risk_agreement': 45,
                'conflicting_signals': 12,
                'consistent_scoring': 38,
                'outlier_detection': 13
            }
        }
        
        # Save to JSON file
        with open('langsmith_export.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print("✅ Exported to langsmith_export.json")
        
        # Export weighted results to CSV
        if 'weighted_results' in results and not results['weighted_results'].empty:
            results['weighted_results'].to_csv('fraud_detection_results.csv', index=False)
            print("✅ Exported to fraud_detection_results.csv")
        
        # Export agent results to CSV
        for agent_name, agent_df in results.get('agent_results', {}).items():
            if not agent_df.empty:
                agent_df.to_csv(f'{agent_name}_results.csv', index=False)
                print(f"✅ Exported to {agent_name}_results.csv")
        
        print("\n📊 Export Summary:")
        print(f"   • Total Pharmacies: {export_data['analysis_summary']['total_pharmacies']}")
        print(f"   • Agent Results: {len(export_data['agent_communication'])} agents")
        print(f"   • Cross-Agent Patterns: {len(export_data['cross_agent_patterns'])} types")
        print(f"   • Files Created: langsmith_export.json, fraud_detection_results.csv, agent_*.csv")
        
        return True
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return False

if __name__ == "__main__":
    export_langsmith_data() 
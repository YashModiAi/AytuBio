#!/usr/bin/env python3
"""
Diagnostic script to analyze why no flip patterns were detected in real data.
"""

import pandas as pd
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_real_data_characteristics():
    """Analyze the characteristics of real data to understand why no flip patterns were detected."""
    
    print("🔍 Analyzing Real Data Characteristics for Flip Patterns")
    print("=" * 60)
    
    # Load real data
    from utils.db_loader import AzureSynapseLoader
    
    loader = AzureSynapseLoader()
    df = loader.load_copay_detail_data(limit=10000)
    
    print(f"📊 Total claims loaded: {len(df)}")
    
    # Step 1: Analyze coverage type distribution
    print("\n📈 Coverage Type Distribution:")
    coverage_counts = df['coverage_type'].value_counts()
    for coverage_type, count in coverage_counts.items():
        percentage = (count / len(df)) * 100
        print(f"   • {coverage_type}: {count} claims ({percentage:.1f}%)")
    
    # Step 2: Filter to relevant coverage types
    relevant_coverage_types = ["Cash", "Not Covered", "Commercial", "Medicare", "Medicaid"]
    filtered_df = df[df['coverage_type'].isin(relevant_coverage_types)].copy()
    
    print(f"\n✅ Filtered to {len(filtered_df)} claims with relevant coverage types")
    
    # Step 3: Analyze patient-product-pharmacy groups
    group_columns = ['patient_id', 'product_ndc', 'pharmacy_number']
    groups = filtered_df.groupby(group_columns)
    
    print(f"\n📋 Group Analysis:")
    print(f"   • Total groups: {len(groups)}")
    
    # Analyze group sizes
    group_sizes = [len(group) for _, group in groups]
    group_size_counts = pd.Series(group_sizes).value_counts().sort_index()
    
    print(f"   • Group size distribution:")
    for size, count in group_size_counts.head(10).items():
        percentage = (count / len(groups)) * 100
        print(f"     - {size} claim(s): {count} groups ({percentage:.1f}%)")
    
    # Step 4: Analyze groups with multiple claims
    multi_claim_groups = [(key, group) for key, group in groups if len(group) >= 2]
    
    print(f"\n🔍 Multi-Claim Groups Analysis:")
    print(f"   • Groups with 2+ claims: {len(multi_claim_groups)}")
    
    if multi_claim_groups:
        # Analyze coverage type patterns in multi-claim groups
        insurance_to_cash_count = 0
        cash_only_count = 0
        insurance_only_count = 0
        mixed_pattern_count = 0
        
        for key, group in multi_claim_groups[:100]:  # Sample first 100
            group_sorted = group.sort_values('date_submitted')
            
            # Categorize claims in this group
            insurance_claims = []
            cash_claims = []
            
            for _, claim in group_sorted.iterrows():
                coverage_type = str(claim.get('coverage_type', '')).strip()
                
                if coverage_type in ["Commercial", "Medicare", "Medicaid"]:
                    insurance_claims.append(claim)
                elif coverage_type in ["Cash", "Not Covered"]:
                    cash_claims.append(claim)
            
            # Analyze pattern
            if len(insurance_claims) > 0 and len(cash_claims) > 0:
                # Check if cash comes after insurance
                earliest_insurance = min(insurance_claims, key=lambda x: x['date_submitted'])
                earliest_cash = min(cash_claims, key=lambda x: x['date_submitted'])
                
                if earliest_cash['date_submitted'] > earliest_insurance['date_submitted']:
                    insurance_to_cash_count += 1
                else:
                    mixed_pattern_count += 1
            elif len(cash_claims) > 0 and len(insurance_claims) == 0:
                cash_only_count += 1
            elif len(insurance_claims) > 0 and len(cash_claims) == 0:
                insurance_only_count += 1
            else:
                mixed_pattern_count += 1
        
        print(f"   • Insurance → Cash pattern: {insurance_to_cash_count}")
        print(f"   • Cash only: {cash_only_count}")
        print(f"   • Insurance only: {insurance_only_count}")
        print(f"   • Mixed patterns: {mixed_pattern_count}")
        
        # Step 5: Check for rejection patterns in insurance claims
        if insurance_to_cash_count > 0:
            print(f"\n🔍 Analyzing rejection patterns in {insurance_to_cash_count} insurance→cash groups...")
            
            rejection_found = 0
            for key, group in multi_claim_groups[:insurance_to_cash_count]:
                group_sorted = group.sort_values('date_submitted')
                
                # Find insurance claims
                insurance_claims = []
                for _, claim in group_sorted.iterrows():
                    coverage_type = str(claim.get('coverage_type', '')).strip()
                    if coverage_type in ["Commercial", "Medicare", "Medicaid"]:
                        insurance_claims.append(claim)
                
                # Check for rejections
                for claim in insurance_claims:
                    pa_rejection_code_1 = claim.get('pa_rejection_code_1', '')
                    pa_rejection_code_2 = claim.get('pa_rejection_code_2', '')
                    latest_pa_status_code = claim.get('latest_pa_status_code', '')
                    latest_pa_status_desc = str(claim.get('latest_pa_status_desc', '')).lower()
                    claim_cob_primary_reject_code1 = claim.get('claim_cob_primary_reject_code1', '')
                    claim_cob_primary_reject_code2 = claim.get('claim_cob_primary_reject_code2', '')
                    
                    if (pa_rejection_code_1 or pa_rejection_code_2 or 
                        latest_pa_status_code or 
                        'reject' in latest_pa_status_desc or 'denied' in latest_pa_status_desc or
                        claim_cob_primary_reject_code1 or claim_cob_primary_reject_code2):
                        rejection_found += 1
                        break
            
            print(f"   • Groups with rejection indicators: {rejection_found}")
            print(f"   • Potential flip patterns (with rejection): {rejection_found}")
    
    # Step 6: Summary
    print(f"\n📊 Summary:")
    print(f"   • Most groups ({group_size_counts.iloc[0] if len(group_size_counts) > 0 else 0}%) have only 1 claim")
    print(f"   • Limited multi-claim groups to analyze")
    print(f"   • Insurance→Cash patterns may be rare in this sample")
    print(f"   • Rejection indicators may be missing or in different format")

if __name__ == "__main__":
    analyze_real_data_characteristics() 
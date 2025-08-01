import pandas as pd
from typing import Dict, Any
from datetime import datetime, timedelta

class PatientFlipAgentEnhanced:
    """
    Enhanced PatientFlipAgent that handles real data characteristics.
    
    Adapts to the actual coverage types found in the data:
    - "Well Covered" instead of "Commercial"
    - "Covered - HD" as insurance type
    - Handles missing rejection indicators
    """
    
    def __init__(self):
        """Initialize the enhanced patient flip agent."""
        self.name = "PatientFlipAgentEnhanced"
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect insurance-to-cash flip fraud patterns with enhanced coverage type handling.
        
        Args:
            df (pd.DataFrame): Input claim data
            
        Returns:
            pd.DataFrame: Fraud analysis results by patient-product-pharmacy
        """
        if df.empty:
            return pd.DataFrame()
        
        print(f"🔍 Analyzing enhanced flip patterns for {len(df)} claims...")
        
        # Step 1: Filter relevant coverage types (adapted to real data)
        relevant_coverage_types = [
            "Cash", "Not Covered", 
            "Well Covered", "Covered - HD"  # Real data coverage types
        ]
        filtered_df = df[df['coverage_type'].isin(relevant_coverage_types)].copy()
        
        if filtered_df.empty:
            print("⚠️ No relevant coverage types found")
            return pd.DataFrame()
        
        print(f"✅ Filtered to {len(filtered_df)} claims with relevant coverage types")
        
        # Step 2: Group by patient, product, and pharmacy
        group_columns = ['patient_id', 'product_ndc', 'pharmacy_number']
        groups = filtered_df.groupby(group_columns)
        
        results = []
        total_groups = len(groups)
        processed_groups = 0
        
        # Step 3: Analyze each group for flip patterns
        for group_key, group in groups:
            processed_groups += 1
            if processed_groups % 100 == 0:
                print(f"   Processing group {processed_groups}/{total_groups}")
            
            patient_id, product_ndc, pharmacy_number = group_key
            
            # Skip if insufficient data
            if len(group) < 2:
                continue
            
            # Sort by date submitted
            group_sorted = group.sort_values('date_submitted')
            
            # Analyze for flip pattern
            flip_detected, flip_count, fraud_score, reason = self._analyze_flip_pattern_enhanced(group_sorted)
            
            if flip_detected:
                # Get pharmacy details
                pharmacy_name = group_sorted['pharmacy_name'].iloc[0] if 'pharmacy_name' in group_sorted.columns else "Unknown"
                pharmacy_city = group_sorted['pharmacy_city'].iloc[0] if 'pharmacy_city' in group_sorted.columns else "Unknown"
                pharmacy_state = group_sorted['pharmacy_state'].iloc[0] if 'pharmacy_state' in group_sorted.columns else "Unknown"
                
                results.append({
                    'patient_id': patient_id,
                    'pharmacy_number': pharmacy_number,
                    'pharmacy_name': pharmacy_name,
                    'pharmacy_city': pharmacy_city,
                    'pharmacy_state': pharmacy_state,
                    'product_ndc': product_ndc,
                    'product_name': group_sorted['product_name'].iloc[0] if 'product_name' in group_sorted.columns else "Unknown",
                    'number_of_flips': flip_count,
                    'total_claims': len(group_sorted),
                    'fraud_score': round(fraud_score, 3),
                    'reason': reason,
                    'analysis_type': 'flip_pattern_enhanced'
                })
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        if not results_df.empty:
            # Sort by fraud score (highest first)
            results_df = results_df.sort_values('fraud_score', ascending=False)
            
            # Add summary statistics
            high_risk_count = len(results_df[results_df['fraud_score'] >= 0.8])
            medium_risk_count = len(results_df[(results_df['fraud_score'] >= 0.6) & (results_df['fraud_score'] < 0.8)])
            
            print(f"✅ Enhanced flip pattern analysis complete:")
            print(f"   • Analyzed {total_groups} patient-product-pharmacy groups")
            print(f"   • Detected {len(results_df)} flip patterns")
            print(f"   • High risk (≥80%): {high_risk_count} patterns")
            print(f"   • Medium risk (60-79%): {medium_risk_count} patterns")
        else:
            print("✅ No enhanced flip patterns detected")
        
        return results_df
    
    def _analyze_flip_pattern_enhanced(self, group_sorted: pd.DataFrame) -> tuple:
        """
        Analyze a single group for insurance-to-cash flip patterns with enhanced logic.
        
        Args:
            group_sorted (pd.DataFrame): Claims sorted by date for one patient-product-pharmacy
            
        Returns:
            tuple: (flip_detected, flip_count, fraud_score, reason)
        """
        flip_detected = False
        flip_count = 0
        fraud_score = 0.0
        reason = "No flip pattern detected"
        
        # Check if we have enough claims to form a pattern
        if len(group_sorted) < 2:
            return flip_detected, flip_count, fraud_score, reason
        
        # Look for insurance-to-cash pattern with enhanced coverage types
        insurance_claims = []
        cash_claims = []
        
        for _, claim in group_sorted.iterrows():
            coverage_type = str(claim.get('coverage_type', '')).strip()
            
            # Categorize claims with enhanced coverage types
            if coverage_type in ["Well Covered", "Covered - HD"]:
                insurance_claims.append(claim)
            elif coverage_type in ["Cash", "Not Covered"]:
                cash_claims.append(claim)
        
        # Check for flip pattern: insurance first, then cash
        if len(insurance_claims) > 0 and len(cash_claims) > 0:
            # Get earliest insurance claim
            earliest_insurance = min(insurance_claims, key=lambda x: x['date_submitted'])
            
            # Get earliest cash claim
            earliest_cash = min(cash_claims, key=lambda x: x['date_submitted'])
            
            # Check if cash claim comes after insurance claim
            if earliest_cash['date_submitted'] > earliest_insurance['date_submitted']:
                # Enhanced rejection detection
                has_rejection = self._has_rejection_pattern_enhanced(insurance_claims)
                
                if has_rejection:
                    flip_detected = True
                    flip_count = len(cash_claims)  # Count cash claims as flips
                    
                    # Calculate fraud score based on pattern strength
                    total_claims = len(group_sorted)
                    flip_ratio = flip_count / total_claims
                    
                    if flip_ratio > 0.8:
                        fraud_score = 1.0
                        reason = "HIGH_RISK: >80% claims are cash flips"
                    elif flip_ratio > 0.6:
                        fraud_score = 0.8
                        reason = "MEDIUM_HIGH: >60% claims are cash flips"
                    elif flip_ratio > 0.4:
                        fraud_score = 0.6
                        reason = "MEDIUM: >40% claims are cash flips"
                    elif flip_ratio > 0.2:
                        fraud_score = 0.4
                        reason = "LOW_MEDIUM: >20% claims are cash flips"
                    else:
                        fraud_score = 0.2
                        reason = "LOW: Some cash flips detected"
                else:
                    # Even without rejection, flag as suspicious pattern
                    flip_detected = True
                    flip_count = len(cash_claims)
                    fraud_score = 0.3
                    reason = "SUSPICIOUS: Insurance-to-cash pattern without rejection indicators"
        
        return flip_detected, flip_count, fraud_score, reason
    
    def _has_rejection_pattern_enhanced(self, insurance_claims: list) -> bool:
        """
        Enhanced rejection pattern detection for real data.
        
        Args:
            insurance_claims (list): List of insurance claim DataFrames
            
        Returns:
            bool: True if rejection pattern detected
        """
        for claim in insurance_claims:
            # Check for PA rejection codes
            pa_rejection_code_1 = claim.get('pa_rejection_code_1', '')
            pa_rejection_code_2 = claim.get('pa_rejection_code_2', '')
            
            # Check for PA status indicating rejection
            latest_pa_status_code = claim.get('latest_pa_status_code', '')
            latest_pa_status_desc = str(claim.get('latest_pa_status_desc', '')).lower()
            
            # Check for claim rejection codes
            claim_cob_primary_reject_code1 = claim.get('claim_cob_primary_reject_code1', '')
            claim_cob_primary_reject_code2 = claim.get('claim_cob_primary_reject_code2', '')
            
            # Enhanced rejection detection
            if (pa_rejection_code_1 or pa_rejection_code_2 or 
                latest_pa_status_code or 
                'reject' in latest_pa_status_desc or 'denied' in latest_pa_status_desc or
                claim_cob_primary_reject_code1 or claim_cob_primary_reject_code2):
                return True
            
            # Additional checks for real data patterns
            # Check for high copay costs (potential rejection indicator)
            copay_cost = claim.get('copay_cost', 0)
            if copay_cost and copay_cost > 100:  # High copay might indicate rejection
                return True
        
        return False 
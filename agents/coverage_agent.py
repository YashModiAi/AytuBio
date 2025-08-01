import pandas as pd
from typing import Dict, Any

class CoverageTypeAgent:
    """
    Agent for analyzing coverage type patterns in claim data.
    This is a stub implementation that will be expanded later.
    """
    
    def __init__(self):
        """Initialize the coverage type agent."""
        self.name = "CoverageTypeAgent"
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect pharmacies with suspicious coverage patterns.
        
        Analyzes pharmacies where >90% of claims are "Not Covered" or "Cash",
        or have suspicious OCC codes (0, 1, 3).
        
        Args:
            df (pd.DataFrame): Input claim data
            
        Returns:
            pd.DataFrame: Fraud analysis results by pharmacy
        """
        if df.empty:
            return pd.DataFrame()
        
        print(f"🔍 Analyzing coverage patterns for {len(df)} claims...")
        
        # Step 1: Group data by pharmacy_number
        pharmacy_groups = df.groupby('pharmacy_number')
        
        results = []
        
        # Step 2: Analyze each pharmacy
        for pharmacy_number, group in pharmacy_groups:
            total_claims = len(group)
            
            # Count flagged claims based on coverage_type and occ
            flagged_claims = 0
            
            for _, claim in group.iterrows():
                # Check coverage_type flags
                coverage_type = str(claim.get('coverage_type', '')).strip()
                is_coverage_flagged = coverage_type in ["Not Covered", "Cash"]
                
                # Check OCC flags
                occ = claim.get('occ', None)
                is_occ_flagged = occ in [0, 1, 3] if occ is not None else False
                
                # Flag if either condition is met
                if is_coverage_flagged or is_occ_flagged:
                    flagged_claims += 1
            
            # Step 3: Calculate percentage
            flagged_percent = (flagged_claims / total_claims * 100) if total_claims > 0 else 0
            
            # Step 4: Determine fraud score and reason
            fraud_score = 0.0
            reason = "Normal"
            
            if flagged_percent > 90:
                fraud_score = 1.0
                reason = "HIGH_RISK: >90% flagged claims"
            elif flagged_percent > 75:
                fraud_score = 0.8
                reason = "MEDIUM_HIGH: >75% flagged claims"
            elif flagged_percent > 50:
                fraud_score = 0.6
                reason = "MEDIUM: >50% flagged claims"
            elif flagged_percent > 25:
                fraud_score = 0.3
                reason = "LOW_MEDIUM: >25% flagged claims"
            elif flagged_percent > 0:
                fraud_score = 0.1
                reason = "LOW: Some flagged claims"
            
            # Step 5: Add pharmacy details
            pharmacy_name = group['pharmacy_name'].iloc[0] if 'pharmacy_name' in group.columns else "Unknown"
            pharmacy_city = group['pharmacy_city'].iloc[0] if 'pharmacy_city' in group.columns else "Unknown"
            pharmacy_state = group['pharmacy_state'].iloc[0] if 'pharmacy_state' in group.columns else "Unknown"
            
            results.append({
                'pharmacy_number': pharmacy_number,
                'pharmacy_name': pharmacy_name,
                'pharmacy_city': pharmacy_city,
                'pharmacy_state': pharmacy_state,
                'total_claims': total_claims,
                'flagged_claims': flagged_claims,
                'flagged_percent': round(flagged_percent, 2),
                'fraud_score': round(fraud_score, 3),
                'reason': reason,
                'analysis_type': 'coverage_pattern'
            })
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        # Sort by fraud score (highest first)
        results_df = results_df.sort_values('fraud_score', ascending=False)
        
        # Add summary statistics
        high_risk_count = len(results_df[results_df['fraud_score'] >= 0.8])
        medium_risk_count = len(results_df[(results_df['fraud_score'] >= 0.6) & (results_df['fraud_score'] < 0.8)])
        
        print(f"✅ Analysis complete:")
        print(f"   • Analyzed {len(results_df)} pharmacies")
        print(f"   • High risk (≥80%): {high_risk_count} pharmacies")
        print(f"   • Medium risk (60-79%): {medium_risk_count} pharmacies")
        
        return results_df
    
    def analyze_coverage_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze coverage type patterns in the data.
        
        Args:
            df (pd.DataFrame): Input claim data
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        # Stub analysis - will be implemented later
        return {
            'total_claims': len(df),
            'coverage_types': df.get('coverage_type', pd.Series()).value_counts().to_dict(),
            'analysis_status': 'STUB'
        } 
import pandas as pd
from typing import Dict, Any

class HighDollarClaimAgent:
    def __init__(self):
        self.name = "HighDollarClaimAgent"

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect high-dollar claims that might indicate rebate abuse or fraud.
        
        Args:
            df (pd.DataFrame): Raw claim data
            
        Returns:
            pd.DataFrame: High-dollar claim analysis results
        """
        if df.empty:
            return pd.DataFrame()
        
        print(f"💰 Analyzing high-dollar claims for {len(df)} claims...")
        
        # Filter for high-dollar claims
        high_dollar_claims = df[
            (df['copay_cost'] > 200) | 
            (df['oop_cost'] > 500) |
            (df['copay_fee_cost'] > 200) |
            (df['original_cost'] > 1000)
        ].copy()
        
        if high_dollar_claims.empty:
            print("⚠️ No high-dollar claims found")
            return pd.DataFrame()
        
        print(f"✅ Found {len(high_dollar_claims)} high-dollar claims")
        
        # Group by pharmacy for analysis
        pharmacy_groups = high_dollar_claims.groupby('pharmacy_number')
        results = []
        
        for pharmacy_number, group in pharmacy_groups:
            total_claims = len(group)
            total_cost = group['original_cost'].sum()
            avg_cost = group['original_cost'].mean()
            
            # Count claims by coverage type
            cash_not_covered = len(group[
                group['coverage_type'].isin(['Cash', 'Not Covered'])
            ])
            
            # Calculate risk metrics
            cash_percentage = (cash_not_covered / total_claims * 100) if total_claims > 0 else 0
            
            # Calculate fraud score based on multiple factors
            fraud_score = self._calculate_fraud_score(
                total_claims, total_cost, avg_cost, cash_percentage
            )
            
            # Determine reason
            reason = self._determine_reason(
                total_claims, total_cost, avg_cost, cash_percentage, fraud_score
            )
            
            # Get pharmacy details
            pharmacy_name = group['pharmacy_name'].iloc[0] if 'pharmacy_name' in group.columns else "Unknown"
            pharmacy_city = group['pharmacy_city'].iloc[0] if 'pharmacy_city' in group.columns else "Unknown"
            pharmacy_state = group['pharmacy_state'].iloc[0] if 'pharmacy_state' in group.columns else "Unknown"
            
            results.append({
                'pharmacy_number': pharmacy_number,
                'pharmacy_name': pharmacy_name,
                'pharmacy_city': pharmacy_city,
                'pharmacy_state': pharmacy_state,
                'total_high_dollar_claims': total_claims,
                'total_cost': round(total_cost, 2),
                'avg_claim_cost': round(avg_cost, 2),
                'cash_not_covered_count': cash_not_covered,
                'cash_percentage': round(cash_percentage, 2),
                'fraud_score': round(fraud_score, 3),
                'reason': reason,
                'analysis_type': 'high_dollar_claims'
            })
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('fraud_score', ascending=False)
        
        print(f"✅ High-dollar claim analysis complete:")
        print(f"   • Analyzed {len(results_df)} pharmacies with high-dollar claims")
        high_risk_count = len(results_df[results_df['fraud_score'] >= 0.8])
        medium_risk_count = len(results_df[(results_df['fraud_score'] >= 0.6) & (results_df['fraud_score'] < 0.8)])
        print(f"   • High risk (≥80%): {high_risk_count} pharmacies")
        print(f"   • Medium risk (60-79%): {medium_risk_count} pharmacies")
        
        return results_df

    def _calculate_fraud_score(self, total_claims: int, total_cost: float, 
                              avg_cost: float, cash_percentage: float) -> float:
        """
        Calculate fraud score based on multiple risk factors.
        
        Args:
            total_claims (int): Number of high-dollar claims
            total_cost (float): Total cost of high-dollar claims
            avg_cost (float): Average cost per claim
            cash_percentage (float): Percentage of cash/not covered claims
            
        Returns:
            float: Fraud score between 0 and 1
        """
        score = 0.0
        
        # Factor 1: Number of high-dollar claims (0-25 points)
        if total_claims >= 10:
            score += 0.25
        elif total_claims >= 5:
            score += 0.15
        elif total_claims >= 2:
            score += 0.10
        
        # Factor 2: Total cost (0-25 points)
        if total_cost >= 10000:
            score += 0.25
        elif total_cost >= 5000:
            score += 0.15
        elif total_cost >= 2000:
            score += 0.10
        
        # Factor 3: Average cost per claim (0-25 points)
        if avg_cost >= 1000:
            score += 0.25
        elif avg_cost >= 500:
            score += 0.15
        elif avg_cost >= 300:
            score += 0.10
        
        # Factor 4: Cash/Not Covered percentage (0-25 points)
        if cash_percentage >= 80:
            score += 0.25
        elif cash_percentage >= 60:
            score += 0.15
        elif cash_percentage >= 40:
            score += 0.10
        
        return min(score, 1.0)

    def _determine_reason(self, total_claims: int, total_cost: float, 
                         avg_cost: float, cash_percentage: float, fraud_score: float) -> str:
        """
        Determine the reason for the fraud score.
        
        Args:
            total_claims (int): Number of high-dollar claims
            total_cost (float): Total cost of high-dollar claims
            avg_cost (float): Average cost per claim
            cash_percentage (float): Percentage of cash/not covered claims
            fraud_score (float): Calculated fraud score
            
        Returns:
            str: Reason for the fraud score
        """
        if fraud_score >= 0.9:
            return "CRITICAL: Multiple high-risk factors - high volume, high cost, high cash percentage"
        elif fraud_score >= 0.8:
            return "HIGH_RISK: High-dollar claims with suspicious patterns"
        elif fraud_score >= 0.6:
            return "MEDIUM_HIGH: Elevated high-dollar claim activity"
        elif fraud_score >= 0.4:
            return "MEDIUM: Moderate high-dollar claim patterns"
        elif fraud_score >= 0.2:
            return "LOW_MEDIUM: Some high-dollar claims detected"
        else:
            return "LOW: Minimal high-dollar claim activity" 
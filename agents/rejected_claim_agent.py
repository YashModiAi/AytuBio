import pandas as pd
from typing import Dict, Any

class RejectedClaimDensityAgent:
    def __init__(self):
        self.name = "RejectedClaimDensityAgent"

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect pharmacies with high density of rejected claims that may indicate gaming.
        
        Args:
            df (pd.DataFrame): Raw claim data
            
        Returns:
            pd.DataFrame: Rejection density analysis results
        """
        if df.empty:
            return pd.DataFrame()
        
        print(f"🚫 Analyzing rejected claim density for {len(df)} claims...")
        
        # Create a rejection indicator column
        df_with_rejections = df.copy()
        df_with_rejections['has_rejection'] = self._has_rejection_indicator(df_with_rejections)
        
        # Count total claims and rejected claims per pharmacy
        pharmacy_groups = df_with_rejections.groupby('pharmacy_number')
        results = []
        
        for pharmacy_number, group in pharmacy_groups:
            total_claims = len(group)
            rejected_claims = group['has_rejection'].sum()
            rejection_percentage = (rejected_claims / total_claims * 100) if total_claims > 0 else 0
            
            # Only include pharmacies with some rejections
            if rejected_claims == 0:
                continue
            
            # Calculate fraud score based on rejection density
            fraud_score = self._calculate_fraud_score(
                total_claims, rejected_claims, rejection_percentage
            )
            
            # Determine reason
            reason = self._determine_reason(
                total_claims, rejected_claims, rejection_percentage, fraud_score
            )
            
            # Get pharmacy details
            pharmacy_name = group['pharmacy_name'].iloc[0] if 'pharmacy_name' in group.columns else "Unknown"
            pharmacy_city = group['pharmacy_city'].iloc[0] if 'pharmacy_city' in group.columns else "Unknown"
            pharmacy_state = group['pharmacy_state'].iloc[0] if 'pharmacy_state' in group.columns else "Unknown"
            
            # Analyze rejection types
            rejection_types = self._analyze_rejection_types(group)
            
            results.append({
                'pharmacy_number': pharmacy_number,
                'pharmacy_name': pharmacy_name,
                'pharmacy_city': pharmacy_city,
                'pharmacy_state': pharmacy_state,
                'total_claims': total_claims,
                'rejected_claims': rejected_claims,
                'rejection_percentage': round(rejection_percentage, 2),
                'fraud_score': round(fraud_score, 3),
                'reason': reason,
                'analysis_type': 'rejection_density',
                'primary_rejections': rejection_types['primary_rejections'],
                'pa_rejections': rejection_types['pa_rejections'],
                'status_rejections': rejection_types['status_rejections'],
                'total_rejection_types': rejection_types['total_types']
            })
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('fraud_score', ascending=False)
        
        print(f"✅ Rejection density analysis complete:")
        print(f"   • Analyzed {len(results_df)} pharmacies with rejections")
        high_risk_count = len(results_df[results_df['fraud_score'] >= 0.8])
        medium_risk_count = len(results_df[(results_df['fraud_score'] >= 0.6) & (results_df['fraud_score'] < 0.8)])
        print(f"   • High risk (≥80%): {high_risk_count} pharmacies")
        print(f"   • Medium risk (60-79%): {medium_risk_count} pharmacies")
        
        return results_df

    def _has_rejection_indicator(self, df: pd.DataFrame) -> pd.Series:
        """
        Check if each claim has any rejection indicators.
        
        Args:
            df (pd.DataFrame): Claim data
            
        Returns:
            pd.Series: Boolean series indicating if claim has rejection
        """
        # Check for primary rejection codes
        primary_rejections = (
            df['claim_cob_primary_reject_code1'].notna() & 
            (df['claim_cob_primary_reject_code1'] != '') |
            df['claim_cob_primary_reject_code2'].notna() & 
            (df['claim_cob_primary_reject_code2'] != '')
        )
        
        # Check for PA rejection codes
        pa_rejections = (
            df['pa_rejection_code_1'].notna() & 
            (df['pa_rejection_code_1'] != '') |
            df['pa_rejection_code_2'].notna() & 
            (df['pa_rejection_code_2'] != '')
        )
        
        # Check for PA status rejections
        status_rejections = (
            df['latest_pa_status_desc'].notna() &
            df['latest_pa_status_desc'].str.contains('reject|denied|failed', case=False, na=False)
        )
        
        # Combine all rejection indicators
        has_rejection = primary_rejections | pa_rejections | status_rejections
        
        return has_rejection

    def _analyze_rejection_types(self, group: pd.DataFrame) -> Dict[str, int]:
        """
        Analyze the types of rejections for a pharmacy.
        
        Args:
            group (pd.DataFrame): Pharmacy claim group
            
        Returns:
            Dict[str, int]: Count of different rejection types
        """
        primary_rejections = (
            (group['claim_cob_primary_reject_code1'].notna() & 
             (group['claim_cob_primary_reject_code1'] != '')).sum() +
            (group['claim_cob_primary_reject_code2'].notna() & 
             (group['claim_cob_primary_reject_code2'] != '')).sum()
        )
        
        pa_rejections = (
            (group['pa_rejection_code_1'].notna() & 
             (group['pa_rejection_code_1'] != '')).sum() +
            (group['pa_rejection_code_2'].notna() & 
             (group['pa_rejection_code_2'] != '')).sum()
        )
        
        status_rejections = (
            group['latest_pa_status_desc'].notna() &
            group['latest_pa_status_desc'].str.contains('reject|denied|failed', case=False, na=False)
        ).sum()
        
        total_types = primary_rejections + pa_rejections + status_rejections
        
        return {
            'primary_rejections': primary_rejections,
            'pa_rejections': pa_rejections,
            'status_rejections': status_rejections,
            'total_types': total_types
        }

    def _calculate_fraud_score(self, total_claims: int, rejected_claims: int, 
                              rejection_percentage: float) -> float:
        """
        Calculate fraud score based on rejection density.
        
        Args:
            total_claims (int): Total number of claims
            rejected_claims (int): Number of rejected claims
            rejection_percentage (float): Percentage of rejected claims
            
        Returns:
            float: Fraud score between 0 and 1
        """
        score = 0.0
        
        # Factor 1: Rejection percentage (0-40 points)
        if rejection_percentage >= 50:
            score += 0.4
        elif rejection_percentage >= 30:
            score += 0.3
        elif rejection_percentage >= 20:
            score += 0.2
        elif rejection_percentage >= 10:
            score += 0.1
        
        # Factor 2: Volume of rejections (0-30 points)
        if rejected_claims >= 20:
            score += 0.3
        elif rejected_claims >= 10:
            score += 0.2
        elif rejected_claims >= 5:
            score += 0.1
        
        # Factor 3: Total claim volume (0-30 points)
        if total_claims >= 50:
            score += 0.3
        elif total_claims >= 20:
            score += 0.2
        elif total_claims >= 10:
            score += 0.1
        
        return min(score, 1.0)

    def _determine_reason(self, total_claims: int, rejected_claims: int, 
                         rejection_percentage: float, fraud_score: float) -> str:
        """
        Determine the reason for the fraud score.
        
        Args:
            total_claims (int): Total number of claims
            rejected_claims (int): Number of rejected claims
            rejection_percentage (float): Percentage of rejected claims
            fraud_score (float): Calculated fraud score
            
        Returns:
            str: Reason for the fraud score
        """
        if fraud_score >= 0.9:
            return "CRITICAL: Extremely high rejection rate with large volume"
        elif fraud_score >= 0.8:
            return "HIGH_RISK: High rejection density indicating potential gaming"
        elif fraud_score >= 0.6:
            return "MEDIUM_HIGH: Elevated rejection patterns"
        elif fraud_score >= 0.4:
            return "MEDIUM: Moderate rejection density"
        elif fraud_score >= 0.2:
            return "LOW_MEDIUM: Some rejection patterns detected"
        else:
            return "LOW: Minimal rejection activity" 
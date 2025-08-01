import pandas as pd
from typing import Dict, Any
from datetime import datetime

class PatientFlipAgent:
    """
    Agent for detecting insurance-to-cash flip fraud patterns.
    Identifies when pharmacies start claims with insurance, get rejected,
    and then switch to cash payments for the same patient/drug combination.
    """

    def __init__(self):
        self.name = "PatientFlipAgent"

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()

        print(f"🔍 Analyzing insurance-to-cash flip patterns for {len(df)} claims...")

        # Step 1: Normalize coverage types
        COVERAGE_TYPE_MAP = {
            "Well Covered": "Commercial",
            "Covered - HD": "Commercial",
            "Covered – LD": "Commercial",
            "Trade": "Cash",
            "Retail": "Cash",
            "Not Covered": "Cash",
            "Cash": "Cash"
        }

        df["normalized_coverage_type"] = df["coverage_type"].map(COVERAGE_TYPE_MAP).fillna(df["coverage_type"])

        relevant_coverage_types = ["Cash", "Not Covered", "Commercial", "Medicare", "Medicaid"]
        filtered_df = df[df['normalized_coverage_type'].isin(relevant_coverage_types)].copy()

        if filtered_df.empty:
            print("⚠️ No relevant coverage types found")
            return pd.DataFrame()

        print(f"✅ Filtered to {len(filtered_df)} claims with relevant coverage types")

        group_columns = ['patient_id', 'product_ndc', 'pharmacy_number']
        groups = filtered_df.groupby(group_columns)

        results = []
        total_groups = len(groups)
        for idx, (group_key, group) in enumerate(groups):
            if idx % 100 == 0:
                print(f"   Processing group {idx}/{total_groups}")

            if len(group) < 2:
                continue

            group_sorted = group.sort_values('date_submitted')
            flip_detected, flip_count, fraud_score, reason = self._analyze_flip_pattern(group_sorted)

            if flip_detected:
                results.append({
                    'patient_id': group_key[0],
                    'pharmacy_number': group_key[2],
                    'pharmacy_name': group_sorted['pharmacy_name'].iloc[0] if 'pharmacy_name' in group_sorted.columns else "Unknown",
                    'pharmacy_city': group_sorted['pharmacy_city'].iloc[0] if 'pharmacy_city' in group_sorted.columns else "Unknown",
                    'pharmacy_state': group_sorted['pharmacy_state'].iloc[0] if 'pharmacy_state' in group_sorted.columns else "Unknown",
                    'product_ndc': group_key[1],
                    'product_name': group_sorted['product_name'].iloc[0] if 'product_name' in group_sorted.columns else "Unknown",
                    'number_of_flips': flip_count,
                    'total_claims': len(group_sorted),
                    'fraud_score': round(fraud_score, 3),
                    'reason': reason,
                    'analysis_type': 'flip_pattern'
                })

        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('fraud_score', ascending=False)
            print(f"✅ Flip pattern analysis complete:")
            print(f"   • Analyzed {total_groups} groups")
            print(f"   • Detected {len(results_df)} flip patterns")
        else:
            print("✅ No flip patterns detected")

        return results_df

    def _analyze_flip_pattern(self, group_sorted: pd.DataFrame) -> tuple:
        flip_detected = False
        flip_count = 0
        fraud_score = 0.0
        reason = "No flip pattern detected"

        insurance_claims = []
        cash_claims = []

        for _, claim in group_sorted.iterrows():
            ctype = str(claim.get('normalized_coverage_type', '')).strip()
            if ctype in ["Commercial", "Medicare", "Medicaid"]:
                insurance_claims.append(claim)
            elif ctype in ["Cash", "Not Covered"]:
                cash_claims.append(claim)

        if insurance_claims and cash_claims:
            earliest_ins = min(insurance_claims, key=lambda x: x['date_submitted'])
            earliest_cash = min(cash_claims, key=lambda x: x['date_submitted'])

            if earliest_cash['date_submitted'] > earliest_ins['date_submitted']:
                if self._has_rejection_pattern(insurance_claims):
                    flip_detected = True
                    flip_count = len(cash_claims)
                    flip_ratio = flip_count / len(group_sorted)

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

        return flip_detected, flip_count, fraud_score, reason

    def _has_rejection_pattern(self, insurance_claims: list) -> bool:
        for claim in insurance_claims:
            pa_reject_1 = claim.get('pa_rejection_code_1', '')
            pa_reject_2 = claim.get('pa_rejection_code_2', '')
            pa_status_code = claim.get('latest_pa_status_code', '')
            pa_status_desc = str(claim.get('latest_pa_status_desc', '')).lower()
            cob_reject_1 = claim.get('claim_cob_primary_reject_code1', '')
            cob_reject_2 = claim.get('claim_cob_primary_reject_code2', '')

            if (pa_reject_1 or pa_reject_2 or pa_status_code or 
                'reject' in pa_status_desc or 'denied' in pa_status_desc or 
                cob_reject_1 or cob_reject_2):
                print(f"🔎 Rejection match — PA desc: {pa_status_desc}, PA code: {pa_reject_1}, COB reject: {cob_reject_1}")
                return True

        return False

    def analyze_flip_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        results_df = self.run(df)
        if results_df.empty:
            return {
                'total_patterns': 0,
                'high_risk_patterns': 0,
                'medium_risk_patterns': 0,
                'avg_fraud_score': 0.0,
                'analysis_status': 'NO_PATTERNS'
            }

        high = len(results_df[results_df['fraud_score'] >= 0.8])
        med = len(results_df[(results_df['fraud_score'] >= 0.6) & (results_df['fraud_score'] < 0.8)])

        return {
            'total_patterns': len(results_df),
            'high_risk_patterns': high,
            'medium_risk_patterns': med,
            'avg_fraud_score': round(results_df['fraud_score'].mean(), 3),
            'analysis_status': 'PATTERNS_DETECTED'
        }
 
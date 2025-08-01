import pandas as pd
from typing import Dict, Any

class PharmacyNetworkAnomalyAgent:
    def __init__(self):
        self.name = "PharmacyNetworkAnomalyAgent"

    def run(self, df: pd.DataFrame, combined_results: pd.DataFrame = None) -> pd.DataFrame:
        """
        Detect non-network pharmacies with unusual fraud signals.
        
        Args:
            df (pd.DataFrame): Raw claim data
            combined_results (pd.DataFrame): Results from other agents (optional)
            
        Returns:
            pd.DataFrame: Network anomaly analysis results
        """
        if df.empty:
            return pd.DataFrame()
        
        print(f"🏥 Analyzing pharmacy network anomalies for {len(df)} claims...")
        
        # Check if network columns exist
        network_columns = ['is_network_pharmacy', 'network_pharmacy_group_type']
        missing_columns = [col for col in network_columns if col not in df.columns]
        
        if missing_columns:
            print(f"⚠️ Missing network columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            return pd.DataFrame()
        
        # Analyze network vs non-network pharmacies
        pharmacy_network_analysis = self._analyze_network_pharmacies(df)
        
        # If we have combined results from other agents, enhance the analysis
        if combined_results is not None and not combined_results.empty:
            enhanced_results = self._enhance_with_agent_results(
                pharmacy_network_analysis, combined_results
            )
            return enhanced_results
        
        return pharmacy_network_analysis

    def _analyze_network_pharmacies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Analyze network vs non-network pharmacy patterns.
        
        Args:
            df (pd.DataFrame): Raw claim data
            
        Returns:
            pd.DataFrame: Network analysis results
        """
        # Group by pharmacy and analyze network status
        pharmacy_groups = df.groupby('pharmacy_number')
        results = []
        
        for pharmacy_number, group in pharmacy_groups:
            total_claims = len(group)
            
            # Analyze network status (using 'Y'/'N' values)
            network_pharmacies = group[group['is_network_pharmacy'] == 'Y']
            non_network_pharmacies = group[group['is_network_pharmacy'] == 'N']
            
            network_claim_count = len(network_pharmacies)
            non_network_claim_count = len(non_network_pharmacies)
            
            # Determine primary network status (majority of claims)
            is_primarily_network = network_claim_count > non_network_claim_count
            
            # Get network group type
            network_group_types = group['network_pharmacy_group_type'].dropna().unique()
            primary_network_type = network_group_types[0] if len(network_group_types) > 0 else "Unknown"
            
            # Calculate fraud indicators based on network status
            fraud_score = self._calculate_network_fraud_score(
                total_claims, network_claim_count, non_network_claim_count,
                is_primarily_network, primary_network_type
            )
            
            # Determine reason
            reason = self._determine_network_reason(
                total_claims, network_claim_count, non_network_claim_count,
                is_primarily_network, primary_network_type, fraud_score
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
                'total_claims': total_claims,
                'network_claims': network_claim_count,
                'non_network_claims': non_network_claim_count,
                'network_percentage': round((network_claim_count / total_claims * 100), 2) if total_claims > 0 else 0,
                'is_primarily_network': is_primarily_network,
                'primary_network_type': primary_network_type,
                'fraud_score': round(fraud_score, 3),
                'reason': reason,
                'analysis_type': 'network_anomaly'
            })
        
        results_df = pd.DataFrame(results)
        if not results_df.empty:
            results_df = results_df.sort_values('fraud_score', ascending=False)
        
        print(f"✅ Network anomaly analysis complete:")
        print(f"   • Analyzed {len(results_df)} pharmacies")
        high_risk_count = len(results_df[results_df['fraud_score'] >= 0.8])
        medium_risk_count = len(results_df[(results_df['fraud_score'] >= 0.6) & (results_df['fraud_score'] < 0.8)])
        print(f"   • High risk (≥80%): {high_risk_count} pharmacies")
        print(f"   • Medium risk (60-79%): {medium_risk_count} pharmacies")
        
        return results_df

    def _enhance_with_agent_results(self, network_results: pd.DataFrame, 
                                   combined_results: pd.DataFrame) -> pd.DataFrame:
        """
        Enhance network analysis with results from other agents.
        
        Args:
            network_results (pd.DataFrame): Network analysis results
            combined_results (pd.DataFrame): Results from other agents
            
        Returns:
            pd.DataFrame: Enhanced network anomaly results
        """
        print("🔗 Enhancing network analysis with agent results...")
        
        # Merge network results with combined agent results
        enhanced_results = []
        
        for _, network_row in network_results.iterrows():
            pharmacy_number = network_row['pharmacy_number']
            
            # Find matching results from other agents
            agent_results = combined_results[combined_results['pharmacy_number'] == pharmacy_number]
            
            if not agent_results.empty:
                # Calculate enhanced fraud score
                network_score = network_row['fraud_score']
                agent_scores = agent_results['fraud_score'].tolist()
                avg_agent_score = sum(agent_scores) / len(agent_scores) if agent_scores else 0
                
                # Enhanced fraud score combines network and agent scores
                enhanced_score = (network_score * 0.3) + (avg_agent_score * 0.7)
                
                # Count agent findings
                agent_count = len(agent_results)
                high_risk_agents = len(agent_results[agent_results['fraud_score'] >= 0.8])
                
                # Determine enhanced reason
                enhanced_reason = self._determine_enhanced_reason(
                    network_row, agent_count, high_risk_agents, enhanced_score
                )
                
                enhanced_results.append({
                    'pharmacy_number': pharmacy_number,
                    'pharmacy_name': network_row['pharmacy_name'],
                    'pharmacy_city': network_row['pharmacy_city'],
                    'pharmacy_state': network_row['pharmacy_state'],
                    'total_claims': network_row['total_claims'],
                    'network_claims': network_row['network_claims'],
                    'non_network_claims': network_row['non_network_claims'],
                    'network_percentage': network_row['network_percentage'],
                    'is_primarily_network': network_row['is_primarily_network'],
                    'primary_network_type': network_row['primary_network_type'],
                    'network_fraud_score': network_row['fraud_score'],
                    'agent_fraud_score': round(avg_agent_score, 3),
                    'agent_count': agent_count,
                    'high_risk_agents': high_risk_agents,
                    'fraud_score': round(enhanced_score, 3),
                    'reason': enhanced_reason,
                    'analysis_type': 'network_anomaly_enhanced'
                })
            else:
                # No agent results, use original network score
                enhanced_results.append({
                    'pharmacy_number': pharmacy_number,
                    'pharmacy_name': network_row['pharmacy_name'],
                    'pharmacy_city': network_row['pharmacy_city'],
                    'pharmacy_state': network_row['pharmacy_state'],
                    'total_claims': network_row['total_claims'],
                    'network_claims': network_row['network_claims'],
                    'non_network_claims': network_row['non_network_claims'],
                    'network_percentage': network_row['network_percentage'],
                    'is_primarily_network': network_row['is_primarily_network'],
                    'primary_network_type': network_row['primary_network_type'],
                    'network_fraud_score': network_row['fraud_score'],
                    'agent_fraud_score': 0.0,
                    'agent_count': 0,
                    'high_risk_agents': 0,
                    'fraud_score': network_row['fraud_score'],
                    'reason': network_row['reason'] + " (No agent findings)",
                    'analysis_type': 'network_anomaly_enhanced'
                })
        
        enhanced_df = pd.DataFrame(enhanced_results)
        if not enhanced_df.empty:
            enhanced_df = enhanced_df.sort_values('fraud_score', ascending=False)
        
        print(f"✅ Enhanced network analysis complete:")
        print(f"   • Enhanced {len(enhanced_df)} pharmacies with agent data")
        high_risk_count = len(enhanced_df[enhanced_df['fraud_score'] >= 0.8])
        medium_risk_count = len(enhanced_df[(enhanced_df['fraud_score'] >= 0.6) & (enhanced_df['fraud_score'] < 0.8)])
        print(f"   • High risk (≥80%): {high_risk_count} pharmacies")
        print(f"   • Medium risk (60-79%): {medium_risk_count} pharmacies")
        
        return enhanced_df

    def _calculate_network_fraud_score(self, total_claims: int, network_claims: int, 
                                     non_network_claims: int, is_primarily_network: bool,
                                     network_type: str) -> float:
        """
        Calculate fraud score based on network patterns.
        
        Args:
            total_claims (int): Total number of claims
            network_claims (int): Number of network claims
            non_network_claims (int): Number of non-network claims
            is_primarily_network (bool): Whether pharmacy is primarily network
            network_type (str): Network group type
            
        Returns:
            float: Fraud score between 0 and 1
        """
        score = 0.0
        
        # Factor 1: Non-network claim percentage (0-40 points)
        non_network_percentage = (non_network_claims / total_claims * 100) if total_claims > 0 else 0
        
        if non_network_percentage >= 80:
            score += 0.4
        elif non_network_percentage >= 60:
            score += 0.3
        elif non_network_percentage >= 40:
            score += 0.2
        elif non_network_percentage >= 20:
            score += 0.1
        
        # Factor 2: Network type anomalies (0-30 points)
        if network_type in ["Unknown", "None", ""] and total_claims > 5:
            score += 0.3
        elif network_type in ["Independent", "Small Chain"] and non_network_percentage > 50:
            score += 0.2
        
        # Factor 3: Claim volume patterns (0-30 points)
        if total_claims >= 50 and non_network_percentage > 30:
            score += 0.3
        elif total_claims >= 20 and non_network_percentage > 50:
            score += 0.2
        elif total_claims >= 10 and non_network_percentage > 70:
            score += 0.1
        
        return min(score, 1.0)

    def _determine_network_reason(self, total_claims: int, network_claims: int,
                                non_network_claims: int, is_primarily_network: bool,
                                network_type: str, fraud_score: float) -> str:
        """
        Determine the reason for the network fraud score.
        
        Args:
            total_claims (int): Total number of claims
            network_claims (int): Number of network claims
            non_network_claims (int): Number of non-network claims
            is_primarily_network (bool): Whether pharmacy is primarily network
            network_type (str): Network group type
            fraud_score (float): Calculated fraud score
            
        Returns:
            str: Reason for the fraud score
        """
        non_network_percentage = (non_network_claims / total_claims * 100) if total_claims > 0 else 0
        
        if fraud_score >= 0.9:
            return "CRITICAL: High non-network activity with suspicious patterns"
        elif fraud_score >= 0.8:
            return "HIGH_RISK: Elevated non-network claim patterns"
        elif fraud_score >= 0.6:
            return "MEDIUM_HIGH: Unusual network/non-network distribution"
        elif fraud_score >= 0.4:
            return "MEDIUM: Some network anomalies detected"
        elif fraud_score >= 0.2:
            return "LOW_MEDIUM: Minor network pattern variations"
        else:
            return "LOW: Normal network patterns"

    def _determine_enhanced_reason(self, network_row: pd.Series, agent_count: int,
                                 high_risk_agents: int, enhanced_score: float) -> str:
        """
        Determine enhanced reason combining network and agent results.
        
        Args:
            network_row (pd.Series): Network analysis row
            agent_count (int): Number of agents that flagged this pharmacy
            high_risk_agents (int): Number of high-risk agent findings
            enhanced_score (float): Enhanced fraud score
            
        Returns:
            str: Enhanced reason
        """
        non_network_percentage = network_row['network_percentage']
        
        if enhanced_score >= 0.9:
            return f"CRITICAL: Non-network pharmacy ({100-non_network_percentage:.1f}% non-network) with {high_risk_agents} high-risk agent findings"
        elif enhanced_score >= 0.8:
            return f"HIGH_RISK: Non-network pharmacy with {agent_count} agent findings ({high_risk_agents} high-risk)"
        elif enhanced_score >= 0.6:
            return f"MEDIUM_HIGH: Network anomaly with {agent_count} agent findings"
        elif enhanced_score >= 0.4:
            return f"MEDIUM: Some network and agent concerns"
        elif enhanced_score >= 0.2:
            return f"LOW_MEDIUM: Minor network and agent issues"
        else:
            return f"LOW: Minimal network and agent concerns" 
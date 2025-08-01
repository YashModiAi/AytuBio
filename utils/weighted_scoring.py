import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import concurrent.futures
from agents.coverage_agent import CoverageTypeAgent
from agents.patient_flip_agent_enhanced import PatientFlipAgentEnhanced
from agents.high_dollar_agent import HighDollarClaimAgent
from agents.rejected_claim_agent import RejectedClaimDensityAgent
from agents.network_anomaly_agent import PharmacyNetworkAnomalyAgent
from utils.db_loader import AzureSynapseLoader
from utils.langsmith_integration import langsmith_tracker


class WeightedScoringSystem:
    def __init__(self):
        self.default_weights = {
            'coverage_agent': 0.25,
            'patient_flip_agent': 0.20,
            'high_dollar_agent': 0.20,
            'rejection_agent': 0.20,
            'network_agent': 0.15
        }
        self.current_weights = self.default_weights.copy()
        self.agents = {
            'coverage_agent': CoverageTypeAgent(),
            'patient_flip_agent': PatientFlipAgentEnhanced(),
            'high_dollar_agent': HighDollarClaimAgent(),
            'rejection_agent': RejectedClaimDensityAgent(),
            'network_agent': PharmacyNetworkAnomalyAgent()
        }
    
    def update_weights(self, new_weights: Dict[str, float]):
        """Update agent weights from UI."""
        self.current_weights.update(new_weights)
        # Normalize weights to sum to 1.0
        total = sum(self.current_weights.values())
        if total > 0:
            self.current_weights = {k: v/total for k, v in self.current_weights.items()}
    
    def run_agents_parallel(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Execute all agents in parallel."""
        print("🚀 Running agents in parallel...")
        
        # Start LangSmith tracking
        langsmith_tracker.start_project_run("Parallel Fraud Detection with Supervisor")
        
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_agent = {
                executor.submit(self._run_single_agent, agent_name, agent, df): agent_name 
                for agent_name, agent in self.agents.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_agent):
                agent_name = future_to_agent[future]
                try:
                    agent_results = future.result()
                    results[agent_name] = agent_results
                    
                    # Track agent run in LangSmith
                    langsmith_tracker.track_agent_run(
                        agent_name=agent_name,
                        input_data={"data_shape": df.shape, "columns": list(df.columns)},
                        output_data={
                            "findings_count": len(agent_results),
                            "columns": list(agent_results.columns) if not agent_results.empty else [],
                            "sample_findings": agent_results.head(3).to_dict() if not agent_results.empty else {}
                        }
                    )
                    
                    print(f"✅ {agent_name} completed: {len(agent_results)} findings")
                except Exception as e:
                    print(f"❌ Error in {agent_name}: {e}")
                    results[agent_name] = pd.DataFrame()
        
        return results
    
    def _run_single_agent(self, agent_name: str, agent, df: pd.DataFrame) -> pd.DataFrame:
        """Run a single agent with error handling."""
        try:
            if agent_name == 'network_agent':
                # Network agent needs combined results from other agents
                return agent.run(df, pd.DataFrame())  # Will be enhanced later
            else:
                return agent.run(df)
        except Exception as e:
            print(f"❌ Error running {agent_name}: {e}")
            return pd.DataFrame()
    
    def calculate_weighted_scores(self, agent_results: Dict[str, pd.DataFrame], df: pd.DataFrame) -> pd.DataFrame:
        """Calculate weighted scores for all pharmacies."""
        print("⚖️ Calculating weighted scores...")
        
        # Get all unique pharmacies from all agents
        all_pharmacies = set()
        for results_df in agent_results.values():
            if not results_df.empty and 'pharmacy_number' in results_df.columns:
                all_pharmacies.update(results_df['pharmacy_number'].unique())
        
        weighted_results = []
        
        for pharmacy_number in all_pharmacies:
            pharmacy_result = self._calculate_single_pharmacy_score(
                pharmacy_number, agent_results, df
            )
            weighted_results.append(pharmacy_result)
        
        weighted_df = pd.DataFrame(weighted_results)
        
        # Track weighted scoring in LangSmith
        langsmith_tracker.track_weighted_scoring(
            agent_results=agent_results,
            weighted_results=weighted_df,
            weights=self.current_weights
        )
        
        return weighted_df
    
    def _calculate_single_pharmacy_score(self, pharmacy_number: str, agent_results: Dict[str, pd.DataFrame], df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate weighted score for a single pharmacy."""
        pharmacy_scores = {}
        pharmacy_reasons = {}
        pharmacy_details = {}
        
        # Collect scores and reasons from each agent
        for agent_name, results_df in agent_results.items():
            if not results_df.empty and 'pharmacy_number' in results_df.columns:
                pharmacy_data = results_df[results_df['pharmacy_number'] == pharmacy_number]
                if not pharmacy_data.empty:
                    pharmacy_scores[agent_name] = pharmacy_data['fraud_score'].iloc[0]
                    pharmacy_reasons[agent_name] = pharmacy_data['reason'].iloc[0]
                    pharmacy_details[agent_name] = pharmacy_data.iloc[0].to_dict()
        
        # Calculate weighted score
        weighted_score = 0.0
        contributing_agents = []
        
        for agent_name, score in pharmacy_scores.items():
            weight = self.current_weights.get(agent_name, 0.0)
            weighted_score += score * weight
            contributing_agents.append(agent_name)
        
        # Cross-agent consistency check
        consistency_score = self._calculate_consistency_score(pharmacy_scores)
        
        # Outlier detection
        outlier_score = self._calculate_outlier_score(pharmacy_number, agent_results)
        
        # Track cross-agent communication for this pharmacy
        langsmith_tracker.track_cross_agent_communication(
            pharmacy_number=pharmacy_number,
            agent_scores=pharmacy_scores,
            consistency_score=consistency_score,
            outlier_score=outlier_score
        )
        
        # Final aggregated score
        final_score = (weighted_score * 0.7) + (consistency_score * 0.2) + (outlier_score * 0.1)
        
        # Get pharmacy transactions
        pharmacy_transactions = self._get_pharmacy_transactions(pharmacy_number, df)
        
        # Generate fraud explanation
        fraud_explanation = self._generate_fraud_explanation(pharmacy_scores, pharmacy_reasons, pharmacy_transactions)
        
        return {
            'pharmacy_number': pharmacy_number,
            'pharmacy_name': pharmacy_details.get('coverage_agent', {}).get('pharmacy_name', 'Unknown'),
            'pharmacy_city': pharmacy_details.get('coverage_agent', {}).get('pharmacy_city', 'Unknown'),
            'pharmacy_state': pharmacy_details.get('coverage_agent', {}).get('pharmacy_state', 'Unknown'),
            'weighted_score': round(final_score, 3),
            'contributing_agents': contributing_agents,
            'agent_scores': pharmacy_scores,
            'agent_reasons': pharmacy_reasons,
            'consistency_score': round(consistency_score, 3),
            'outlier_score': round(outlier_score, 3),
            'fraud_explanation': fraud_explanation,
            'transaction_count': len(pharmacy_transactions),
            'risk_level': self._determine_risk_level(final_score)
        }
    
    def _calculate_consistency_score(self, pharmacy_scores: Dict[str, float]) -> float:
        """Calculate consistency across agents (prevent double-penalizing)."""
        if len(pharmacy_scores) < 2:
            return 0.5  # Neutral if only one agent
        
        # Check for conflicting signals
        high_scores = [s for s in pharmacy_scores.values() if s >= 0.8]
        low_scores = [s for s in pharmacy_scores.values() if s < 0.4]
        
        if high_scores and low_scores:
            return 0.3  # Inconsistent signals
        elif high_scores:
            return 0.9  # Consistent high risk
        elif low_scores:
            return 0.1  # Consistent low risk
        else:
            return 0.5  # Mixed signals
    
    def _calculate_outlier_score(self, pharmacy_number: str, agent_results: Dict[str, pd.DataFrame]) -> float:
        """Calculate outlier score using Z-scores."""
        all_scores = []
        
        for agent_name, results_df in agent_results.items():
            if not results_df.empty and 'fraud_score' in results_df.columns:
                all_scores.extend(results_df['fraud_score'].tolist())
        
        if not all_scores:
            return 0.5
        
        mean_score = np.mean(all_scores)
        std_score = np.std(all_scores)
        
        if std_score == 0:
            return 0.5
        
        # Find this pharmacy's average score
        pharmacy_scores = []
        for agent_name, results_df in agent_results.items():
            if not results_df.empty and 'pharmacy_number' in results_df.columns:
                pharmacy_data = results_df[results_df['pharmacy_number'] == pharmacy_number]
                if not pharmacy_data.empty:
                    pharmacy_scores.append(pharmacy_data['fraud_score'].iloc[0])
        
        if not pharmacy_scores:
            return 0.5
        
        avg_pharmacy_score = np.mean(pharmacy_scores)
        z_score = (avg_pharmacy_score - mean_score) / std_score
        
        # Convert Z-score to 0-1 scale
        outlier_score = 1 / (1 + np.exp(-z_score))  # Sigmoid function
        return outlier_score
    
    def _get_pharmacy_transactions(self, pharmacy_number: str, df: pd.DataFrame) -> pd.DataFrame:
        """Get all transactions for a specific pharmacy."""
        if 'pharmacy_number' in df.columns:
            pharmacy_transactions = df[df['pharmacy_number'] == pharmacy_number].copy()
            return pharmacy_transactions
        return pd.DataFrame()
    
    def _generate_fraud_explanation(self, scores: Dict[str, float], reasons: Dict[str, str], transactions: pd.DataFrame) -> str:
        """Generate detailed fraud explanation."""
        high_risk_agents = [agent for agent, score in scores.items() if score >= 0.8]
        medium_risk_agents = [agent for agent, score in scores.items() if 0.6 <= score < 0.8]
        
        explanation_parts = []
        
        if high_risk_agents:
            agent_reasons = [reasons.get(agent, "High risk") for agent in high_risk_agents]
            explanation_parts.append(f"🚨 HIGH RISK from {len(high_risk_agents)} agents: {', '.join(agent_reasons)}")
        
        if medium_risk_agents:
            agent_reasons = [reasons.get(agent, "Medium risk") for agent in medium_risk_agents]
            explanation_parts.append(f"⚠️ MEDIUM RISK from {len(medium_risk_agents)} agents: {', '.join(agent_reasons)}")
        
        # Add transaction insights
        if not transactions.empty:
            total_claims = len(transactions)
            cash_claims = len(transactions[transactions['coverage_type'].isin(['Cash', 'Not Covered'])])
            high_dollar_claims = len(transactions[
                (transactions['copay_cost'] > 200) | (transactions['oop_cost'] > 500)
            ])
            
            transaction_insights = []
            if cash_claims > 0:
                cash_percent = (cash_claims / total_claims) * 100
                transaction_insights.append(f"{cash_percent:.1f}% cash/not covered claims")
            if high_dollar_claims > 0:
                high_dollar_percent = (high_dollar_claims / total_claims) * 100
                transaction_insights.append(f"{high_dollar_percent:.1f}% high-dollar claims")
            
            if transaction_insights:
                explanation_parts.append(f"📊 Transaction Analysis: {', '.join(transaction_insights)}")
        
        if not explanation_parts:
            explanation_parts.append("Multiple agent analysis completed - no significant fraud indicators detected")
        
        return " | ".join(explanation_parts)
    
    def _determine_risk_level(self, score: float) -> str:
        """Determine risk level based on weighted score."""
        if score >= 0.8:
            return "HIGH RISK"
        elif score >= 0.6:
            return "MEDIUM RISK"
        elif score >= 0.4:
            return "LOW RISK"
        else:
            return "VERY LOW RISK"


class SupervisorAgent:
    def __init__(self):
        self.scoring_system = WeightedScoringSystem()
    
    def supervise_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Supervise the entire fraud detection process."""
        print("👨‍💼 Supervisor starting analysis...")
        
        # Run agents in parallel
        agent_results = self.scoring_system.run_agents_parallel(df)
        
        # Calculate weighted scores
        weighted_results = self.scoring_system.calculate_weighted_scores(agent_results, df)
        
        # Generate supervisor insights
        supervisor_insights = self._generate_supervisor_insights(weighted_results, agent_results)
        
        # End LangSmith tracking
        final_results = {
            'agent_results': agent_results,
            'weighted_results': weighted_results,
            'supervisor_insights': supervisor_insights,
            'scoring_system': self.scoring_system
        }
        
        langsmith_tracker.end_project_run(final_results)
        
        # Print LangSmith URL
        print(f"📊 View detailed run at: {langsmith_tracker.get_run_url()}")
        
        return final_results
    
    def _generate_supervisor_insights(self, weighted_results: pd.DataFrame, agent_results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate supervisor insights and recommendations."""
        insights = {
            'total_pharmacies_analyzed': len(weighted_results),
            'high_risk_pharmacies': len(weighted_results[weighted_results['weighted_score'] >= 0.8]),
            'medium_risk_pharmacies': len(weighted_results[
                (weighted_results['weighted_score'] >= 0.6) & (weighted_results['weighted_score'] < 0.8)
            ]),
            'agent_performance': {},
            'cross_agent_patterns': {},
            'recommendations': []
        }
        
        # Analyze agent performance
        for agent_name, results_df in agent_results.items():
            if not results_df.empty:
                avg_score = results_df['fraud_score'].mean()
                high_risk_count = len(results_df[results_df['fraud_score'] >= 0.8])
                insights['agent_performance'][agent_name] = {
                    'avg_score': round(avg_score, 3),
                    'high_risk_findings': high_risk_count,
                    'total_findings': len(results_df)
                }
        
        # Analyze cross-agent patterns
        cross_agent_analysis = self._analyze_cross_agent_patterns(weighted_results, agent_results)
        insights['cross_agent_patterns'] = cross_agent_analysis
        
        # Generate recommendations
        if insights['high_risk_pharmacies'] > 10:
            insights['recommendations'].append("High number of high-risk pharmacies detected - consider manual review")
        
        if insights['medium_risk_pharmacies'] > 20:
            insights['recommendations'].append("Many medium-risk pharmacies - consider adjusting thresholds")
        
        # Add supervisor-specific recommendations
        if cross_agent_analysis.get('conflicting_signals_count', 0) > 5:
            insights['recommendations'].append("Multiple conflicting signals detected - review agent weights")
        
        if cross_agent_analysis.get('high_consistency_count', 0) > 10:
            insights['recommendations'].append("High agent agreement detected - consider increasing confidence threshold")
        
        # Track supervisor analysis in LangSmith
        langsmith_tracker.track_supervisor_analysis(
            agent_results=agent_results,
            weighted_results=weighted_results,
            insights=insights
        )
        
        return insights
    
    def _analyze_cross_agent_patterns(self, weighted_results: pd.DataFrame, agent_results: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze patterns across agents for supervisor insights."""
        patterns = {
            'conflicting_signals_count': 0,
            'high_consistency_count': 0,
            'agent_agreement_analysis': {},
            'double_penalty_instances': 0
        }
        
        # Analyze each pharmacy for cross-agent patterns
        for _, row in weighted_results.iterrows():
            pharmacy_number = row['pharmacy_number']
            agent_scores = row.get('agent_scores', {})
            
            if agent_scores:
                high_risk_agents = [agent for agent, score in agent_scores.items() if score >= 0.8]
                low_risk_agents = [agent for agent, score in agent_scores.items() if score < 0.4]
                
                # Check for conflicting signals
                if high_risk_agents and low_risk_agents:
                    patterns['conflicting_signals_count'] += 1
                
                # Check for high consistency
                if len(high_risk_agents) >= 3 or len(low_risk_agents) >= 3:
                    patterns['high_consistency_count'] += 1
                
                # Check for double penalty (same pattern flagged by multiple agents)
                if 'coverage_agent' in high_risk_agents and 'patient_flip_agent' in high_risk_agents:
                    patterns['double_penalty_instances'] += 1
        
        return patterns 
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from langsmith import Client
from langsmith.run_trees import RunTree


class LangSmithTracker:
    def __init__(self, project_name: str = "fraud-detection-system"):
        """Initialize LangSmith tracking."""
        self.project_name = project_name
        self.client = Client()
        self.current_run_tree = None
        self.agent_runs = {}
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def start_project_run(self, description: str = "Fraud Detection Pipeline") -> str:
        """Start a new project run."""
        try:
            self.current_run_tree = RunTree(
                name="fraud-detection-pipeline",
                description=description,
                project_name=self.project_name,
                tags=["fraud-detection", "parallel-agents", "supervisor"]
            )
            self.logger.info(f"🚀 Started LangSmith project run: {self.current_run_tree.id}")
            return self.current_run_tree.id
        except Exception as e:
            self.logger.error(f"❌ Error starting LangSmith run: {e}")
            return None
    
    def track_agent_run(self, agent_name: str, input_data: Dict[str, Any], 
                       output_data: Dict[str, Any]) -> str:
        """Track an individual agent run."""
        try:
            if not self.current_run_tree:
                self.start_project_run()
            
            run_id = f"{agent_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create agent run
            agent_run = self.current_run_tree.create_child(
                name=f"{agent_name}-execution",
                inputs=input_data,
                outputs=output_data,
                tags=[agent_name, "agent-execution"]
            )
            
            self.agent_runs[agent_name] = agent_run
            self.logger.info(f"📊 Tracked {agent_name} run: {agent_run.id}")
            return agent_run.id
            
        except Exception as e:
            self.logger.error(f"❌ Error tracking {agent_name} run: {e}")
            return None
    
    def track_supervisor_analysis(self, agent_results: Dict[str, pd.DataFrame], 
                                weighted_results: pd.DataFrame, 
                                insights: Dict[str, Any]) -> str:
        """Track supervisor analysis and cross-agent communication."""
        try:
            if not self.current_run_tree:
                self.start_project_run()
            
            # Prepare supervisor inputs
            supervisor_inputs = {
                "agent_results_summary": {
                    agent: {
                        "findings_count": len(results_df),
                        "columns": list(results_df.columns) if not results_df.empty else [],
                        "sample_data": results_df.head(3).to_dict() if not results_df.empty else {}
                    }
                    for agent, results_df in agent_results.items()
                },
                "total_pharmacies": len(weighted_results),
                "weighted_results_summary": {
                    "high_risk_count": len(weighted_results[weighted_results['weighted_score'] >= 0.8]),
                    "medium_risk_count": len(weighted_results[
                        (weighted_results['weighted_score'] >= 0.6) & 
                        (weighted_results['weighted_score'] < 0.8)
                    ]),
                    "avg_score": weighted_results['weighted_score'].mean(),
                    "score_std": weighted_results['weighted_score'].std()
                }
            }
            
            # Create supervisor run
            supervisor_run = self.current_run_tree.create_child(
                name="supervisor-analysis",
                inputs=supervisor_inputs,
                outputs={
                    "insights": insights,
                    "recommendations": insights.get('recommendations', []),
                    "agent_performance": insights.get('agent_performance', {}),
                    "cross_agent_patterns": insights.get('cross_agent_patterns', {})
                },
                tags=["supervisor", "cross-agent-analysis", "consistency-checking"]
            )
            
            self.logger.info(f"👨‍💼 Tracked supervisor analysis: {supervisor_run.id}")
            return supervisor_run.id
            
        except Exception as e:
            self.logger.error(f"❌ Error tracking supervisor analysis: {e}")
            return None
    
    def track_weighted_scoring(self, agent_results: Dict[str, pd.DataFrame], 
                             weighted_results: pd.DataFrame, 
                             weights: Dict[str, float]) -> str:
        """Track weighted scoring process."""
        try:
            if not self.current_run_tree:
                self.start_project_run()
            
            # Calculate scoring metrics
            scoring_metrics = {
                "weights_used": weights,
                "total_pharmacies": len(weighted_results),
                "score_distribution": {
                    "high_risk": len(weighted_results[weighted_results['weighted_score'] >= 0.8]),
                    "medium_risk": len(weighted_results[
                        (weighted_results['weighted_score'] >= 0.6) & 
                        (weighted_results['weighted_score'] < 0.8)
                    ]),
                    "low_risk": len(weighted_results[
                        (weighted_results['weighted_score'] >= 0.4) & 
                        (weighted_results['weighted_score'] < 0.6)
                    ]),
                    "very_low_risk": len(weighted_results[weighted_results['weighted_score'] < 0.4])
                },
                "agent_contributions": {
                    agent: {
                        "findings_count": len(results_df),
                        "avg_score": results_df['fraud_score'].mean() if not results_df.empty else 0
                    }
                    for agent, results_df in agent_results.items()
                }
            }
            
            # Create weighted scoring run
            scoring_run = self.current_run_tree.create_child(
                name="weighted-scoring",
                inputs={
                    "agent_results_count": {agent: len(results_df) for agent, results_df in agent_results.items()},
                    "weights": weights
                },
                outputs={
                    "weighted_results_summary": {
                        "total_pharmacies": len(weighted_results),
                        "score_range": [weighted_results['weighted_score'].min(), weighted_results['weighted_score'].max()],
                        "avg_score": weighted_results['weighted_score'].mean()
                    },
                    "scoring_metrics": scoring_metrics
                },
                tags=["weighted-scoring", "score-aggregation", "multi-agent"]
            )
            
            self.logger.info(f"⚖️ Tracked weighted scoring: {scoring_run.id}")
            return scoring_run.id
            
        except Exception as e:
            self.logger.error(f"❌ Error tracking weighted scoring: {e}")
            return None
    
    def track_cross_agent_communication(self, pharmacy_number: str, 
                                      agent_scores: Dict[str, float],
                                      consistency_score: float,
                                      outlier_score: float) -> str:
        """Track cross-agent communication for a specific pharmacy."""
        try:
            if not self.current_run_tree:
                self.start_project_run()
            
            # Analyze cross-agent patterns
            high_risk_agents = [agent for agent, score in agent_scores.items() if score >= 0.8]
            low_risk_agents = [agent for agent, score in agent_scores.items() if score < 0.4]
            conflicting_signals = len(high_risk_agents) > 0 and len(low_risk_agents) > 0
            
            communication_analysis = {
                "pharmacy_number": pharmacy_number,
                "agent_scores": agent_scores,
                "consistency_score": consistency_score,
                "outlier_score": outlier_score,
                "cross_agent_patterns": {
                    "high_risk_agents": high_risk_agents,
                    "low_risk_agents": low_risk_agents,
                    "conflicting_signals": conflicting_signals,
                    "agent_agreement": "high" if consistency_score >= 0.8 else "medium" if consistency_score >= 0.6 else "low"
                }
            }
            
            # Create cross-agent communication run
            communication_run = self.current_run_tree.create_child(
                name="cross-agent-communication",
                inputs={
                    "pharmacy_number": pharmacy_number,
                    "agent_scores": agent_scores
                },
                outputs=communication_analysis,
                tags=["cross-agent", "consistency-checking", "pharmacy-analysis"]
            )
            
            self.logger.info(f"🔗 Tracked cross-agent communication for {pharmacy_number}: {communication_run.id}")
            return communication_run.id
            
        except Exception as e:
            self.logger.error(f"❌ Error tracking cross-agent communication: {e}")
            return None
    
    def end_project_run(self, final_results: Dict[str, Any] = None):
        """End the project run and finalize tracking."""
        try:
            if self.current_run_tree:
                if final_results:
                    self.current_run_tree.end(
                        outputs=final_results
                    )
                else:
                    self.current_run_tree.end()
                
                self.logger.info(f"✅ Completed LangSmith project run: {self.current_run_tree.id}")
                self.logger.info(f"📊 View run at: https://smith.langchain.com/runs/{self.current_run_tree.id}")
                
        except Exception as e:
            self.logger.error(f"❌ Error ending LangSmith run: {e}")
    
    def get_run_url(self) -> str:
        """Get the URL for the current run."""
        if self.current_run_tree:
            return f"https://smith.langchain.com/runs/{self.current_run_tree.id}"
        return "No active run"


# Global tracker instance
langsmith_tracker = LangSmithTracker() 
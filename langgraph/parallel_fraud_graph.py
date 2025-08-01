import pandas as pd
from typing import TypedDict, Dict, Any
from langgraph.graph import StateGraph, END
from utils.db_loader import AzureSynapseLoader
from utils.weighted_scoring import SupervisorAgent


class ParallelFraudDetectionState(TypedDict):
    df: pd.DataFrame
    agent_results: Dict[str, pd.DataFrame]
    weighted_results: pd.DataFrame
    supervisor_insights: Dict[str, Any]
    final_results: pd.DataFrame


def load_data_node(state: ParallelFraudDetectionState) -> ParallelFraudDetectionState:
    """Load data from Azure Synapse."""
    print("🔄 Loading data from Azure Synapse...")
    try:
        loader = AzureSynapseLoader()
        df = loader.load_copay_detail_data(limit=10000)
        print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        state["df"] = df
        return state
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        state["df"] = pd.DataFrame()
        return state


def parallel_analysis_node(state: ParallelFraudDetectionState) -> ParallelFraudDetectionState:
    """Run parallel analysis with supervisor."""
    print("🚀 Starting parallel fraud detection with supervisor...")
    try:
        df = state.get("df", pd.DataFrame())
        if df.empty:
            print("⚠️ No data to process")
            state["agent_results"] = {}
            state["weighted_results"] = pd.DataFrame()
            state["supervisor_insights"] = {}
            return state
        
        # Initialize supervisor
        supervisor = SupervisorAgent()
        
        # Run supervised analysis
        results = supervisor.supervise_analysis(df)
        
        state["agent_results"] = results["agent_results"]
        state["weighted_results"] = results["weighted_results"]
        state["supervisor_insights"] = results["supervisor_insights"]
        
        print(f"✅ Parallel analysis completed:")
        print(f"   • Total pharmacies analyzed: {len(results['weighted_results'])}")
        print(f"   • High risk pharmacies: {results['supervisor_insights']['high_risk_pharmacies']}")
        print(f"   • Medium risk pharmacies: {results['supervisor_insights']['medium_risk_pharmacies']}")
        
        return state
    except Exception as e:
        print(f"❌ Error in parallel analysis: {e}")
        state["agent_results"] = {}
        state["weighted_results"] = pd.DataFrame()
        state["supervisor_insights"] = {}
        return state


def final_results_node(state: ParallelFraudDetectionState) -> ParallelFraudDetectionState:
    """Prepare final results with detailed pharmacy information."""
    print("📊 Preparing final results...")
    try:
        weighted_results = state.get("weighted_results", pd.DataFrame())
        agent_results = state.get("agent_results", {})
        df = state.get("df", pd.DataFrame())
        
        if weighted_results.empty:
            print("⚠️ No weighted results to process")
            state["final_results"] = pd.DataFrame()
            return state
        
        # Sort by weighted score (highest risk first)
        final_results = weighted_results.sort_values('weighted_score', ascending=False).copy()
        
        # Add additional details
        final_results['rank'] = range(1, len(final_results) + 1)
        
        # Also update weighted_results with rank for Streamlit compatibility
        weighted_results_with_rank = weighted_results.sort_values('weighted_score', ascending=False).copy()
        weighted_results_with_rank['rank'] = range(1, len(weighted_results_with_rank) + 1)
        state["weighted_results"] = weighted_results_with_rank
        
        print(f"✅ Final results prepared: {len(final_results)} pharmacies ranked by risk")
        state["final_results"] = final_results
        return state
    except Exception as e:
        print(f"❌ Error preparing final results: {e}")
        state["final_results"] = pd.DataFrame()
        return state


def build_parallel_graph() -> StateGraph:
    """Build the parallel fraud detection graph."""
    workflow = StateGraph(ParallelFraudDetectionState)
    
    # Add nodes
    workflow.add_node("load_data", load_data_node)
    workflow.add_node("parallel_analysis", parallel_analysis_node)
    workflow.add_node("final_results", final_results_node)
    
    # Set entry point
    workflow.set_entry_point("load_data")
    
    # Add edges
    workflow.add_edge("load_data", "parallel_analysis")
    workflow.add_edge("parallel_analysis", "final_results")
    workflow.add_edge("final_results", END)
    
    # Compile graph
    graph = workflow.compile()
    return graph


def run_parallel_fraud_detection_pipeline() -> Dict[str, Any]:
    """Run the complete parallel fraud detection pipeline."""
    print("🚀 Starting Parallel Fraud Detection Pipeline")
    print("=" * 50)
    
    try:
        # Build and run graph
        graph = build_parallel_graph()
        result = graph.invoke({})
        
        print("=" * 50)
        print("✅ Parallel Pipeline completed successfully!")
        
        return {
            'agent_results': result.get('agent_results', {}),
            'weighted_results': result.get('weighted_results', pd.DataFrame()),
            'supervisor_insights': result.get('supervisor_insights', {}),
            'final_results': result.get('final_results', pd.DataFrame()),
            'raw_data': result.get('df', pd.DataFrame())
        }
    except Exception as e:
        print(f"❌ Error in parallel pipeline: {e}")
        return {
            'agent_results': {},
            'weighted_results': pd.DataFrame(),
            'supervisor_insights': {},
            'final_results': pd.DataFrame(),
            'raw_data': pd.DataFrame()
        } 
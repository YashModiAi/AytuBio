from typing import Dict, Any, TypedDict
import pandas as pd
from langgraph.graph import StateGraph, END
from utils.db_loader import AzureSynapseLoader
from agents.coverage_agent import CoverageTypeAgent
from agents.patient_flip_agent_enhanced import PatientFlipAgentEnhanced
from agents.high_dollar_agent import HighDollarClaimAgent
from agents.rejected_claim_agent import RejectedClaimDensityAgent
from agents.network_anomaly_agent import PharmacyNetworkAnomalyAgent

# Define the state structure for our graph
class FraudDetectionState(TypedDict):
    """State structure for the fraud detection pipeline."""
    df: pd.DataFrame
    coverage_flags: pd.DataFrame
    flip_flags: pd.DataFrame
    high_dollar_flags: pd.DataFrame
    rejection_flags: pd.DataFrame
    network_flags: pd.DataFrame
    results: pd.DataFrame

def load_data_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 1: Load claim data from Azure Synapse SQL.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with loaded data
    """
    print("🔄 Loading data from Azure Synapse...")
    
    try:
        # Initialize the loader
        loader = AzureSynapseLoader()
        
        # Load data (default 10,000 rows)
        df = loader.load_copay_detail_data(limit=10000)
        
        print(f"✅ Loaded {len(df)} rows with {len(df.columns)} columns")
        
        # Update state
        state["df"] = df
        
        return state
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        # Return empty DataFrame on error
        state["df"] = pd.DataFrame()
        return state

def coverage_agent_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 2: Process data through the coverage type agent.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with coverage flags
    """
    print("🤖 Processing data through CoverageTypeAgent...")
    
    try:
        df = state.get("df", pd.DataFrame())
        
        if df.empty:
            print("⚠️ No data to process")
            state["coverage_flags"] = pd.DataFrame()
            return state
        
        # Initialize and run the coverage agent
        agent = CoverageTypeAgent()
        coverage_flags = agent.run(df)
        
        print(f"✅ Coverage agent processed {len(coverage_flags)} rows")
        
        # Update state
        state["coverage_flags"] = coverage_flags
        
        return state
        
    except Exception as e:
        print(f"❌ Error in coverage agent: {e}")
        state["coverage_flags"] = pd.DataFrame()
        return state

def patient_flip_agent_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 3: Process data through the patient flip agent.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with flip flags
    """
    print("🔄 Processing data through PatientFlipAgent...")
    
    try:
        df = state.get("df", pd.DataFrame())
        
        if df.empty:
            print("⚠️ No data to process")
            state["flip_flags"] = pd.DataFrame()
            return state
        
        # Initialize and run the enhanced patient flip agent
        agent = PatientFlipAgentEnhanced()
        flip_flags = agent.run(df)
        
        print(f"✅ Patient flip agent processed {len(flip_flags)} patterns")
        
        # Update state
        state["flip_flags"] = flip_flags
        
        return state
        
    except Exception as e:
        print(f"❌ Error in patient flip agent: {e}")
        state["flip_flags"] = pd.DataFrame()
        return state

def high_dollar_agent_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 4: Process data through the high dollar claim agent.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with high dollar flags
    """
    print("💰 Processing data through HighDollarClaimAgent...")
    
    try:
        df = state.get("df", pd.DataFrame())
        
        if df.empty:
            print("⚠️ No data to process")
            state["high_dollar_flags"] = pd.DataFrame()
            return state
        
        # Initialize and run the high dollar agent
        agent = HighDollarClaimAgent()
        high_dollar_flags = agent.run(df)
        
        print(f"✅ High dollar agent processed {len(high_dollar_flags)} rows")
        
        # Update state
        state["high_dollar_flags"] = high_dollar_flags
        
        return state
        
    except Exception as e:
        print(f"❌ Error in high dollar agent: {e}")
        state["high_dollar_flags"] = pd.DataFrame()
        return state

def rejection_agent_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 5: Process data through the rejected claim density agent.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with rejection flags
    """
    print("🚫 Processing data through RejectedClaimDensityAgent...")
    
    try:
        df = state.get("df", pd.DataFrame())
        
        if df.empty:
            print("⚠️ No data to process")
            state["rejection_flags"] = pd.DataFrame()
            return state
        
        # Initialize and run the rejection agent
        agent = RejectedClaimDensityAgent()
        rejection_flags = agent.run(df)
        
        print(f"✅ Rejection agent processed {len(rejection_flags)} rows")
        
        # Update state
        state["rejection_flags"] = rejection_flags
        
        return state
        
    except Exception as e:
        print(f"❌ Error in rejection agent: {e}")
        state["rejection_flags"] = pd.DataFrame()
        return state

def network_agent_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 6: Process data through the pharmacy network anomaly agent.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with network flags
    """
    print("🏥 Processing data through PharmacyNetworkAnomalyAgent...")
    
    try:
        df = state.get("df", pd.DataFrame())
        
        if df.empty:
            print("⚠️ No data to process")
            state["network_flags"] = pd.DataFrame()
            return state
        
        # Get combined results from other agents for enhancement
        coverage_flags = state.get("coverage_flags", pd.DataFrame())
        flip_flags = state.get("flip_flags", pd.DataFrame())
        high_dollar_flags = state.get("high_dollar_flags", pd.DataFrame())
        rejection_flags = state.get("rejection_flags", pd.DataFrame())
        
        # Combine all agent results for enhancement
        combined_agent_results = []
        if not coverage_flags.empty:
            combined_agent_results.append(coverage_flags)
        if not flip_flags.empty:
            combined_agent_results.append(flip_flags)
        if not high_dollar_flags.empty:
            combined_agent_results.append(high_dollar_flags)
        if not rejection_flags.empty:
            combined_agent_results.append(rejection_flags)
        
        combined_results = pd.concat(combined_agent_results, ignore_index=True) if combined_agent_results else pd.DataFrame()
        
        # Initialize and run the network agent
        agent = PharmacyNetworkAnomalyAgent()
        network_flags = agent.run(df, combined_results)
        
        print(f"✅ Network agent processed {len(network_flags)} rows")
        
        # Update state
        state["network_flags"] = network_flags
        
        return state
        
    except Exception as e:
        print(f"❌ Error in network agent: {e}")
        state["network_flags"] = pd.DataFrame()
        return state

def combine_results_node(state: FraudDetectionState) -> FraudDetectionState:
    """
    Node 7: Combine results from all agents.
    
    Args:
        state (FraudDetectionState): Current graph state
        
    Returns:
        FraudDetectionState: Updated state with final results
    """
    print("🔗 Combining results from all agents...")
    
    try:
        coverage_flags = state.get("coverage_flags", pd.DataFrame())
        flip_flags = state.get("flip_flags", pd.DataFrame())
        high_dollar_flags = state.get("high_dollar_flags", pd.DataFrame())
        rejection_flags = state.get("rejection_flags", pd.DataFrame())
        network_flags = state.get("network_flags", pd.DataFrame())
        
        if coverage_flags.empty and flip_flags.empty and high_dollar_flags.empty and rejection_flags.empty and network_flags.empty:
            print("⚠️ No results to combine")
            state["results"] = pd.DataFrame()
            return state
        
        # Combine results from all agents
        combined_results = []
        
        # Add coverage agent results
        if not coverage_flags.empty:
            for _, row in coverage_flags.iterrows():
                combined_results.append({
                    'pharmacy_number': row['pharmacy_number'],
                    'pharmacy_name': row['pharmacy_name'],
                    'pharmacy_city': row['pharmacy_city'],
                    'pharmacy_state': row['pharmacy_state'],
                    'fraud_score': row['fraud_score'],
                    'reason': row['reason'],
                    'analysis_type': row['analysis_type'],
                    'agent_source': 'coverage_agent',
                    'total_claims': row['total_claims'],
                    'flagged_claims': row['flagged_claims'],
                    'flagged_percent': row['flagged_percent']
                })
        
        # Add flip agent results
        if not flip_flags.empty:
            for _, row in flip_flags.iterrows():
                combined_results.append({
                    'pharmacy_number': row['pharmacy_number'],
                    'pharmacy_name': row['pharmacy_name'],
                    'pharmacy_city': row['pharmacy_city'],
                    'pharmacy_state': row['pharmacy_state'],
                    'fraud_score': row['fraud_score'],
                    'reason': row['reason'],
                    'analysis_type': row['analysis_type'],
                    'agent_source': 'patient_flip_agent',
                    'patient_id': row['patient_id'],
                    'product_ndc': row['product_ndc'],
                    'product_name': row['product_name'],
                    'number_of_flips': row['number_of_flips'],
                    'total_claims': row['total_claims']
                })
        
        # Add high dollar agent results
        if not high_dollar_flags.empty:
            for _, row in high_dollar_flags.iterrows():
                combined_results.append({
                    'pharmacy_number': row['pharmacy_number'],
                    'pharmacy_name': row['pharmacy_name'],
                    'pharmacy_city': row['pharmacy_city'],
                    'pharmacy_state': row['pharmacy_state'],
                    'fraud_score': row['fraud_score'],
                    'reason': row['reason'],
                    'analysis_type': row['analysis_type'],
                    'agent_source': 'high_dollar_agent',
                    'total_high_dollar_claims': row['total_high_dollar_claims'],
                    'total_cost': row['total_cost'],
                    'avg_claim_cost': row['avg_claim_cost'],
                    'cash_not_covered_count': row['cash_not_covered_count'],
                    'cash_percentage': row['cash_percentage']
                })
        
        # Add rejection agent results
        if not rejection_flags.empty:
            for _, row in rejection_flags.iterrows():
                combined_results.append({
                    'pharmacy_number': row['pharmacy_number'],
                    'pharmacy_name': row['pharmacy_name'],
                    'pharmacy_city': row['pharmacy_city'],
                    'pharmacy_state': row['pharmacy_state'],
                    'fraud_score': row['fraud_score'],
                    'reason': row['reason'],
                    'analysis_type': row['analysis_type'],
                    'agent_source': 'rejection_agent',
                    'total_claims': row['total_claims'],
                    'rejected_claims': row['rejected_claims'],
                    'rejection_percentage': row['rejection_percentage'],
                    'primary_rejections': row['primary_rejections'],
                    'pa_rejections': row['pa_rejections'],
                    'status_rejections': row['status_rejections'],
                    'total_rejection_types': row['total_rejection_types']
                })
        
        # Add network agent results
        if not network_flags.empty:
            for _, row in network_flags.iterrows():
                combined_results.append({
                    'pharmacy_number': row['pharmacy_number'],
                    'pharmacy_name': row['pharmacy_name'],
                    'pharmacy_city': row['pharmacy_city'],
                    'pharmacy_state': row['pharmacy_state'],
                    'fraud_score': row['fraud_score'],
                    'reason': row['reason'],
                    'analysis_type': row['analysis_type'],
                    'agent_source': 'network_agent',
                    'total_claims': row['total_claims'],
                    'network_claims': row['network_claims'],
                    'non_network_claims': row['non_network_claims'],
                    'network_percentage': row['network_percentage'],
                    'is_primarily_network': row['is_primarily_network'],
                    'primary_network_type': row['primary_network_type'],
                    'network_fraud_score': row.get('network_fraud_score', 0.0),
                    'agent_fraud_score': row.get('agent_fraud_score', 0.0),
                    'agent_count': row.get('agent_count', 0),
                    'high_risk_agents': row.get('high_risk_agents', 0)
                })
        
        # Create combined DataFrame
        results_df = pd.DataFrame(combined_results)
        
        # Sort by fraud score (highest first)
        if not results_df.empty:
            results_df = results_df.sort_values('fraud_score', ascending=False)
        
        print(f"✅ Combined results: {len(results_df)} total findings")
        print(f"   • Coverage agent findings: {len(coverage_flags)}")
        print(f"   • Flip agent findings: {len(flip_flags)}")
        print(f"   • High dollar agent findings: {len(high_dollar_flags)}")
        print(f"   • Rejection agent findings: {len(rejection_flags)}")
        print(f"   • Network agent findings: {len(network_flags)}")
        
        # Update state
        state["results"] = results_df
        
        return state
        
    except Exception as e:
        print(f"❌ Error combining results: {e}")
        state["results"] = pd.DataFrame()
        return state

def build_graph() -> StateGraph:
    """
    Build the LangGraph pipeline for fraud detection.
    
    Returns:
        StateGraph: Configured graph with nodes and edges
    """
    # Create the state graph
    workflow = StateGraph(FraudDetectionState)
    
    # Add nodes
    workflow.add_node("load_data", load_data_node)
    workflow.add_node("coverage_agent", coverage_agent_node)
    workflow.add_node("patient_flip_agent", patient_flip_agent_node)
    workflow.add_node("high_dollar_agent", high_dollar_agent_node)
    workflow.add_node("rejection_agent", rejection_agent_node)
    workflow.add_node("network_agent", network_agent_node)
    workflow.add_node("combine_results", combine_results_node)
    
    # Define the flow: load_data → coverage_agent → patient_flip_agent → high_dollar_agent → rejection_agent → network_agent → combine_results → END
    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "coverage_agent")
    workflow.add_edge("coverage_agent", "patient_flip_agent")
    workflow.add_edge("patient_flip_agent", "high_dollar_agent")
    workflow.add_edge("high_dollar_agent", "rejection_agent")
    workflow.add_edge("rejection_agent", "network_agent")
    workflow.add_edge("network_agent", "combine_results")
    workflow.add_edge("combine_results", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    return graph

def run_fraud_detection_pipeline() -> Dict[str, Any]:
    """
    Run the complete fraud detection pipeline.
    
    Returns:
        Dict[str, Any]: Pipeline results
    """
    print("🚀 Starting Fraud Detection Pipeline")
    print("=" * 50)
    
    # Build and run the graph
    graph = build_graph()
    result = graph.invoke({})
    
    print("=" * 50)
    print("✅ Pipeline completed successfully!")
    
    return result 
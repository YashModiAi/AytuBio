import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
import json
from langgraph.parallel_fraud_graph import run_parallel_fraud_detection_pipeline
from utils.weighted_scoring import WeightedScoringSystem


# Page configuration
st.set_page_config(
    page_title="Enhanced Fraud Detection Dashboard",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .risk-high { color: #d62728; font-weight: bold; }
    .risk-medium { color: #ff7f0e; font-weight: bold; }
    .risk-low { color: #2ca02c; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


def render_weight_controls():
    """Render agent weight controls in sidebar."""
    st.sidebar.subheader("⚖️ Agent Weight Controls")
    st.sidebar.markdown("Adjust the importance of each agent in the final score calculation.")
    
    weights = {}
    weights['coverage_agent'] = st.sidebar.slider(
        "Coverage Agent Weight", 0.0, 1.0, 0.25, 0.05,
        help="Weight for coverage pattern analysis (Cash, Not Covered, OCC codes)"
    )
    
    weights['patient_flip_agent'] = st.sidebar.slider(
        "Patient Flip Agent Weight", 0.0, 1.0, 0.20, 0.05,
        help="Weight for insurance-to-cash flip detection"
    )
    
    weights['high_dollar_agent'] = st.sidebar.slider(
        "High Dollar Agent Weight", 0.0, 1.0, 0.20, 0.05,
        help="Weight for high-dollar claim analysis (copay > $200, OOP > $500)"
    )
    
    weights['rejection_agent'] = st.sidebar.slider(
        "Rejection Agent Weight", 0.0, 1.0, 0.20, 0.05,
        help="Weight for rejection pattern analysis"
    )
    
    weights['network_agent'] = st.sidebar.slider(
        "Network Agent Weight", 0.0, 1.0, 0.15, 0.05,
        help="Weight for network anomaly analysis"
    )
    
    # Show current weight distribution
    total_weight = sum(weights.values())
    if total_weight > 0:
        normalized_weights = {k: v/total_weight for k, v in weights.items()}
        st.sidebar.markdown("**Current Weight Distribution:**")
        for agent, weight in normalized_weights.items():
            st.sidebar.text(f"{agent.replace('_', ' ').title()}: {weight:.1%}")
    
    return normalized_weights if total_weight > 0 else weights


def render_threshold_controls():
    """Render threshold controls in sidebar."""
    st.sidebar.subheader("🎯 Threshold Controls")
    
    fraud_threshold = st.sidebar.slider(
        "Fraud Score Threshold", 0.0, 1.0, 0.6, 0.1,
        help="Minimum fraud score to flag pharmacy"
    )
    
    consistency_threshold = st.sidebar.slider(
        "Consistency Threshold", 0.0, 1.0, 0.7, 0.1,
        help="Minimum consistency score for high confidence"
    )
    
    outlier_threshold = st.sidebar.slider(
        "Outlier Threshold", 0.0, 1.0, 0.8, 0.1,
        help="Threshold for outlier detection"
    )
    
    return {
        'fraud_threshold': fraud_threshold,
        'consistency_threshold': consistency_threshold,
        'outlier_threshold': outlier_threshold
    }


def display_supervisor_insights(insights: Dict[str, Any]):
    """Display supervisor insights and recommendations."""
    st.subheader("👨‍💼 Supervisor Insights")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pharmacies", insights.get('total_pharmacies_analyzed', 0))
    
    with col2:
        st.metric("High Risk", insights.get('high_risk_pharmacies', 0), 
                 delta=f"{insights.get('high_risk_pharmacies', 0)} flagged")
    
    with col3:
        st.metric("Medium Risk", insights.get('medium_risk_pharmacies', 0))
    
    with col4:
        total_risk = insights.get('high_risk_pharmacies', 0) + insights.get('medium_risk_pharmacies', 0)
        st.metric("Total Risk", total_risk)
    
    # Agent performance
    if 'agent_performance' in insights:
        st.subheader("🤖 Agent Performance")
        agent_perf = insights['agent_performance']
        
        perf_data = []
        for agent_name, perf in agent_perf.items():
            perf_data.append({
                'Agent': agent_name.replace('_', ' ').title(),
                'Avg Score': perf['avg_score'],
                'High Risk Findings': perf['high_risk_findings'],
                'Total Findings': perf['total_findings']
            })
        
        perf_df = pd.DataFrame(perf_data)
        st.dataframe(perf_df, use_container_width=True)
    
    # Recommendations
    if 'recommendations' in insights and insights['recommendations']:
        st.subheader("💡 Recommendations")
        for rec in insights['recommendations']:
            st.info(rec)


def display_weighted_results(weighted_results: pd.DataFrame, raw_data: pd.DataFrame):
    """Display weighted results with detailed pharmacy information."""
    st.subheader("📊 Weighted Fraud Analysis Results")
    
    if weighted_results.empty:
        st.warning("No weighted results available.")
        return
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        risk_filter = st.selectbox(
            "Filter by Risk Level",
            ['All', 'HIGH RISK', 'MEDIUM RISK', 'LOW RISK', 'VERY LOW RISK']
        )
    
    with col2:
        min_score = st.slider("Minimum Score", 0.0, 1.0, 0.0, 0.1)
    
    with col3:
        search_pharmacy = st.text_input("Search Pharmacy Number", "")
    
    # Apply filters
    filtered_results = weighted_results.copy()
    
    if risk_filter != 'All':
        filtered_results = filtered_results[filtered_results['risk_level'] == risk_filter]
    
    filtered_results = filtered_results[filtered_results['weighted_score'] >= min_score]
    
    if search_pharmacy:
        filtered_results = filtered_results[
            filtered_results['pharmacy_number'].astype(str).str.contains(search_pharmacy, case=False)
        ]
    
    # Display results
    display_columns = ['pharmacy_number', 'pharmacy_name', 'pharmacy_city', 'pharmacy_state',
                      'weighted_score', 'risk_level', 'transaction_count', 'contributing_agents']
    
    # Add rank column if it exists
    if 'rank' in filtered_results.columns:
        display_columns.insert(0, 'rank')
    
    st.dataframe(
        filtered_results[display_columns].head(20),
        use_container_width=True
    )
    
    # Detailed pharmacy view
    if not filtered_results.empty:
        st.subheader("🔍 Detailed Pharmacy Analysis")
        
        selected_pharmacy = st.selectbox(
            "Select Pharmacy for Detailed Analysis",
            filtered_results['pharmacy_number'].tolist()
        )
        
        if selected_pharmacy:
            pharmacy_data = filtered_results[filtered_results['pharmacy_number'] == selected_pharmacy].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Pharmacy:** {pharmacy_data['pharmacy_name']}")
                st.markdown(f"**Location:** {pharmacy_data['pharmacy_city']}, {pharmacy_data['pharmacy_state']}")
                st.markdown(f"**Risk Level:** {pharmacy_data['risk_level']}")
                st.markdown(f"**Weighted Score:** {pharmacy_data['weighted_score']:.3f}")
                st.markdown(f"**Transaction Count:** {pharmacy_data['transaction_count']}")
            
            with col2:
                st.markdown("**Agent Contributions:**")
                agent_scores = pharmacy_data['agent_scores']
                for agent, score in agent_scores.items():
                    st.markdown(f"- {agent.replace('_', ' ').title()}: {score:.3f}")
            
            # Fraud explanation
            st.markdown("**Fraud Explanation:**")
            st.info(pharmacy_data['fraud_explanation'])
            
            # Show pharmacy transactions
            if not raw_data.empty:
                pharmacy_transactions = raw_data[raw_data['pharmacy_number'] == selected_pharmacy]
                
                if not pharmacy_transactions.empty:
                    st.subheader("📋 Pharmacy Transactions")
                    
                    # Transaction summary
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Claims", len(pharmacy_transactions))
                    
                    with col2:
                        cash_claims = len(pharmacy_transactions[
                            pharmacy_transactions['coverage_type'].isin(['Cash', 'Not Covered'])
                        ])
                        st.metric("Cash/Not Covered", cash_claims)
                    
                    with col3:
                        high_dollar = len(pharmacy_transactions[
                            (pharmacy_transactions['copay_cost'] > 200) | 
                            (pharmacy_transactions['oop_cost'] > 500)
                        ])
                        st.metric("High Dollar Claims", high_dollar)
                    
                    with col4:
                        rejected = len(pharmacy_transactions[
                            pharmacy_transactions['claim_cob_primary_reject_code1'].notna() |
                            pharmacy_transactions['pa_rejection_code_1'].notna()
                        ])
                        st.metric("Rejected Claims", rejected)
                    
                    # Show transaction details
                    st.dataframe(
                        pharmacy_transactions[[
                            'date_submitted', 'patient_id', 'product_ndc', 'coverage_type',
                            'copay_cost', 'oop_cost', 'claim_cob_primary_reject_code1',
                            'pa_rejection_code_1'
                        ]].head(10),
                        use_container_width=True
                    )


def create_visualizations(weighted_results: pd.DataFrame, insights: Dict[str, Any]):
    """Create visualizations for the weighted results."""
    st.subheader("📈 Visualizations")
    
    if weighted_results.empty:
        st.warning("No data available for visualizations.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Risk level distribution
        risk_counts = weighted_results['risk_level'].value_counts()
        fig_risk = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            title="Risk Level Distribution"
        )
        st.plotly_chart(fig_risk, use_container_width=True)
    
    with col2:
        # Weighted score distribution
        fig_score = px.histogram(
            weighted_results,
            x='weighted_score',
            nbins=20,
            title="Weighted Score Distribution"
        )
        st.plotly_chart(fig_score, use_container_width=True)
    
    # Top risk pharmacies
    st.subheader("🏆 Top 10 Highest Risk Pharmacies")
    top_pharmacies = weighted_results.head(10)
    
    fig_top = px.bar(
        top_pharmacies,
        x='pharmacy_number',
        y='weighted_score',
        color='weighted_score',
        title="Top 10 Highest Risk Pharmacies",
        labels={'weighted_score': 'Weighted Score', 'pharmacy_number': 'Pharmacy Number'}
    )
    st.plotly_chart(fig_top, use_container_width=True)


def export_data(weighted_results: pd.DataFrame, agent_results: Dict[str, pd.DataFrame]):
    """Export functionality."""
    st.subheader("📤 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export weighted results
        csv_weighted = weighted_results.to_csv(index=False)
        st.download_button(
            label="Download Weighted Results (CSV)",
            data=csv_weighted,
            file_name="weighted_fraud_results.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export all agent results
        all_agent_data = []
        for agent_name, results_df in agent_results.items():
            if not results_df.empty:
                results_df['agent_name'] = agent_name
                all_agent_data.append(results_df)
        
        if all_agent_data:
            combined_agent_data = pd.concat(all_agent_data, ignore_index=True)
            csv_agents = combined_agent_data.to_csv(index=False)
            st.download_button(
                label="Download All Agent Results (CSV)",
                data=csv_agents,
                file_name="all_agent_results.csv",
                mime="text/csv"
            )


def main():
    """Main application."""
    st.markdown('<h1 class="main-header">🚨 Enhanced Fraud Detection Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar controls
    weights = render_weight_controls()
    thresholds = render_threshold_controls()
    
    # Run analysis button
    if st.sidebar.button("🚀 Run Parallel Analysis", type="primary"):
        with st.spinner("Running parallel fraud detection analysis..."):
            # Run the parallel pipeline
            results = run_parallel_fraud_detection_pipeline()
            
            # Store results in session state
            st.session_state['results'] = results
            st.session_state['weights'] = weights
            st.session_state['thresholds'] = thresholds
    
    # Display results if available
    if 'results' in st.session_state:
        results = st.session_state['results']
        weights = st.session_state['weights']
        thresholds = st.session_state['thresholds']
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", "🎯 Weighted Results", "👨‍💼 Supervisor", "📈 Visualizations", "📤 Export"
        ])
        
        with tab1:
            st.subheader("📊 Analysis Overview")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Pharmacies", len(results['weighted_results']))
            
            with col2:
                high_risk = len(results['weighted_results'][results['weighted_results']['weighted_score'] >= 0.8])
                st.metric("High Risk", high_risk)
            
            with col3:
                medium_risk = len(results['weighted_results'][
                    (results['weighted_results']['weighted_score'] >= 0.6) & 
                    (results['weighted_results']['weighted_score'] < 0.8)
                ])
                st.metric("Medium Risk", medium_risk)
            
            with col4:
                avg_score = results['weighted_results']['weighted_score'].mean()
                st.metric("Average Score", f"{avg_score:.3f}")
            
            # Current weights
            st.subheader("⚖️ Current Agent Weights")
            weight_df = pd.DataFrame([
                {'Agent': agent.replace('_', ' ').title(), 'Weight': f"{weight:.1%}"}
                for agent, weight in weights.items()
            ])
            st.dataframe(weight_df, use_container_width=True)
        
        with tab2:
            display_weighted_results(results['weighted_results'], results['raw_data'])
        
        with tab3:
            display_supervisor_insights(results['supervisor_insights'])
        
        with tab4:
            create_visualizations(results['weighted_results'], results['supervisor_insights'])
        
        with tab5:
            export_data(results['weighted_results'], results['agent_results'])
    
    else:
        st.info("👆 Click 'Run Parallel Analysis' to start the fraud detection process.")


if __name__ == "__main__":
    main() 
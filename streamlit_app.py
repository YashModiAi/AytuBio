#!/usr/bin/env python3
"""
Enhanced Streamlit App for Azure Synapse Fraud Detection Pipeline
Visualizes fraud detection results from both CoverageTypeAgent and PatientFlipAgent
with interactive features, filters, and export capabilities.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_fraud_detection_results():
    """
    Load fraud detection results using the LangGraph pipeline.
    
    Returns:
        Dict[str, Any]: Pipeline results
    """
    try:
        from langgraph.fraud_graph import run_fraud_detection_pipeline
        return run_fraud_detection_pipeline()
    except Exception as e:
        st.error(f"Error loading fraud detection results: {e}")
        return None

def load_raw_claim_data(pharmacy_number: str):
    """
    Load raw claim data for a specific pharmacy.
    
    Args:
        pharmacy_number (str): Pharmacy number to filter by
        
    Returns:
        pd.DataFrame: Raw claim data for the pharmacy
    """
    try:
        from utils.db_loader import AzureSynapseLoader
        
        loader = AzureSynapseLoader()
        df = loader.load_copay_detail_data(limit=10000)
        
        # Filter by pharmacy number
        pharmacy_data = df[df['pharmacy_number'] == pharmacy_number]
        return pharmacy_data
    except Exception as e:
        st.error(f"Error loading raw claim data: {e}")
        return pd.DataFrame()

def calculate_summary_metrics(results_df: pd.DataFrame, agent_type: str = "all") -> Dict[str, Any]:
    """
    Calculate summary metrics from fraud detection results.
    
    Args:
        results_df (pd.DataFrame): Fraud detection results
        agent_type (str): Filter by agent type ("coverage_agent", "patient_flip_agent", or "all")
        
    Returns:
        Dict[str, Any]: Summary metrics
    """
    if results_df.empty:
        return {
            'total_findings': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'avg_fraud_score': 0.0,
            'total_pharmacies': 0,
            'total_patients': 0
        }
    
    # Filter by agent type if specified
    if agent_type != "all":
        filtered_df = results_df[results_df['agent_source'] == agent_type]
    else:
        filtered_df = results_df
    
    if filtered_df.empty:
        return {
            'total_findings': 0,
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'avg_fraud_score': 0.0,
            'total_pharmacies': 0,
            'total_patients': 0
        }
    
    total_findings = len(filtered_df)
    high_risk_count = len(filtered_df[filtered_df['fraud_score'] >= 0.8])
    medium_risk_count = len(filtered_df[(filtered_df['fraud_score'] >= 0.6) & (filtered_df['fraud_score'] < 0.8)])
    low_risk_count = len(filtered_df[filtered_df['fraud_score'] < 0.6])
    avg_fraud_score = filtered_df['fraud_score'].mean()
    
    # Count unique pharmacies and patients
    total_pharmacies = filtered_df['pharmacy_number'].nunique()
    total_patients = filtered_df['patient_id'].nunique() if 'patient_id' in filtered_df.columns else 0
    
    return {
        'total_findings': total_findings,
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
        'avg_fraud_score': round(avg_fraud_score, 3),
        'total_pharmacies': total_pharmacies,
        'total_patients': total_patients
    }

def create_fraud_score_chart(results_df: pd.DataFrame, agent_type: str = "all"):
    """
    Create a bar chart of fraud scores by pharmacy.
    
    Args:
        results_df (pd.DataFrame): Fraud detection results
        agent_type (str): Filter by agent type
        
    Returns:
        plotly.graph_objects.Figure: Bar chart
    """
    if results_df.empty:
        return go.Figure()
    
    # Filter by agent type if specified
    if agent_type != "all":
        filtered_df = results_df[results_df['agent_source'] == agent_type]
    else:
        filtered_df = results_df
    
    if filtered_df.empty:
        return go.Figure()
    
    # Sort by fraud score for better visualization
    sorted_df = filtered_df.sort_values('fraud_score', ascending=True).tail(20)
    
    # Create hover text based on agent type
    if agent_type == "coverage_agent":
        hover_template = '<b>%{y}</b><br>' + \
                       'Fraud Score: %{x:.3f}<br>' + \
                       'Location: %{customdata[0]}, %{customdata[1]}<br>' + \
                       'Total Claims: %{customdata[2]}<br>' + \
                       'Flagged Claims: %{customdata[3]}<br>' + \
                       'Flagged %: %{customdata[4]}%<br>' + \
                       'Reason: %{customdata[5]}<extra></extra>'
        customdata = list(zip(
            sorted_df['pharmacy_city'],
            sorted_df['pharmacy_state'],
            sorted_df['total_claims'],
            sorted_df['flagged_claims'],
            sorted_df['flagged_percent'],
            sorted_df['reason']
        ))
    else:
        hover_template = '<b>%{y}</b><br>' + \
                       'Fraud Score: %{x:.3f}<br>' + \
                       'Location: %{customdata[0]}, %{customdata[1]}<br>' + \
                       'Patient ID: %{customdata[2]}<br>' + \
                       'Product: %{customdata[3]}<br>' + \
                       'Number of Flips: %{customdata[4]}<br>' + \
                       'Total Claims: %{customdata[5]}<br>' + \
                       'Reason: %{customdata[6]}<extra></extra>'
        customdata = list(zip(
            sorted_df['pharmacy_city'],
            sorted_df['pharmacy_state'],
            sorted_df['patient_id'],
            sorted_df['product_name'],
            sorted_df['number_of_flips'],
            sorted_df['total_claims'],
            sorted_df['reason']
        ))
    
    fig = go.Figure(data=[
        go.Bar(
            x=sorted_df['fraud_score'],
            y=sorted_df['pharmacy_name'],
            orientation='h',
            marker=dict(
                color=sorted_df['fraud_score'],
                colorscale='RdYlGn_r'
            ),
            text=sorted_df['fraud_score'].round(3),
            textposition='auto',
            hovertemplate=hover_template,
            customdata=customdata
        )
    ])
    
    agent_title = "Coverage Type" if agent_type == "coverage_agent" else "Patient Flip" if agent_type == "patient_flip_agent" else "All Agents"
    fig.update_layout(
        title=f"Top 20 Pharmacies by Fraud Score - {agent_title}",
        xaxis_title="Fraud Score",
        yaxis_title="Pharmacy Name",
        height=600,
        showlegend=False,
        xaxis=dict(range=[0, 1])
    )
    
    return fig

def create_risk_distribution_chart(results_df: pd.DataFrame, agent_type: str = "all"):
    """
    Create a pie chart showing risk distribution.
    
    Args:
        results_df (pd.DataFrame): Fraud detection results
        agent_type (str): Filter by agent type
        
    Returns:
        plotly.graph_objects.Figure: Pie chart
    """
    if results_df.empty:
        return go.Figure()
    
    # Filter by agent type if specified
    if agent_type != "all":
        filtered_df = results_df[results_df['agent_source'] == agent_type]
    else:
        filtered_df = results_df
    
    if filtered_df.empty:
        return go.Figure()
    
    # Categorize by risk level
    high_risk = len(filtered_df[filtered_df['fraud_score'] >= 0.8])
    medium_risk = len(filtered_df[(filtered_df['fraud_score'] >= 0.6) & (filtered_df['fraud_score'] < 0.8)])
    low_risk = len(filtered_df[filtered_df['fraud_score'] < 0.6])
    
    fig = go.Figure(data=[go.Pie(
        labels=['High Risk (≥80%)', 'Medium Risk (60-79%)', 'Low Risk (<60%)'],
        values=[high_risk, medium_risk, low_risk],
        hole=0.3,
        marker_colors=['#d62728', '#ff7f0e', '#2ca02c']
    )])
    
    agent_title = "Coverage Type" if agent_type == "coverage_agent" else "Patient Flip" if agent_type == "patient_flip_agent" else "All Agents"
    fig.update_layout(
        title=f"Risk Distribution - {agent_title}",
        height=400
    )
    
    return fig

def create_state_map_chart(results_df: pd.DataFrame, agent_type: str = "all"):
    """
    Create a choropleth map showing fraud by state.
    
    Args:
        results_df (pd.DataFrame): Fraud detection results
        agent_type (str): Filter by agent type
        
    Returns:
        plotly.graph_objects.Figure: Map chart
    """
    if results_df.empty:
        return go.Figure()
    
    # Filter by agent type if specified
    if agent_type != "all":
        filtered_df = results_df[results_df['agent_source'] == agent_type]
    else:
        filtered_df = results_df
    
    if filtered_df.empty:
        return go.Figure()
    
    # Aggregate by state
    state_agg = filtered_df.groupby('pharmacy_state').agg({
        'fraud_score': ['mean', 'count'],
        'pharmacy_number': 'nunique'
    }).round(3)
    
    state_agg.columns = ['avg_fraud_score', 'total_findings', 'unique_pharmacies']
    state_agg = state_agg.reset_index()
    
    fig = px.choropleth(
        state_agg,
        locations='pharmacy_state',
        locationmode='USA-states',
        color='avg_fraud_score',
        hover_name='pharmacy_state',
        hover_data=['total_findings', 'unique_pharmacies'],
        color_continuous_scale='RdYlGn_r',
        range_color=[0, 1],
        title=f"Average Fraud Score by State - {agent_type.replace('_', ' ').title() if agent_type != 'all' else 'All Agents'}"
    )
    
    fig.update_layout(
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)'
        ),
        height=500
    )
    
    return fig

def export_data(data: pd.DataFrame, format: str, filename: str):
    """
    Export data in specified format.
    
    Args:
        data (pd.DataFrame): Data to export
        format (str): Export format ('csv' or 'json')
        filename (str): Base filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'csv':
        csv = data.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {filename} (CSV)",
            data=csv,
            file_name=f"{filename}_{timestamp}.csv",
            mime="text/csv"
        )
    elif format == 'json':
        json_str = data.to_json(orient='records', indent=2)
        st.download_button(
            label=f"📥 Download {filename} (JSON)",
            data=json_str,
            file_name=f"{filename}_{timestamp}.json",
            mime="application/json"
        )

def main():
    """Main Streamlit app function."""
    st.set_page_config(
        page_title="Azure Synapse Fraud Detection Dashboard",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 Azure Synapse Fraud Detection Dashboard")
    st.markdown("---")
    
    # Sidebar for filters
    st.sidebar.header("📊 Filters & Controls")
    
    # Load data
    with st.spinner("Loading fraud detection results..."):
        results = load_fraud_detection_results()
    
    if results is None or "results" not in results or results["results"].empty:
        st.error("❌ Failed to load fraud detection results")
        return
    
    results_df = results["results"]
    
    # Sidebar filters
    st.sidebar.subheader("🔍 Data Filters")
    
    # Agent type filter
    agent_types = ['All Agents', 'Coverage Type Agent', 'Patient Flip Agent', 'High Dollar Agent', 'Rejection Agent', 'Network Agent']
    selected_agent = st.sidebar.selectbox("Filter by Agent", agent_types)
    
    # Map agent display names to internal names
    agent_mapping = {
        'All Agents': 'all',
        'Coverage Type Agent': 'coverage_agent',
        'Patient Flip Agent': 'patient_flip_agent',
        'High Dollar Agent': 'high_dollar_agent',
        'Rejection Agent': 'rejection_agent',
        'Network Agent': 'network_agent'
    }
    selected_agent_internal = agent_mapping[selected_agent]
    
    # State filter
    states = ['All'] + sorted(results_df['pharmacy_state'].unique().tolist())
    selected_state = st.sidebar.selectbox("Filter by State", states)
    
    # Fraud score threshold filter
    min_fraud_score = st.sidebar.slider(
        "Minimum Fraud Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="Show only findings with fraud score >= this value"
    )
    
    # Apply filters
    filtered_df = results_df.copy()
    
    if selected_agent_internal != 'all':
        filtered_df = filtered_df[filtered_df['agent_source'] == selected_agent_internal]
    
    if selected_state != 'All':
        filtered_df = filtered_df[filtered_df['pharmacy_state'] == selected_state]
    
    filtered_df = filtered_df[filtered_df['fraud_score'] >= min_fraud_score]
    
    # Calculate summary metrics
    metrics = calculate_summary_metrics(filtered_df, selected_agent_internal)
    
    # Display summary metrics
    st.header("📈 Summary Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("Total Findings", metrics['total_findings'])
    
    with col2:
        st.metric("High Risk", metrics['high_risk_count'], 
                 delta=f"{metrics['high_risk_count']/metrics['total_findings']*100:.1f}%" if metrics['total_findings'] > 0 else 0)
    
    with col3:
        st.metric("Medium Risk", metrics['medium_risk_count'],
                 delta=f"{metrics['medium_risk_count']/metrics['total_findings']*100:.1f}%" if metrics['total_findings'] > 0 else 0)
    
    with col4:
        st.metric("Low Risk", metrics['low_risk_count'])
    
    with col5:
        st.metric("Avg Fraud Score", f"{metrics['avg_fraud_score']:.3f}")
    
    with col6:
        if selected_agent_internal == "patient_flip_agent":
            st.metric("Unique Patients", metrics['total_patients'])
        else:
            st.metric("Unique Pharmacies", metrics['total_pharmacies'])
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📋 Data Tables", "🗺️ Geographic View", "🔬 Raw Data Analysis"])
    
    with tab1:
        st.header("📊 Interactive Dashboard")
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Risk Distribution")
            risk_chart = create_risk_distribution_chart(filtered_df, selected_agent_internal)
            st.plotly_chart(risk_chart, use_container_width=True)
        
        with col2:
            st.subheader("Top Findings by Fraud Score")
            fraud_chart = create_fraud_score_chart(filtered_df, selected_agent_internal)
            st.plotly_chart(fraud_chart, use_container_width=True)
        
        # State map
        st.subheader("Geographic Distribution")
        map_chart = create_state_map_chart(filtered_df, selected_agent_internal)
        st.plotly_chart(map_chart, use_container_width=True)
    
    with tab2:
        st.header("📋 Data Tables & Export")
        
        # Search functionality
        search_term = st.text_input("🔍 Search by Pharmacy Name, Patient ID, or Product Name", "")
        
        # Apply search filter
        search_filtered_df = filtered_df.copy()
        if search_term:
            mask = (
                search_filtered_df['pharmacy_name'].str.contains(search_term, case=False, na=False) |
                search_filtered_df['patient_id'].astype(str).str.contains(search_term, case=False, na=False) |
                search_filtered_df['product_name'].str.contains(search_term, case=False, na=False)
            )
            search_filtered_df = search_filtered_df[mask]
        
        st.write(f"Showing {len(search_filtered_df)} findings (filtered from {len(filtered_df)} total)")
        
        # Export buttons
        col1, col2 = st.columns(2)
        with col1:
            export_data(search_filtered_df, 'csv', f"fraud_detection_{selected_agent_internal}")
        with col2:
            export_data(search_filtered_df, 'json', f"fraud_detection_{selected_agent_internal}")
        
        # Interactive table with sorting
        st.dataframe(
            search_filtered_df,
            use_container_width=True,
            column_config={
                "fraud_score": st.column_config.NumberColumn(
                    "Fraud Score",
                    help="Risk score from 0 (low) to 1 (high)",
                    format="%.3f"
                ),
                "flagged_percent": st.column_config.NumberColumn(
                    "Flagged %",
                    help="Percentage of claims flagged as suspicious",
                    format="%.1f%%"
                ),
                "number_of_flips": st.column_config.NumberColumn(
                    "Number of Flips",
                    help="Number of insurance-to-cash flips detected",
                    format="%d"
                )
            }
        )
    
    with tab3:
        st.header("🗺️ Geographic Analysis")
        
        # State-level analysis
        if not filtered_df.empty:
            state_analysis = filtered_df.groupby('pharmacy_state').agg({
                'fraud_score': ['mean', 'count', 'max'],
                'pharmacy_number': 'nunique'
            }).round(3)
            
            state_analysis.columns = ['avg_fraud_score', 'total_findings', 'max_fraud_score', 'unique_pharmacies']
            state_analysis = state_analysis.reset_index()
            state_analysis = state_analysis.sort_values('avg_fraud_score', ascending=False)
            
            st.subheader("State-Level Risk Analysis")
            st.dataframe(state_analysis, use_container_width=True)
            
            # Export state analysis
            col1, col2 = st.columns(2)
            with col1:
                export_data(state_analysis, 'csv', f"state_analysis_{selected_agent_internal}")
            with col2:
                export_data(state_analysis, 'json', f"state_analysis_{selected_agent_internal}")
    
    with tab4:
        st.header("🔬 Raw Data Analysis")
        
        # Pharmacy selector for raw data
        if not filtered_df.empty:
            pharmacy_options = filtered_df['pharmacy_name'].unique().tolist()
            selected_pharmacy_name = st.selectbox(
                "Select Pharmacy for Raw Data Analysis",
                pharmacy_options,
                help="Choose a pharmacy to view its raw claim data"
            )
            
            if selected_pharmacy_name:
                selected_pharmacy_data = filtered_df[filtered_df['pharmacy_name'] == selected_pharmacy_name]
                pharmacy_number = selected_pharmacy_data['pharmacy_number'].iloc[0]
                
                st.subheader(f"Raw Claim Data for: {selected_pharmacy_name}")
                st.write(f"**Pharmacy Number:** {pharmacy_number}")
                st.write(f"**Location:** {selected_pharmacy_data['pharmacy_city'].iloc[0]}, {selected_pharmacy_data['pharmacy_state'].iloc[0]}")
                st.write(f"**Fraud Score:** {selected_pharmacy_data['fraud_score'].iloc[0]:.3f}")
                st.write(f"**Reason:** {selected_pharmacy_data['reason'].iloc[0]}")
                
                # Show agent-specific details
                if selected_agent_internal == "coverage_agent":
                    st.write(f"**Total Claims:** {selected_pharmacy_data['total_claims'].iloc[0]}")
                    st.write(f"**Flagged Claims:** {selected_pharmacy_data['flagged_claims'].iloc[0]}")
                    st.write(f"**Flagged Percentage:** {selected_pharmacy_data['flagged_percent'].iloc[0]:.1f}%")
                elif selected_agent_internal == "patient_flip_agent":
                    st.write(f"**Patient ID:** {selected_pharmacy_data['patient_id'].iloc[0]}")
                    st.write(f"**Product:** {selected_pharmacy_data['product_name'].iloc[0]}")
                    st.write(f"**Number of Flips:** {selected_pharmacy_data['number_of_flips'].iloc[0]}")
                    st.write(f"**Total Claims:** {selected_pharmacy_data['total_claims'].iloc[0]}")
                
                # Load and display raw claim data
                show_raw_data = st.checkbox("Show Raw Claim Data", value=False)
                
                if show_raw_data:
                    with st.spinner("Loading raw claim data..."):
                        raw_data = load_raw_claim_data(pharmacy_number)
                    
                    if not raw_data.empty:
                        st.write(f"**Total Raw Claims:** {len(raw_data)}")
                        
                        # Show key columns for analysis
                        key_columns = [
                            'transaction_id', 'rx_id', 'coverage_type', 'occ',
                            'original_cost', 'copay_cost', 'date_filled',
                            'prescriber_npi', 'patient_id'
                        ]
                        
                        display_columns = [col for col in key_columns if col in raw_data.columns]
                        st.dataframe(raw_data[display_columns], use_container_width=True)
                        
                        # Coverage type breakdown
                        if 'coverage_type' in raw_data.columns:
                            st.subheader("Coverage Type Breakdown")
                            coverage_counts = raw_data['coverage_type'].value_counts()
                            st.bar_chart(coverage_counts)
                            
                    else:
                        st.warning("No raw claim data found for this pharmacy.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>🔍 Azure Synapse Fraud Detection Pipeline | Powered by LangGraph & Streamlit</p>
        <p>CoverageTypeAgent + PatientFlipAgent | Multi-Agent Fraud Detection System</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main() 
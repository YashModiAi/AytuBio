# 🚨 AytuBio Fraud Detection System

A comprehensive multi-agent fraud detection system for Azure Synapse SQL data with parallel processing, weighted scoring, and real-time visualization.

## 📁 Project Structure

```
AytuBio/
├── 📁 agents/                    # Fraud Detection Agents
├── 📁 data/                      # Data Storage & Exports  
├── 📁 docs/                      # Documentation
├── 📁 langgraph/                 # Pipeline Orchestration
├── 📁 tests/                     # Testing & Analysis
├── 📁 utils/                     # Utility Modules
└── 🚀 Main Applications
```

**📋 [Complete Project Structure](PROJECT_STRUCTURE.md)**

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Database
Create `.env` file in project root:
```env
DB_USER=your_azure_username
DB_PASSWORD=your_azure_password
```

### 3. Run the System
```bash
# Run parallel fraud detection
python main.py

# Launch enhanced dashboard
streamlit run streamlit_enhanced_app.py --server.port 8505
```

## 🎯 Key Features

### **🤖 Multi-Agent System**
- **Coverage Agent**: Detects Cash/Not Covered patterns
- **Patient Flip Agent**: Identifies insurance-to-cash flips  
- **High Dollar Agent**: Flags expensive claims
- **Rejection Agent**: Tracks claim rejections
- **Network Agent**: Analyzes network pharmacy anomalies

### **⚖️ Parallel Processing**
- **5 Agents** running simultaneously
- **Weighted Scoring** with UI controls
- **Cross-Agent Communication** tracking
- **Supervisor Pattern** for consistency

### **📊 Interactive Dashboard**
- **Real-time Analysis** with custom weights
- **Risk Level Filtering** (HIGH/MEDIUM/LOW)
- **Detailed Pharmacy Drill-down**
- **Export Capabilities** (CSV/JSON)

### **🔍 Observability**
- **LangSmith Integration** for tracking
- **Cross-Agent Communication** visualization
- **Supervisor Insights** and recommendations
- **Local Data Access** as backup

## 📈 System Architecture

```
Azure Synapse SQL → db_loader.py → Parallel Agents → Weighted Scoring → Supervisor → Streamlit Dashboard
```

## 📚 Documentation

### **📖 System Overview**
- **[FINAL_SYSTEM_OVERVIEW.md](FINAL_SYSTEM_OVERVIEW.md)**: Complete system architecture
- **[README_PARALLEL_SYSTEM.md](README_PARALLEL_SYSTEM.md)**: Parallel processing details
- **[SUPERVISOR_BENEFITS.md](SUPERVISOR_BENEFITS.md)**: Multi-agent coordination

### **🔧 LangSmith Integration**
- **[LANGSMITH_FULL_ACCESS.md](LANGSMITH_FULL_ACCESS.md)**: Complete access guide
- **[LANGSMITH_LOGIN_GUIDE.md](LANGSMITH_LOGIN_GUIDE.md)**: Login and setup
- **[LANGSMITH_SUPERVISOR_INTEGRATION.md](LANGSMITH_SUPERVISOR_INTEGRATION.md)**: Integration details

## 🧪 Testing

### **Run All Tests**
```bash
python tests/test_parallel_system.py
```

### **Individual Agent Tests**
```bash
python tests/test_coverage_agent.py
python tests/test_high_dollar_agent.py
python tests/test_network_agent.py
python tests/test_rejection_agent.py
```

### **System Tests**
```bash
python tests/test_connection.py
python tests/test_streamlit_features.py
```

## 📊 Data Access

### **Agent Results**
- `data/agent_results/coverage_agent_results.csv`
- `data/agent_results/high_dollar_agent_results.csv`
- `data/agent_results/network_agent_results.csv`
- `data/agent_results/patient_flip_agent_results.csv`
- `data/agent_results/rejection_agent_results.csv`

### **System Exports**
- `data/exports/fraud_detection_results.csv`
- `data/exports/langsmith_export.json`

## 🛠️ Development

### **Adding New Agents**
1. Create agent in `agents/` folder
2. Add to `utils/weighted_scoring.py`
3. Update weights in dashboard
4. Test with `tests/test_new_agent.py`

### **Modifying Pipeline**
1. Edit `langgraph/parallel_fraud_graph.py`
2. Update supervisor in `utils/weighted_scoring.py`
3. Test with `tests/test_parallel_system.py`

### **Dashboard Customization**
1. Modify `streamlit_enhanced_app.py`
2. Add new visualizations
3. Test with `tests/test_streamlit_features.py`

## 🔧 Configuration

### **Agent Weights**
Adjust in Streamlit dashboard:
- Coverage Agent: 0-100%
- Patient Flip Agent: 0-100%
- High Dollar Agent: 0-100%
- Rejection Agent: 0-100%
- Network Agent: 0-100%

### **Thresholds**
- Fraud Score Threshold: 0.0-1.0
- Consistency Threshold: 0.0-1.0
- Outlier Threshold: 0.0-1.0

## 📈 Performance

### **Current Results**
- **108 Pharmacies** analyzed
- **25 Medium Risk** pharmacies detected
- **5 Specialized Agents** working in parallel
- **Cross-agent communication** tracked for all pharmacies

### **Top Risk Pharmacies**
1. **BETTER CARE PHARMACY** (MD) - Score: 0.77
2. **WEGMANS FOOD MARKETS** (MD) - Score: 0.762
3. **DILLON PHARMACY** (KS) - Score: 0.747
4. **CVS PHARMACY #05744** (MS) - Score: 0.742

## 🚨 Troubleshooting

### **Database Connection**
```bash
python tests/test_connection.py
```

### **LangSmith Access**
- Check API key in environment
- Verify project creation
- Use local data viewer as backup

### **Agent Issues**
```bash
python tests/test_parallel_system.py
```

## 📞 Support

For issues or questions:
1. Check documentation in `docs/`
2. Run relevant tests in `tests/`
3. Review agent outputs in `data/agent_results/`
4. Use local dashboard for data exploration

---

**🎉 Your fraud detection system is now fully organized and ready for production use!** 
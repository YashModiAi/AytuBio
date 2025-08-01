# 📁 AytuBio Fraud Detection System - Project Structure

## 🏗️ Organized Folder Structure

```
AytuBio/
├── 📁 agents/                    # Fraud Detection Agents
│   ├── coverage_agent.py         # Coverage pattern detection
│   ├── high_dollar_agent.py      # High-dollar claim detection
│   ├── network_anomaly_agent.py  # Network pharmacy analysis
│   ├── patient_flip_agent.py     # Insurance-to-cash flip detection
│   └── rejected_claim_agent.py   # Rejection pattern analysis
│
├── 📁 data/                      # Data Storage
│   ├── 📁 agent_results/         # Individual agent outputs
│   │   ├── coverage_agent_results.csv
│   │   ├── high_dollar_agent_results.csv
│   │   ├── network_agent_results.csv
│   │   ├── patient_flip_agent_results.csv
│   │   └── rejection_agent_results.csv
│   └── 📁 exports/              # System exports and summaries
│       ├── fraud_detection_results.csv
│       └── langsmith_export.json
│
├── 📁 docs/                      # Documentation
│   ├── FINAL_SYSTEM_OVERVIEW.md
│   ├── LANGSMITH_FULL_ACCESS.md
│   ├── LANGSMITH_LOGIN_GUIDE.md
│   ├── LANGSMITH_SUPERVISOR_INTEGRATION.md
│   ├── README.md
│   ├── README_PARALLEL_SYSTEM.md
│   └── SUPERVISOR_BENEFITS.md
│
├── 📁 langgraph/                 # Pipeline Orchestration
│   ├── fraud_graph.py           # Basic fraud detection pipeline
│   └── parallel_fraud_graph.py  # Parallel processing pipeline
│
├── 📁 tests/                     # Testing and Analysis Scripts
│   ├── analyze_flip_data.py     # Data analysis utilities
│   ├── run_patient_flip_agent.py
│   ├── test_connection.py       # Database connection tests
│   ├── test_enhanced_flip_agent.py
│   ├── test_flip_agent.py
│   ├── test_high_dollar_agent.py
│   ├── test_network_agent.py
│   ├── test_parallel_system.py
│   ├── test_rejection_agent.py
│   └── test_streamlit_features.py
│
├── 📁 utils/                     # Utility Modules
│   ├── db_loader.py             # Azure Synapse SQL connector
│   ├── export_langsmith_data.py # Data export utilities
│   ├── langsmith_integration.py # LangSmith tracking
│   ├── local_data_viewer.py     # Local data visualization
│   └── weighted_scoring.py      # Parallel scoring system
│
├── 📁 venv/                     # Python virtual environment
├── main.py                      # Main execution script
├── requirements.txt              # Python dependencies
├── streamlit_app.py             # Basic Streamlit dashboard
├── streamlit_enhanced_app.py    # Enhanced dashboard with supervisor
└── .gitignore                   # Git ignore rules
```

## 🎯 Key Components

### **🤖 Agents (`agents/`)**
Specialized fraud detection modules:
- **Coverage Agent**: Detects Cash/Not Covered patterns
- **Patient Flip Agent**: Identifies insurance-to-cash flips
- **High Dollar Agent**: Flags expensive claims
- **Rejection Agent**: Tracks claim rejections
- **Network Agent**: Analyzes network pharmacy anomalies

### **📊 Data (`data/`)**
- **Agent Results**: Individual agent outputs as CSV files
- **Exports**: System-wide results and LangSmith exports

### **📚 Documentation (`docs/`)**
- **System Overview**: Complete system architecture
- **LangSmith Guides**: Integration and access instructions
- **Supervisor Benefits**: Multi-agent coordination details
- **README Files**: Setup and usage instructions

### **🔄 Pipeline (`langgraph/`)**
- **Basic Pipeline**: Sequential fraud detection
- **Parallel Pipeline**: Multi-agent parallel processing

### **🧪 Testing (`tests/`)**
- **Agent Tests**: Individual agent validation
- **System Tests**: End-to-end testing
- **Analysis Scripts**: Data exploration utilities

### **🛠️ Utilities (`utils/`)**
- **Database**: Azure Synapse SQL connector
- **LangSmith**: Observability and tracking
- **Scoring**: Weighted multi-agent scoring
- **Visualization**: Local data viewing tools

## 🚀 Quick Start

1. **Setup**: `pip install -r requirements.txt`
2. **Database**: Configure `.env` with Azure credentials
3. **Run Pipeline**: `python main.py`
4. **Dashboard**: `streamlit run streamlit_enhanced_app.py`

## 📈 Data Flow

```
Azure Synapse SQL → db_loader.py → Agents → Weighted Scoring → Supervisor → Streamlit Dashboard
```

## 🔍 Key Features

- **Parallel Processing**: 5 agents running simultaneously
- **Weighted Scoring**: Configurable agent importance
- **Cross-Agent Communication**: Consistency and outlier detection
- **LangSmith Integration**: Full observability and tracking
- **Interactive Dashboard**: Real-time analysis and visualization

## 📋 File Types

- **`.py`**: Python source code
- **`.csv`**: Agent results and exports
- **`.json`**: LangSmith exports and configurations
- **`.md`**: Documentation and guides
- **`.txt`**: Configuration and requirements 
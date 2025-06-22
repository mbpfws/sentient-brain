# 🧠 Sentient Brain - Multi-Agent AI Code Developer with SurrealDB

A sophisticated multi-agent AI system designed for intelligent code development, featuring a 4-layered memory architecture, real-time monitoring, and advanced workflow orchestration.

## 🎯 **Project Vision**

**Goal:** Develop an advanced AI Code Developer system leveraging a multi-agent architecture and a unified, persistent data layer provided by SurrealDB. This system intelligently guides users through software development, from initial concept to ongoing maintenance, promoting efficiency and best practices.

**Strategic Architecture:** Unified SurrealDB as the sole persistent data layer, providing multi-model capabilities (document, graph, key-value, table) with local Docker deployment for maximum flexibility and control.

## 🏗️ **Core Architecture**

### **Multi-Agent System with Layered Memory**

Our AI Code Developer operates as a sophisticated multi-agent system designed for profound agentic workflow compliance. Each agent possesses specialized roles and interacts seamlessly through dedicated memory layers.

#### **🎯 Primary Agents**

1. **🧭 Ultra Orchestrator Agent (Central Intelligence)**
   - **Role:** Paramount director interfacing with user prompts
   - **Core Functions:**
     - User Intent Disambiguation (new vs existing project)
     - Dynamic Agent Instantiation
     - Workflow Regulation
     - Client-Side Integration

2. **🏛️ Architect Agent (Design & Planning Specialist)**
   - **Role:** Conceptualizes, designs, and details project architecture
   - **Modes:**
     - **Guided Enhancement** (novice/intermediate users)
     - **Standardized Optimization** (experienced users)
   - **Output:** High-Level Plan, PRD, Tech Stack Specification

3. **💾 Codebase Knowledge Memory Layer Agent**
   - **Role:** Manages ingestion, indexing, and persistent storage
   - **Process:**
     - Parse and index entire codebase structure
     - Chunk and vectorize code segments
     - Establish relational metadata
     - Real-time monitoring with file watchers

4. **🔧 Debug and Refactor Agent**
   - **Role:** Identifies inefficiencies, bugs, and improvement areas
   - **Process:**
     - Static and dynamic code analysis
     - Pattern-based issue detection
     - LLM-powered deep analysis
     - Comprehensive refactoring plans

5. **📋 Plan and Tasks Memory Layer Agent**
   - **Role:** Custodian of project plans, tasks, and sub-tasks
   - **Process:**
     - Breaks down high-level plans into granular tasks
     - Manages dependencies and priorities
     - Progress tracking with SurrealDB

6. **📚 Documents Memory Layer Agent**
   - **Role:** Gathers and processes external technical documentation
   - **Process:**
     - Web scraping for latest technical docs
     - Chunking, vectorizing, categorizing
     - Metadata enrichment and relationship linking

## 🧠 **4-Layered Memory System**

### **Layer 1: Plans and Task-Breakdown Memory**
- **Entities:** GrandPlan, Task, Milestone, CompletionCriteria
- **Relationships:** HAS_SUBTASK, DEPENDS_ON, ASSOCIATED_WITH, GOVERNED_BY
- **Features:** Hierarchical task management, dependency tracking, progress monitoring

### **Layer 2: Message Session Memory**
- **Entities:** MessageSession, MessageTurn, SessionContext
- **Relationships:** HAS_TURN, REFERS_TO, RESULTS_IN, INFLUENCES
- **Features:** Conversation tracking, intent extraction, context reconstruction

### **Layer 3: Documents Memory**
- **Entities:** DocumentSource, Document, DocChunk
- **Relationships:** HAS_CHUNK, REFERS_TO, ABOUT, SIMILAR_TO
- **Features:** Multi-granularity chunking, source tracking, quality scoring

### **Layer 4: Open-Source Git Memory**
- **Entities:** GitRepo, RepoFile, RepoChunk, Feature
- **Relationships:** HAS_FILE, HAS_CHUNK, SIMILAR_TO, IMPROVES, INSPIRES
- **Features:** OSS code analysis, feature extraction, local improvement suggestions

## 🔄 **LangGraph Workflow Engine**

### **Workflow Steps**
1. **Intent Analysis** - Understand user goals
2. **Agent Routing** - Direct to appropriate specialist
3. **Architect Planning** - Design and architecture
4. **Codebase Analysis** - Code indexing and analysis
5. **Debug Analysis** - Issue identification and fixes
6. **Task Breakdown** - Project decomposition
7. **Document Research** - Knowledge gathering
8. **Execution Monitoring** - Progress tracking
9. **Result Synthesis** - Final response compilation

### **Advanced Features**
- **State Persistence** with SQLite checkpointing
- **Conditional Routing** based on intent and context
- **Error Recovery** with retry mechanisms
- **Real-time Monitoring** with comprehensive metrics
- **Cross-layer Integration** with automatic relationship creation

## 🛠️ **Technology Stack**

### **Core Technologies**
- **SurrealDB** - Unified multi-model database
- **Groq API** - High-performance LLM inference
- **LangGraph** - Workflow orchestration
- **FastAPI** - REST API framework
- **Pydantic** - Data validation and modeling

### **AI and ML**
- **Sentence Transformers** - Vector embeddings
- **Tree-sitter** - Code parsing and AST analysis
- **Watchdog** - Real-time file monitoring

### **Additional Integrations**
- **Docker** - Containerized deployment
- **Prometheus/Grafana** - Monitoring and observability
- **Redis** - Caching (optional)

## 🚀 **Getting Started**

### **Prerequisites**
- Docker and Docker Compose
- Python 3.11+
- SurrealDB (via Docker)

### **Quick Start**

1. **Clone and Setup**
```bash
git clone <repository>
cd sentient-brain-surreal
cp .env.example .env
# Edit .env with your configuration
```

2. **Start with Docker Compose**
```bash
docker-compose up -d
```

3. **Initialize the System**
```bash
curl -X POST http://localhost:8000/initialize
```

4. **Start Coding with AI**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Build a REST API with authentication", "session_id": "user_123"}'
```

## 📡 **API Endpoints**

### **Core Workflow**
- `POST /query` - Main query processing through orchestrator
- `GET /workflow/{workflow_id}/status` - Workflow status
- `POST /workflow/{workflow_id}/cancel` - Cancel workflow

### **Project Management**
- `POST /projects` - Create new project
- `GET /projects/{project_id}` - Get project details
- `PUT /projects/{project_id}/context` - Update project context

### **Memory Management**
- `POST /knowledge/nodes` - Create knowledge nodes
- `GET /knowledge/search` - Hybrid semantic search
- `GET /knowledge/relationships/{entity_id}` - Get relationships

### **Agent Management**
- `GET /agents/status` - Agent health and status
- `POST /agents/{agent_id}/task` - Direct agent task
- `GET /metrics/workflow` - Workflow execution metrics

## 🎛️ **Configuration**

### **Environment Variables**

```env
# Database Configuration
SURREALDB_URL=ws://surrealdb:8000/rpc
SURREALDB_USERNAME=root
SURREALDB_PASSWORD=sentient_brain_secure_2024
SURREALDB_NAMESPACE=sentient_brain
SURREALDB_DATABASE=production

# LLM Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=mixtral-8x7b-32768

# Application Configuration
ENVIRONMENT=production
DEBUG=false
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
API_RATE_LIMIT=100

# Codebase Monitoring
CODEBASE_PATH=/app/codebase
ENABLE_FILE_MONITORING=true

# Vector Search Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384
SIMILARITY_THRESHOLD=0.7
```

## 🧪 **Advanced Features**

### **Real-time Code Monitoring**
- Automatic file change detection
- Incremental codebase indexing
- Live relationship updates
- Performance optimization

### **Hybrid Semantic Search**
- Vector similarity search
- Graph relationship traversal
- Multi-layer result fusion
- Contextual ranking

### **Workflow Orchestration**
- State-based execution
- Dynamic agent routing
- Error recovery patterns
- Performance monitoring

### **Memory Integration**
- Cross-layer relationships
- Automatic linking
- Semantic enrichment
- Quality scoring

## 📊 **Monitoring and Observability**

### **Built-in Metrics**
- Workflow execution times
- Agent performance stats
- Memory usage analytics
- Error rate monitoring

### **Health Checks**
- Database connectivity
- Agent availability
- Memory system status
- External service health

### **Logging**
- Structured JSON logging
- Request/response tracing
- Agent interaction logs
- Performance profiling

## 🔧 **Development**

### **Running Tests**
```bash
pytest tests/ -v --asyncio-mode=auto
```

### **Code Quality**
```bash
# Linting
flake8 src/
mypy src/

# Formatting
black src/
isort src/
```

### **Development Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 **Use Cases**

### **1. New Project Initialization**
```json
{
  "query": "I want to build a social media app with React and Node.js",
  "session_id": "user_123",
  "project_type": "new"
}
```

### **2. Existing Codebase Analysis**
```json
{
  "query": "Analyze my codebase for performance issues and security vulnerabilities",
  "session_id": "user_123",
  "codebase_path": "/path/to/project"
}
```

### **3. Feature Planning**
```json
{
  "query": "Add real-time chat functionality to my existing app",
  "session_id": "user_123",
  "context": {"existing_tech_stack": ["react", "express", "mongodb"]}
}
```

## 🛡️ **Security**

### **Built-in Security Features**
- Non-root container execution
- Environment-based secrets
- CORS protection
- Rate limiting
- Input validation

### **Best Practices**
- Regular dependency updates
- Secure API key management
- Database access controls
- Network security configurations

## 📈 **Performance**

### **Optimization Features**
- Vector search acceleration
- Caching strategies
- Batch processing
- Background task queues

### **Scalability**
- Horizontal agent scaling
- Database partitioning
- Load balancing ready
- Monitoring integration

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **Development Workflow**
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **SurrealDB** for the unified database platform
- **Groq** for high-performance LLM inference
- **LangGraph** for workflow orchestration
- **Archon** for multi-agent inspiration
- **Fetch.ai** for decentralized AI concepts

---

## 🔬 **Research and Advanced Features**

### **Bonus Integrations (Future)**
- **Coral Protocol** - Decentralized machine intelligence
- **Fetch.ai** - Autonomous Economic Agents (AEAs)
- **Advanced Autonomy** - Independent decision making

### **Innovation Areas**
- Cross-project knowledge transfer
- Adaptive learning from user feedback
- Predictive code evolution
- Autonomous refactoring decisions

---

**🚀 Ready to build the future of AI-assisted development!** 
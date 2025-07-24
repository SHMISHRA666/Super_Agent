# Super Agent - Advanced Multi-Agent AI System

A sophisticated multi-agent AI system built on NetworkX graph execution that combines document processing, web search, browser automation, and intelligent task planning to provide comprehensive AI assistance.

## 🚀 Overview

Super Agent is an advanced AI orchestration system featuring **AgentLoop4** - a NetworkX graph-based execution engine that coordinates multiple specialized agents to handle complex queries. The system includes browser automation, MCP (Model Context Protocol) server integration, memory management, and real-time execution visualization.

## Link to Demo - https://youtu.be/n33XGT5XvWo

## 🏗️ Architecture

### Core Components

- **AgentLoop4**: NetworkX graph-based execution engine with sophisticated task orchestration
- **ExecutionContextManager**: Advanced context and state management with execution tracking
- **Graph Debugger**: Development and debugging tools for agent execution flows
- **MultiMCP**: Manages multiple MCP servers for different capabilities
- **BrowserMCP**: Advanced browser automation based on browser-use framework
- **Memory System**: Session management, indexing, and intelligent search
- **Action Executor**: Code execution and file generation with sandbox capabilities
- **Model Manager**: AI model management and cost tracking
- **Visualizer**: Real-time execution graph visualization and monitoring

### Agent Architecture

The system uses a **NetworkX graph-first approach** where agents execute in a dependency-aware graph structure:

- **PlannerAgent**: Creates NetworkX execution graphs and task dependencies
- **RetrieverAgent**: Searches and retrieves information from documents and web
- **ThinkerAgent**: Analyzes and processes complex information
- **QAAgent**: Handles question-answering with context awareness
- **DistillerAgent**: Summarizes and extracts key information from files
- **FormatterAgent**: Formats and structures output data
- **CoderAgent**: Handles code generation, analysis, and file creation
- **ExecutorAgent**: Executes planned actions and code with sandbox safety
- **ClarificationAgent**: Seeks clarification when requirements are ambiguous
- **SchedulerAgent**: Manages task scheduling and resource allocation

## 🔧 Features

### Graph-Based Execution
- **NetworkX Integration**: Task execution as directed acyclic graphs
- **Dependency Resolution**: Automatic handling of task dependencies
- **Parallel Execution**: Concurrent agent execution where possible
- **Failure Recovery**: Robust error handling and retry mechanisms
- **Real-time Visualization**: Live execution graph monitoring

### Document Processing
- **Multi-format Support**: PDF, DOC, CSV, text, and image files
- **FAISS Integration**: Vector-based document indexing and search
- **MarkItDown**: Advanced document parsing and conversion
- **Content Extraction**: Intelligent text and data extraction
- **File Profiling**: Automatic analysis of uploaded file structures

### Web Capabilities
- **Advanced Browser Automation**: Click, scroll, form filling, tab management
- **Content Extraction**: Structured data extraction from web pages
- **Web Search Integration**: Intelligent web search and content retrieval
- **URL Processing**: Content fetching and analysis from URLs
- **PDF Generation**: Save web pages as PDF documents

### Browser Automation (BrowserMCP)
Based on the browser-use framework with enhanced capabilities:
- **Element Interaction**: Click, input text, drag and drop
- **Navigation**: Tab management, back/forward, URL navigation
- **Content Manipulation**: Scroll, extract content, save PDFs
- **Special Actions**: Send keys, scroll to text, coordinate-based actions
- **Session Management**: Persistent browser sessions and context

### AI Integration
- **Google Gemini**: Primary model with cost tracking
- **Multi-agent Coordination**: Intelligent agent selection and routing
- **Context Preservation**: Session memory and state persistence
- **Token Management**: Usage tracking and cost optimization

### Development Tools
- **Graph Debugger**: Step-by-step execution debugging
- **Session Replay**: Replay and modify execution graphs
- **Cost Tracking**: Detailed token usage and cost analysis
- **Rich Logging**: Comprehensive execution logging with Rich console
- **Performance Monitoring**: Execution time and resource tracking

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- UV package manager (recommended for fast dependency management)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Super_agent
   ```

2. **Install dependencies using UV**
   ```bash
   uv sync
   ```

3. **Environment Setup**
   ```bash
   # Create and configure environment variables
   cp .env.example .env
   # Edit .env with your API keys (Google Gemini, etc.)
   ```

4. **Install Playwright browsers** (for browser automation)
   ```bash
   uv run playwright install
   ```

## 🚀 Usage

### Basic Usage

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Interactive Process**
   - Upload files (drag and drop or enter paths)
   - Enter your query
   - Watch the NetworkX graph execute your request
   - View results with cost analysis

### Example Queries

The system handles various complex queries:

- **Document Analysis**: "Analyze this financial report and extract key metrics"
- **Web Research**: "Research the latest AI developments and create a summary"
- **Code Generation**: "Create a web dashboard for this data with modern UI"
- **Multi-step Tasks**: "Compare BMW 7 series vs 5 series, research prices, and format as professional report"
- **Browser Automation**: "Navigate to this website and extract all product information"

### File Upload Support

Supports multiple file formats:
- **Documents**: PDF, DOC, DOCX, TXT, MD
- **Data**: CSV, Excel, JSON
- **Images**: PNG, JPG, JPEG (with OCR)
- **Code**: All programming languages

## ⚙️ Configuration

### Agent Configuration
Edit `config/agent_config.yaml` to customize agents:

```yaml
agents:
  PlannerAgent:
    prompt_file: "prompts/planner_prompt.txt"
    model: "gemini"
    mcp_servers: []
  
  CoderAgent:
    prompt_file: "prompts/coder_prompt.txt"
    model: "gemini"
    mcp_servers: ["documents", "websearch"]
```

### MCP Server Configuration
Configure servers in `config/mcp_server_config.yaml`:

```yaml
mcp_servers:
  - id: documents
    script: mcp_server_2.py
    description: "Document processing, PDF analysis, and local search"
  - id: websearch
    script: mcp_server_3.py
    description: "Web search, content extraction, and URL processing"
```

### Profile Configuration
Browser and system profiles in `config/profiles.yaml`

## 🏛️ Project Structure

```
Super_agent/
├── main.py                 # Application entry point
├── agentLoop/             # Core agent orchestration
│   ├── flow.py           # AgentLoop4 NetworkX execution engine
│   ├── agents.py         # Agent runner and management
│   ├── contextManager.py # Execution context and state management
│   ├── graph_debugger.py # Development and debugging tools
│   ├── visualizer.py     # Real-time execution visualization
│   ├── model_manager.py  # AI model management and cost tracking
│   └── output_analyzer.py # Result analysis and formatting
├── action/                # Action execution system
│   ├── executor.py       # Code execution and file generation
│   ├── execute_step.py   # Step execution logic
│   └── sandbox_state/    # Execution sandbox state
├── browserMCP/           # Advanced browser automation
│   ├── agent/           # Browser agent components
│   ├── browser/         # Browser control and session management
│   ├── dom/             # DOM processing and element handling
│   ├── controller/      # Browser control registry
│   ├── mcp_tools.py     # Browser automation tools
│   ├── utils.py         # Browser utilities
│   └── tests/           # Browser automation tests
├── mcp_servers/          # MCP server implementations
│   ├── multiMCP.py      # Multi-MCP coordination
│   ├── mcp_server_1.py  # Math, utilities, and Python sandbox
│   ├── mcp_server_2.py  # Document processing and FAISS search
│   ├── mcp_server_3.py  # Web search and content extraction
│   ├── mcp_server_4.py  # Additional utilities
│   ├── models.py        # Data models for MCP servers
│   └── tools/           # Specialized tools and utilities
├── memory/               # Memory and session management
│   ├── memory_indexer.py # Session indexing and search
│   ├── memory_search.py  # Memory search capabilities
│   ├── session_logs/     # Session execution logs
│   └── session_summaries_index/ # Session summaries
├── config/               # Configuration files
│   ├── agent_config.yaml # Agent configurations
│   ├── mcp_server_config.yaml # MCP server settings
│   └── profiles.yaml     # System and browser profiles
├── prompts/              # Agent prompt templates
│   ├── planner_prompt.txt # Planning agent prompt
│   ├── coder_prompt.txt   # Code generation agent
│   ├── retriever_prompt.txt # Information retrieval
│   └── [other agent prompts]
├── heuristics/           # Intelligent heuristics system
│   └── heuristics.py     # Decision-making logic
├── utils/                # Utility functions
│   ├── json_parser.py    # JSON parsing utilities
│   └── utils.py          # General utilities
└── media/                # Generated content and media
    ├── generated/        # Generated files and outputs
    ├── screenshots/      # Browser screenshots
    └── pdf/              # Generated PDF files
```

## 🔍 MCP Servers

### Available Servers

1. **Document Server** (`mcp_server_2.py`)
   - PDF processing with PyMuPDF4LLM
   - FAISS-based vector search and indexing
   - MarkItDown document conversion
   - Local document analysis and summarization
   - Multi-format file support

2. **Web Search Server** (`mcp_server_3.py`)
   - Advanced web search capabilities
   - Content extraction with Trafilatura
   - URL processing and validation
   - Web page analysis and summarization
   - Search result aggregation

3. **Math & Utilities Server** (`mcp_server_1.py`)
   - Mathematical operations and calculations
   - String processing and conversions
   - Python sandbox execution
   - Shell command execution (sandboxed)
   - Data processing utilities

4. **Browser Server** (BrowserMCP)
   - Full browser automation suite
   - Web page interaction and navigation
   - Content extraction and manipulation
   - Session management and persistence
   - Screenshot and PDF generation

## 🎯 Key Features

### NetworkX Graph Execution
- **Directed Acyclic Graphs**: Task execution as DAGs with dependency resolution
- **Parallel Processing**: Concurrent execution of independent tasks
- **Dynamic Scheduling**: Intelligent task scheduling based on dependencies
- **State Management**: Comprehensive execution state tracking
- **Failure Recovery**: Automatic retry and error handling

### Advanced Context Management
- **Session Persistence**: Long-running session memory and state
- **File Context Integration**: Automatic file profiling and context awareness
- **Query History**: Complete execution history and replay capabilities
- **Global State**: Shared state management across agent execution

### Intelligent Planning
- **Strategy-based Planning**: Conservative, aggressive, and balanced planning modes
- **Dynamic Task Generation**: Adaptive task creation based on context
- **Resource Optimization**: Efficient resource allocation and scheduling
- **Cost Optimization**: Token usage optimization and cost tracking

### Development & Debugging
- **Graph Debugger**: Interactive debugging of execution graphs
- **Session Replay**: Replay and modify previous executions
- **Performance Analytics**: Detailed performance and cost analysis
- **Rich Console**: Beautiful terminal output with progress tracking

## 🛠️ Development

### Adding New Agents

1. **Create agent prompt** in `prompts/agent_name_prompt.txt`
2. **Add configuration** in `config/agent_config.yaml`
3. **Update agent runner** in `agentLoop/agents.py` if needed

### Adding New MCP Servers

1. **Create server implementation** in `mcp_servers/mcp_server_X.py`
2. **Add server configuration** in `config/mcp_server_config.yaml`
3. **Update agent configurations** to use the new server capabilities

### Debugging Execution Graphs

Use the built-in graph debugger:
```bash
python agentLoop/graph_debugger.py
```

### Customizing Behavior

- **Prompts**: Edit files in `prompts/` directory
- **Heuristics**: Modify `heuristics/heuristics.py` for decision logic
- **Execution**: Customize `action/executor.py` for action handling

## 📊 Performance

- **Graph-based Execution**: Optimized task execution with dependency awareness
- **Concurrent Processing**: Multiple agents executing simultaneously
- **Memory Efficiency**: Intelligent memory management and garbage collection
- **Cost Tracking**: Real-time token usage and cost monitoring
- **Session Management**: Efficient long-running session handling

## 🔧 Dependencies

Key technologies and frameworks:
- **NetworkX**: Graph-based execution engine
- **FastMCP**: Model Context Protocol implementation
- **FAISS**: Vector search and indexing
- **Playwright**: Browser automation
- **Rich**: Terminal UI and logging
- **Pydantic**: Data validation and modeling
- **PyMuPDF4LLM**: PDF processing
- **Google Gemini**: Primary AI model

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 🙏 Acknowledgments

- **browser-use**: Browser automation framework foundation
- **MCP (Model Context Protocol)**: AI integration protocol
- **NetworkX**: Graph-based execution engine
- **Google Gemini**: AI model capabilities
- **FAISS**: Vector search technology

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the comprehensive documentation
- Review configuration examples
- Use the built-in graph debugger for development

---

**Super Agent** - Next-generation AI orchestration with NetworkX graph execution, advanced agent coordination, and comprehensive tool integration. 



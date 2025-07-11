# Super Agent - Multi-Agent AI System

A sophisticated multi-agent AI system that combines document processing, web search, browser automation, and intelligent task planning to provide comprehensive AI assistance.

## 🚀 Overview

Super Agent is an advanced AI system that orchestrates multiple specialized agents to handle complex queries. It features a NetworkX-based execution graph, MCP (Model Context Protocol) server integration, browser automation capabilities, and intelligent task planning.

## 🏗️ Architecture

### Core Components

- **AgentLoop4**: Main orchestration engine using NetworkX graphs for task execution
- **MultiMCP**: Manages multiple MCP servers for different capabilities
- **BrowserMCP**: Browser automation and web interaction capabilities
- **Memory System**: Session management and context persistence
- **Visualizer**: Real-time execution visualization

### Agent Types

The system includes several specialized agents:

- **PlannerAgent**: Creates execution plans and task graphs
- **RetrieverAgent**: Searches and retrieves information from documents and web
- **ThinkerAgent**: Analyzes and processes information
- **QAAgent**: Handles question-answering tasks
- **DistillerAgent**: Summarizes and extracts key information
- **FormatterAgent**: Formats and structures output
- **CoderAgent**: Handles code-related tasks
- **ExecutorAgent**: Executes planned actions
- **ClarificationAgent**: Seeks clarification when needed
- **SchedulerAgent**: Manages task scheduling

## 🔧 Features

### Document Processing
- PDF document parsing and analysis
- Text extraction and summarization
- FAISS-based document indexing
- Local document search capabilities

### Web Capabilities
- Web search integration
- Browser automation (click, scroll, form filling)
- Web page content extraction
- Tab management and navigation

### AI Integration
- Google Gemini model integration
- Multi-agent coordination
- Context-aware responses
- Session memory and persistence

### Visualization
- Real-time execution graph visualization
- Task status monitoring
- Execution flow tracking

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- UV package manager (recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Super_agent
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Environment Setup**
   ```bash
   # Copy and configure environment variables
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Install Playwright browsers** (for browser automation)
   ```bash
   playwright install
   ```

## 🚀 Usage

### Basic Usage

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Follow the interactive prompts**
   - Upload files (optional)
   - Enter your query
   - Watch the system execute your request

### Example Queries

The system can handle various types of queries:

- **Document Analysis**: "Summarize this PDF document"
- **Web Research**: "Find the latest information about AI trends"
- **Data Processing**: "Analyze this CSV file and find trends"
- **Code Tasks**: "Write a Python function to process this data"
- **Complex Tasks**: "Research BMW 7 series vs 5 series differences and format as markdown"

### File Upload

You can upload files for analysis:
- PDF documents
- CSV/Excel files
- Text files
- Images (with OCR capabilities)

## ⚙️ Configuration

### Agent Configuration
Edit `config/agent_config.yaml` to customize agent behavior:

```yaml
agents:
  PlannerAgent:
    prompt_file: "prompts/planner_prompt.txt"
    model: "gemini"
    mcp_servers: []
```

### MCP Server Configuration
Configure MCP servers in `config/mcp_server_config.yaml`:

```yaml
mcp_servers:
  - id: documents
    script: mcp_server_2.py
    description: "Document processing and search"
  - id: websearch
    script: mcp_server_3.py
    description: "Web search and content extraction"
```

## 🏛️ Project Structure

```
Super_agent/
├── action/                 # Action execution and sandbox
├── agentLoop/             # Core agent orchestration
│   ├── agents.py         # Agent definitions
│   ├── flow.py           # Main execution flow
│   ├── contextManager.py # Execution context management
│   └── visualizer.py     # Execution visualization
├── browserMCP/           # Browser automation
│   ├── agent/           # Browser agent components
│   ├── browser/         # Browser control
│   └── dom/            # DOM processing
├── config/              # Configuration files
├── mcp_servers/         # MCP server implementations
│   ├── mcp_server_1.py # Math and utilities
│   ├── mcp_server_2.py # Document processing
│   ├── mcp_server_3.py # Web search
│   └── multiMCP.py     # Multi-MCP coordination
├── memory/              # Memory and session management
├── prompts/             # Agent prompt templates
├── utils/               # Utility functions
└── main.py             # Application entry point
```

## 🔍 MCP Servers

### Available Servers

1. **Documents Server** (`mcp_server_2.py`)
   - PDF processing and text extraction
   - Document search and indexing
   - FAISS-based similarity search

2. **Web Search Server** (`mcp_server_3.py`)
   - Web search capabilities
   - Content extraction from web pages
   - URL processing and validation

3. **Math Server** (`mcp_server_1.py`)
   - Mathematical operations
   - String processing
   - Python sandbox execution

4. **Browser Server** (BrowserMCP)
   - Browser automation
   - Web page interaction
   - Content extraction

## 🎯 Key Features

### Intelligent Planning
- NetworkX-based execution graphs
- Dynamic task scheduling
- Dependency resolution
- Failure recovery

### Multi-Modal Processing
- Text, PDF, and image processing
- Web content extraction
- Browser automation
- Code execution

### Context Awareness
- Session memory
- File context integration
- Query history tracking
- State persistence

### Real-time Visualization
- Execution progress tracking
- Task status monitoring
- Graph visualization
- Performance metrics

## 🛠️ Development

### Adding New Agents

1. Create agent prompt in `prompts/`
2. Add agent configuration in `config/agent_config.yaml`
3. Implement agent logic in `agentLoop/agents.py`

### Adding New MCP Servers

1. Create server implementation in `mcp_servers/`
2. Add server configuration in `config/mcp_server_config.yaml`
3. Update agent configurations to use the new server

### Customizing Prompts

Edit prompt files in the `prompts/` directory to customize agent behavior and responses.

## 📊 Performance

- **Concurrent Execution**: Multiple agents can run simultaneously
- **Memory Management**: Efficient session and context management
- **Error Recovery**: Robust error handling and retry mechanisms
- **Scalability**: Modular architecture supports easy scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 🙏 Acknowledgments

- Browser automation code adapted from [browser-use](https://github.com/browser-use/browser-use)
- MCP (Model Context Protocol) integration
- NetworkX for graph-based execution
- Google Gemini for AI capabilities

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder
- Review the configuration examples

---

**Super Agent** - Empowering AI with multi-agent orchestration and comprehensive tool integration. 



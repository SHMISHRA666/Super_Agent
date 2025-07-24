#!/usr/bin/env python3
"""
Demo: CoderAgent Self-Calls in Production System
This script demonstrates CoderAgent being called more than 2 times sequentially 
using the actual AgentLoop4 system.
"""

import asyncio
from pathlib import Path
from main import load_server_configs
from mcp_servers.multiMCP import MultiMCP
from agentLoop.flow import AgentLoop4
from utils.utils import log_step
import json

async def demo_coderagent_self_calls():
    """Demo CoderAgent self-calls using the production AgentLoop4 system"""
    
    print("🚀 Demo: CoderAgent Self-Calls in Production System")
    print("=" * 60)
    
    # Load MCP servers
    log_step("📥 Loading MCP Servers...")
    server_configs = load_server_configs()
    multi_mcp = MultiMCP(server_configs)
    await multi_mcp.initialize()
    
    # Initialize AgentLoop4
    agent_loop = AgentLoop4(multi_mcp)
    
    try:
        # Use the test query from test_call_self_question.txt
        query = """Create a comprehensive web application with the following requirements:
1. First, generate an HTML page with a modern landing page structure,
2. Then, add CSS styling to make it visually appealing with gradients and animations,
3. Next, add JavaScript functionality for interactive elements like a contact form,
4. Finally, create a responsive design that works on mobile devices.
Make sure each step builds upon the previous one and requires the next iteration to continue the development process."""
        
        log_step("📝 Query (designed to trigger 4+ CoderAgent calls)", query)
        
        # Process with AgentLoop4
        log_step("🔄 Processing with AgentLoop4...")
        execution_context = await agent_loop.run(query, {}, {}, [])
        
        # Analyze the results for self-calls
        log_step("📊 Analyzing Self-Call Results...")
        
        # Look for CoderAgent steps with self-calls
        coder_steps = []
        for node_id in execution_context.plan_graph.nodes:
            node_data = execution_context.plan_graph.nodes[node_id]
            if node_data.get('agent') == 'CoderAgent':
                coder_steps.append({
                    'step_id': node_id,
                    'iterations': node_data.get('iterations', []),
                    'total_iterations': node_data.get('total_iterations', 1),
                    'self_call_count': node_data.get('self_call_count', 0),
                    'call_self_used': node_data.get('call_self_used', False)
                })
        
        # Display results
        print("\n" + "=" * 60)
        print("📋 CODERAGENT SELF-CALL ANALYSIS")
        print("=" * 60)
        
        for step in coder_steps:
            print(f"\n🔹 Step: {step['step_id']}")
            print(f"   Total Iterations: {step['total_iterations']}")
            print(f"   Self-Calls: {step['self_call_count']}")
            print(f"   Call-Self Used: {step['call_self_used']}")
            
            if step['iterations']:
                print("   Iteration Details:")
                for iteration in step['iterations']:
                    self_call_indicator = " [SELF-CALL]" if iteration.get('is_self_call', False) else ""
                    print(f"     - Iteration {iteration['iteration']}{self_call_indicator}")
        
        # Check for sequential calls (more than 2)
        total_coder_calls = sum(step['total_iterations'] for step in coder_steps)
        total_self_calls = sum(step['self_call_count'] for step in coder_steps)
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total CoderAgent Calls: {total_coder_calls}")
        print(f"   Total Self-Calls: {total_self_calls}")
        
        if total_coder_calls > 2:
            print(f"✅ SUCCESS: CoderAgent called {total_coder_calls} times (more than 2) sequentially!")
        else:
            print(f"⚠️  CoderAgent only called {total_coder_calls} times")
        
        # Show log file location
        session_id = execution_context.plan_graph.graph.get('session_id', 'unknown')
        if session_id != 'unknown':
            log_folder = Path("memory/session_logs")
            log_files = list(log_folder.rglob(f"{session_id}*"))
            if log_files:
                print(f"\n📋 Log files created:")
                for log_file in log_files:
                    print(f"   - {log_file}")
                    
                    # Show a sample of self_call entries
                    if log_file.name.endswith('_steps.json'):
                        try:
                            with open(log_file, 'r') as f:
                                logs = json.load(f)
                            
                            self_call_entries = [log for log in logs if log.get('self_call', False)]
                            if self_call_entries:
                                print(f"\n📝 Sample self_call=true entries from {log_file.name}:")
                                for i, entry in enumerate(self_call_entries[:3]):  # Show first 3
                                    print(f"   Entry {i+1}: agent_type={entry['agent_type']}, self_call={entry['self_call']}, timestamp={entry['timestamp']}")
                        except Exception as e:
                            print(f"   (Could not read log file: {e})")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await multi_mcp.shutdown()
    
    print("\n" + "=" * 60)
    print("🏁 Demo completed!")
    print("✅ Check the output above for evidence of CoderAgent self-calls")

if __name__ == "__main__":
    asyncio.run(demo_coderagent_self_calls()) 
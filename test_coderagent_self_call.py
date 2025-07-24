#!/usr/bin/env python3
"""
Test script to demonstrate CoderAgent self-calls
This script shows a use-case where CoderAgent is called more than 2 times sequentially.
"""

import asyncio
import json
from pathlib import Path
from agentLoop.agents import AgentRunner
from mcp_servers.multiMCP import MultiMCP
from utils.utils import log_step, log_error
import yaml

async def test_coderagent_self_calls():
    """Test CoderAgent with multiple self-calls"""
    
    print("🚀 Testing CoderAgent Self-Calls")
    print("=" * 50)
    
    # Load MCP server configs
    config_path = Path("config/mcp_server_config.yaml")
    if not config_path.exists():
        print("❌ MCP server config not found")
        return
    
    with open(config_path, "r") as f:
        server_configs = yaml.safe_load(f)["mcp_servers"]
    
    # Initialize MultiMCP
    multi_mcp = MultiMCP(server_configs)
    await multi_mcp.initialize()
    
    # Initialize AgentRunner
    agent_runner = AgentRunner(multi_mcp)
    
    try:
        # Test case: Web application development (designed to trigger 4+ self-calls)
        test_query = """Create a comprehensive web application with the following requirements:
1. First, generate an HTML page with a modern landing page structure,
2. Then, add CSS styling to make it visually appealing with gradients and animations,
3. Next, add JavaScript functionality for interactive elements like a contact form,
4. Finally, create a responsive design that works on mobile devices.
Make sure each step builds upon the previous one and requires the next iteration to continue the development process."""

        log_step("📝 Test Query", test_query)
        
        # Prepare input data that will trigger call_self behavior
        input_data = {
            "step_id": "T001",
            "agent_prompt": test_query,
            "reads": [],
            "writes": ["web_app_files"],
            "inputs": {},
            "session_context": {
                "session_id": "test_self_call_session",
                "created_at": "2025-01-25T12:00:00Z",
                "file_manifest": {}
            }
        }
        
        log_step("🤖 Starting CoderAgent Test")
        
        # Call 1: Initial call
        log_step("📞 Call 1: Initial CoderAgent call")
        result1 = await agent_runner.run_agent("CoderAgent", input_data)
        
        if result1["success"]:
            output1 = result1["output"]
            print(f"✅ Call 1 completed. call_self = {output1.get('call_self', False)}")
            
            # If call_self is True, make subsequent calls
            if output1.get("call_self", False):
                
                # Call 2: Self-call
                log_step("📞 Call 2: CoderAgent self-call")
                input_data2 = input_data.copy()
                input_data2.update({
                    "previous_output": output1,
                    "next_instruction": output1.get("next_instruction", "Continue development"),
                    "iteration_context": output1.get("iteration_context", {})
                })
                
                result2 = await agent_runner.run_agent("CoderAgent", input_data2)
                
                if result2["success"]:
                    output2 = result2["output"]
                    print(f"✅ Call 2 completed. call_self = {output2.get('call_self', False)}")
                    
                    # If call_self is still True, make a third call
                    if output2.get("call_self", False):
                        
                        # Call 3: Another self-call
                        log_step("📞 Call 3: CoderAgent self-call")
                        input_data3 = input_data.copy()
                        input_data3.update({
                            "previous_output": output2,
                            "next_instruction": output2.get("next_instruction", "Continue development"),
                            "iteration_context": output2.get("iteration_context", {})
                        })
                        
                        result3 = await agent_runner.run_agent("CoderAgent", input_data3)
                        
                        if result3["success"]:
                            output3 = result3["output"]
                            print(f"✅ Call 3 completed. call_self = {output3.get('call_self', False)}")
                            
                            # If call_self is still True, make a fourth call
                            if output3.get("call_self", False):
                                
                                # Call 4: Final self-call
                                log_step("📞 Call 4: CoderAgent self-call")
                                input_data4 = input_data.copy()
                                input_data4.update({
                                    "previous_output": output3,
                                    "next_instruction": output3.get("next_instruction", "Finalize development"),
                                    "iteration_context": output3.get("iteration_context", {})
                                })
                                
                                result4 = await agent_runner.run_agent("CoderAgent", input_data4)
                                
                                if result4["success"]:
                                    output4 = result4["output"]
                                    print(f"✅ Call 4 completed. call_self = {output4.get('call_self', False)}")
                                else:
                                    print(f"❌ Call 4 failed: {result4.get('error')}")
                            else:
                                print("🏁 CoderAgent completed after 3 calls")
                        else:
                            print(f"❌ Call 3 failed: {result3.get('error')}")
                    else:
                        print("🏁 CoderAgent completed after 2 calls")
                else:
                    print(f"❌ Call 2 failed: {result2.get('error')}")
            else:
                print("🏁 CoderAgent completed after 1 call (no self-call needed)")
        else:
            print(f"❌ Call 1 failed: {result1.get('error')}")
        
        # Show log file location
        log_folder = Path("memory/session_logs")
        if log_folder.exists():
            log_files = list(log_folder.rglob("test_self_call_session*"))
            if log_files:
                log_step("📋 Check the log files for self_call=true entries:", [str(f) for f in log_files])
            else:
                log_step("📋 Log files will be created in:", str(log_folder))
        
    except Exception as e:
        log_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await multi_mcp.shutdown()
        
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("✅ Check the console output above for [SELF-CALL] indicators")
    print("✅ Check the log files in memory/session_logs/ for self_call=true entries")

if __name__ == "__main__":
    asyncio.run(test_coderagent_self_calls()) 
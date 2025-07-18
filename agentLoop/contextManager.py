# contextManager.py – 100% NetworkX Graph-First (SIMPLIFIED)

import networkx as nx
import json
import time
from datetime import datetime
from pathlib import Path
import asyncio
from action.executor import run_user_code
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

class ExecutionContextManager:
    def __init__(self, plan_graph: dict, session_id: str = None, original_query: str = None, file_manifest: list = None, debug_mode: bool = False):
        # 🎯 Build NetworkX graph with ALL data
        self.plan_graph = nx.DiGraph()
        
        # Store session metadata in graph attributes
        self.plan_graph.graph['session_id'] = session_id or str(int(time.time()))[-8:]
        self.plan_graph.graph['original_query'] = original_query
        self.plan_graph.graph['file_manifest'] = file_manifest or []
        self.plan_graph.graph['created_at'] = datetime.utcnow().isoformat()
        self.plan_graph.graph['status'] = 'running'
        self.plan_graph.graph['globals_schema'] = {}
        
        # Add ROOT node
        self.plan_graph.add_node("ROOT",
            description="Initial Query",
            agent="System", 
            status='completed',
            output=None,
            error=None,
            cost=0.0,
            start_time=None,
            end_time=None,
            execution_time=0.0
        )

        # Build plan DAG
        for node in plan_graph.get("nodes", []):
            self.plan_graph.add_node(node["id"], 
                **node,
                status='pending',
                output=None,
                error=None,
                cost=0.0,
                start_time=None,
                end_time=None,
                execution_time=0.0
            )
            
        for edge in plan_graph.get("edges", []):
            self.plan_graph.add_edge(edge["source"], edge["target"])

        self.debug_mode = debug_mode
        self._live_display = None

    def get_ready_steps(self):
        """Return all steps whose dependencies are complete and not yet run."""
        ready = []
        
        for node_id in self.plan_graph.nodes:
            node_data = self.plan_graph.nodes[node_id]
            
            if node_id == "ROOT":
                continue
                
            status = node_data.get('status', 'pending')
            if status in ['completed', 'failed', 'running']:
                continue
                
            # Check if all dependencies are complete
            predecessors = list(self.plan_graph.predecessors(node_id))
            all_deps_complete = all(
                self.plan_graph.nodes[p].get('status', 'pending') == 'completed'
                for p in predecessors
            )
                
            if all_deps_complete:
                ready.append(node_id)
        
        return ready

    def mark_running(self, step_id):
        """Mark step as running"""
        self.plan_graph.nodes[step_id]['status'] = 'running'
        self.plan_graph.nodes[step_id]['start_time'] = datetime.utcnow().isoformat()
        self._auto_save()

    def _has_executable_code(self, output):
        """Universal detection of executable code patterns"""
        if not isinstance(output, dict):
            return False
        
        return (
            "code_variants" in output or
            any(k.startswith("CODE_") for k in output.keys()) or
            any(key in output for key in ["tool_calls", "schedule_tool", "browser_commands", "python_code"])
        )
    
    def _extract_executable_code(self, output):
        """Extract executable code"""
        code_to_execute = {}
        
        if "code_variants" in output:
            for key, code in output["code_variants"].items():
                if isinstance(code, str):
                    code_to_execute[key] = code.strip()
        
        return code_to_execute
    
    async def _auto_execute_code(self, step_id, output):
        """Execute code with COMPLETE variable injection"""
        code_to_execute = self._extract_executable_code(output)
        
        if not code_to_execute:
            return {"status": "error", "error": "No executable code found"}
        
        # Get node data for context
        node_data = self.plan_graph.nodes[step_id]
        reads = node_data.get("reads", [])
        
        # Get globals_schema for injection
        globals_schema = self.plan_graph.graph['globals_schema']
        
        for code_key, code in code_to_execute.items():
            try:
                # INJECT ALL AVAILABLE VARIABLES
                globals_injection = ""
                
                # 1. Inject ALL globals_schema variables
                for var_name, var_value in globals_schema.items():
                    globals_injection += f'{var_name} = {repr(var_value)}\n'
                
                # 2. Inject agent's own output variables
                for var_name, var_value in output.items():
                    if var_name not in ['code_variants', 'call_self', 'cost', 'input_tokens', 'output_tokens', 'execution_result', 'execution_status', 'execution_error', 'execution_time', 'executed_variant']:
                        globals_injection += f'{var_name} = {repr(var_value)}\n'
                
                # 3. Create convenience variables for reads
                reads_data = {}
                for read_key in reads:
                    if read_key in globals_schema:
                        reads_data[read_key] = globals_schema[read_key]
                
                globals_injection += f'reads_data = {repr(reads_data)}\n'
                
                enhanced_code = globals_injection + code
                
                # Create the proper output_data structure for run_user_code
                output_data = {
                    "code_variants": {
                        code_key: enhanced_code
                    }
                }
                
                result = await run_user_code(
                    output_data,
                    self.multi_mcp if hasattr(self, 'multi_mcp') else None,
                    self.plan_graph.graph['session_id'],
                    globals_schema,
                    {}  # inputs
                )
                
                if result.get("status") == "success":
                    result["executed_variant"] = code_key
                    return result
                
            except Exception as e:
                continue
        
        return {"status": "error", "error": "All code variants failed"}
    
    def _merge_execution_results(self, original_output, execution_result):
        """Merge execution results into agent output with enhanced handling"""
        if not isinstance(original_output, dict):
            return original_output
        
        enhanced_output = original_output.copy()
        
        # Add execution metadata
        enhanced_output["execution_result"] = execution_result.get("result")
        enhanced_output["execution_status"] = execution_result.get("status")
        enhanced_output["execution_error"] = execution_result.get("error") 
        enhanced_output["execution_time"] = execution_result.get("execution_time")
        enhanced_output["executed_variant"] = execution_result.get("executed_variant")
        
        # IMPROVED: Better handling of execution results
        if execution_result and execution_result.get("status") == "success":
            result_data = execution_result.get("result", {})
            
            # CRITICAL FIX: Extract variables from result_data and merge them at top level
            # This is the key fix - the variables are in execution_result["result"]
            if isinstance(result_data, dict) and result_data:
                print(f"🔄 CRITICAL FIX: Merging variables from result_data to top level")
                for key, value in result_data.items():
                    if isinstance(value, (str, int, float, bool, list, dict)):
                        enhanced_output[key] = value
                        print(f"🔄 Merged variable {key} = {type(value).__name__}: {value}")
                    else:
                        enhanced_output[key] = str(value)
                        print(f"🔄 Merged variable {key} = str (converted): {str(value)}")
            
            # IMPROVED: Handle nested web search results structure
            if isinstance(result_data, dict):
                for key, value in result_data.items():
                    # Check if this is a nested web search result structure
                    if isinstance(value, dict) and 'content' in value and isinstance(value['content'], list):
                        try:
                            # Extract the JSON string from content[0]['text']
                            if value['content'] and len(value['content']) > 0:
                                text_content = value['content'][0].get('text', '')
                                if text_content.startswith('[') and text_content.endswith(']'):
                                    import json
                                    parsed_data = json.loads(text_content)
                                    enhanced_output[key] = parsed_data
                                    print(f"🔄 Merged parsed data for {key}: {len(parsed_data)} items")
                                else:
                                    enhanced_output[key] = text_content
                                    print(f"🔄 Merged text content for {key}: {text_content[:100]}...")
                            else:
                                enhanced_output[key] = value
                                print(f"🔄 Merged nested structure for {key}")
                        except (json.JSONDecodeError, KeyError, IndexError) as e:
                            print(f"⚠️  Failed to parse nested structure for {key}: {e}")
                            enhanced_output[key] = value
                    else:
                        # IMPROVED: Ensure we merge the actual value
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            enhanced_output[key] = value
                            print(f"🔄 Merged {key} = {type(value).__name__}: {value}")
                        else:
                            enhanced_output[key] = str(value)
                            print(f"🔄 Merged {key} = str (converted): {str(value)}")
            else:
                # Handle non-dict results
                enhanced_output["execution_result"] = result_data
                print(f"🔄 Merged execution result: {result_data}")
        
        return enhanced_output
    
    def _is_clarification_request(self, agent_type, output):
        """Check if agent output requires user interaction"""
        return (
            agent_type == "ClarificationAgent" and 
            isinstance(output, dict) and
            "clarificationMessage" in output
        )
    
    def set_live_display(self, live_display):
        """Set reference to Live display for pausing during user interaction"""
        self._live_display = live_display
    
    def _handle_user_interaction_rich(self, clarification_output):
        """Handle user interaction with Rich prompts"""
        message = clarification_output.get("clarificationMessage", "")
        options = clarification_output.get("options", [])
        
        # Pause Live display during user interaction
        live_was_running = False
        if self._live_display and self._live_display._live_render.is_started:
            self._live_display.stop()
            live_was_running = True
        
        try:
            console = Console()
            console.clear()
            console.print(Panel(
                Text(message, style="bold white"),
                title="🤔 User Input Required",
                border_style="yellow",
                padding=(1, 2)
            ))
            
            if options:
                console.print("\n[bold cyan]Available Options:[/bold cyan]")
                for i, option in enumerate(options, 1):
                    console.print(f"  [bold white]{i}.[/bold white] {option}")
                
                choices = [str(i) for i in range(1, len(options) + 1)]
                choice = Prompt.ask(
                    "\n[bold green]Select option[/bold green]",
                    choices=choices,
                    default="1",
                    show_choices=False
                )
                
                selected_option = options[int(choice) - 1]
                console.print(f"[dim]✓ Selected: {selected_option}[/dim]")
                return selected_option
            else:
                response = Prompt.ask("\n[bold green]Your response[/bold green]")
                console.print(f"[dim]✓ Response: {response}[/dim]")
                return response
                
        finally:
            if live_was_running and self._live_display:
                self._live_display.start()
    
    async def mark_done(self, step_id, output=None, cost=None, input_tokens=None, output_tokens=None):
        """Mark step as completed with IMPROVED extraction logic"""
        node_data = self.plan_graph.nodes[step_id]
        agent_type = node_data.get('agent', '')
        writes = node_data.get("writes", [])
        
        # Extract cost data
        if output and isinstance(output, dict):
            cost = cost or output.get('cost', 0.0)
            input_tokens = input_tokens or output.get('input_tokens', 0)
            output_tokens = output_tokens or output.get('output_tokens', 0)
        
        # USER INTERACTION CHECK
        if self._is_clarification_request(agent_type, output):
            try:
                user_response = self._handle_user_interaction_rich(output)
                writes_to = output.get("writes_to", "user_response")
                self.plan_graph.graph['globals_schema'][writes_to] = user_response
                
                output = output.copy()
                output["user_response"] = user_response
                output["interaction_completed"] = True
                print(f"✅ User input captured: {writes_to} = '{user_response}'")
                
            except Exception as e:
                print(f"❌ User interaction failed: {e}")
        
        # CODE EXECUTION CHECK
        execution_result = None
        if self._has_executable_code(output):
            try:
                execution_result = await self._auto_execute_code(step_id, output)
                output = self._merge_execution_results(output, execution_result)
            except Exception as e:
                print(f"❌ Code execution failed: {e}")
        
        # FORMATTERAGENT FILE SAVING CHECK
        if agent_type == "FormatterAgent" and output and isinstance(output, dict):
            try:
                self._save_formatter_report(step_id, output, writes)
            except Exception as e:
                print(f"❌ FormatterAgent file saving failed: {e}")
        
        # IMPROVED EXTRACTION LOGIC - Enhanced to handle nested structures
        globals_schema = self.plan_graph.graph['globals_schema']
        
        if writes:
            for write_key in writes:
                extracted = False
                
                # Strategy 1: Extract from code execution results (RetrieverAgent, CoderAgent)
                if execution_result and execution_result.get("status") == "success":
                    result_data = execution_result.get("result", {})
                    print(f"🔍 DEBUG: Checking result_data for {write_key}")
                    print(f"🔍 DEBUG: result_data keys: {list(result_data.keys())}")
                    print(f"🔍 DEBUG: result_data type: {type(result_data)}")
                    print(f"🔍 DEBUG: result_data content: {result_data}")
                    print(f"🔍 DEBUG: Full execution_result: {execution_result}")
                    
                    # FIXED: Also check the top-level execution result for direct variable extraction
                    if not result_data and execution_result:
                        print(f"🔍 DEBUG: Trying top-level execution_result extraction")
                        result_data = execution_result
                        print(f"🔍 DEBUG: Using top-level execution_result as result_data: {result_data}")
                    
                    # IMPROVED: Handle nested web search results structure
                    if write_key in result_data:
                        value = result_data[write_key]
                        
                        # Check if this is a nested web search result structure
                        if isinstance(value, dict) and 'content' in value and isinstance(value['content'], list):
                            try:
                                # Extract the JSON string from content[0]['text']
                                if value['content'] and len(value['content']) > 0:
                                    text_content = value['content'][0].get('text', '')
                                    if text_content.startswith('[') and text_content.endswith(']'):
                                        import json
                                        parsed_data = json.loads(text_content)
                                        globals_schema[write_key] = parsed_data
                                        print(f"✅ Extracted {write_key} = {len(parsed_data)} items (parsed from nested structure)")
                                        extracted = True
                            except (json.JSONDecodeError, KeyError, IndexError) as e:
                                print(f"⚠️  Failed to parse nested structure for {write_key}: {e}")
                        
                        # IMPROVED: Handle direct key access with proper value extraction
                        if not extracted:
                            # Ensure we're extracting the actual value, not just the structure
                            if isinstance(value, (str, int, float, bool, list, dict)):
                                globals_schema[write_key] = value
                                print(f"✅ Extracted {write_key} = {type(value).__name__} (direct): {value}")
                                extracted = True
                            else:
                                # Convert to string if it's not a standard type
                                globals_schema[write_key] = str(value)
                                print(f"✅ Extracted {write_key} = str (converted): {str(value)}")
                                extracted = True
                    
                    # Strategy 2: Deep search in nested structures with improved value handling
                    if not extracted:
                        def deep_search(data, target_key):
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if key == target_key:
                                        return value
                                    result = deep_search(value, target_key)
                                    if result is not None:
                                        return result
                            elif isinstance(data, list):
                                for item in data:
                                    result = deep_search(item, target_key)
                                    if result is not None:
                                        return result
                            return None
                        
                        found_value = deep_search(result_data, write_key)
                        if found_value is not None:
                            # IMPROVED: Ensure we extract the actual value
                            if isinstance(found_value, (str, int, float, bool, list, dict)):
                                globals_schema[write_key] = found_value
                                print(f"✅ Extracted {write_key} = {type(found_value).__name__} (deep search): {found_value}")
                            else:
                                globals_schema[write_key] = str(found_value)
                                print(f"✅ Extracted {write_key} = str (deep search converted): {str(found_value)}")
                            extracted = True
                
                # Strategy 3: Extract from direct agent output with improved value handling
                if not extracted and output and isinstance(output, dict):
                    # PRIORITY FIX: Check if the key exists directly in output (after merge from execution)
                    if write_key in output:
                        value = output[write_key]
                        # IMPROVED: Ensure we extract the actual value
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            globals_schema[write_key] = value
                            print(f"✅ Extracted {write_key} = {type(value).__name__} (direct output after merge): {value}")
                        else:
                            globals_schema[write_key] = str(value)
                            print(f"✅ Extracted {write_key} = str (direct output after merge converted): {str(value)}")
                        extracted = True
                    
                    # BACKUP: Also check execution_result field in the output (from merge)
                    elif not extracted and "execution_result" in output and isinstance(output["execution_result"], dict):
                        exec_result = output["execution_result"]
                        if write_key in exec_result:
                            value = exec_result[write_key]
                            if isinstance(value, (str, int, float, bool, list, dict)):
                                globals_schema[write_key] = value
                                print(f"✅ Extracted {write_key} = {type(value).__name__} (from execution_result): {value}")
                            else:
                                globals_schema[write_key] = str(value)
                                print(f"✅ Extracted {write_key} = str (from execution_result converted): {str(value)}")
                            extracted = True
                    else:
                        # Deep search in output with improved value handling
                        def deep_search_output(data, target_key):
                            if isinstance(data, dict):
                                for key, value in data.items():
                                    if key == target_key:
                                        return value
                                    result = deep_search_output(value, target_key)
                                    if result is not None:
                                        return result
                            elif isinstance(data, list):
                                for item in data:
                                    result = deep_search_output(item, target_key)
                                    if result is not None:
                                        return result
                            return None
                        
                        found_value = deep_search_output(output, write_key)
                        if found_value is not None:
                            # IMPROVED: Ensure we extract the actual value
                            if isinstance(found_value, (str, int, float, bool, list, dict)):
                                globals_schema[write_key] = found_value
                                print(f"✅ Extracted {write_key} = {type(found_value).__name__} (deep output search): {found_value}")
                            else:
                                globals_schema[write_key] = str(found_value)
                                print(f"✅ Extracted {write_key} = str (deep output search converted): {str(found_value)}")
                            extracted = True
                
                # Strategy 4: Special FormatterAgent pattern matching
                if not extracted and agent_type == "FormatterAgent" and output:
                    print(f"🔍 DEBUG: FormatterAgent pattern matching for {write_key}")
                    print(f"🔍 DEBUG: Available output keys: {list(output.keys())}")
                    
                    # Enhanced pattern matching for FormatterAgent
                    formatter_patterns = [
                        f"formatted_{write_key}",  # Original pattern
                        f"formatted_report_{write_key.replace('_T', '_T')}",  # formatted_report_T003
                        f"formatted_html_{write_key.replace('_T', '_T')}",  # formatted_html_T003
                        f"formatted_output_{write_key.replace('_T', '_T')}",  # formatted_output_T003
                        f"formatted_{write_key.replace('_T', '_T')}",  # formatted_T003
                        f"formatted_report_{step_id}",  # formatted_report_T003
                        f"formatted_html_{step_id}",  # formatted_html_T003
                        f"formatted_output_{step_id}",  # formatted_output_T003
                        f"formatted_{step_id}",  # formatted_T003
                        "formatted_report",  # Generic formatted_report
                        "formatted_html",  # Generic formatted_html
                        "formatted_output",  # Generic formatted_output
                        "formatted"  # Generic formatted
                    ]
                    
                    print(f"🔍 DEBUG: Trying patterns: {formatter_patterns}")
                    
                    # Try each pattern
                    for pattern in formatter_patterns:
                        if pattern in output and output[pattern]:
                            globals_schema[write_key] = output[pattern]
                            print(f"✅ Extracted {write_key} = {type(output[pattern]).__name__} (formatter pattern: {pattern})")
                            extracted = True
                            break
                        elif pattern in output:
                            print(f"⚠️  Pattern '{pattern}' found but value is empty")
                        else:
                            print(f"❌ Pattern '{pattern}' not found")
                    
                    # If no pattern matched, try to find any key containing 'formatted'
                    if not extracted:
                        print(f"🔍 DEBUG: Trying fallback search for 'formatted' keys")
                        for key, value in output.items():
                            if 'formatted' in key.lower() and value:
                                globals_schema[write_key] = value
                                print(f"✅ Extracted {write_key} = {type(value).__name__} (formatter fallback: {key})")
                                extracted = True
                                break
                            elif 'formatted' in key.lower():
                                print(f"⚠️  Found 'formatted' key '{key}' but value is empty")
                    
                    # Final fallback: look for any key that might contain the expected data
                    if not extracted:
                        print(f"🔍 DEBUG: Trying comprehensive fallback search")
                        # Look for keys containing step_id or write_key components
                        search_terms = [step_id, write_key, write_key.replace('_T', '_T')]
                        for key, value in output.items():
                            if value and any(term in key for term in search_terms):
                                globals_schema[write_key] = value
                                print(f"✅ Extracted {write_key} = {type(value).__name__} (comprehensive fallback: {key})")
                                extracted = True
                                break
                            elif any(term in key for term in search_terms):
                                print(f"⚠️  Found matching key '{key}' but value is empty")
                    
                    if not extracted:
                        print(f"❌ No formatter patterns matched for {write_key}")
                
                # Strategy 5: Emergency fallback with better debugging and value extraction
                if not extracted:
                    print(f"⚠️  Could not extract {write_key}")
                    print(f"   Available execution result keys: {list(execution_result.get('result', {}).keys()) if execution_result else []}")
                    print(f"   Available output keys: {list(output.keys()) if output else []}")
                    print(f"   Execution result status: {execution_result.get('status') if execution_result else None}")
                    
                    # IMPROVED: Use available data instead of empty list
                    if execution_result and execution_result.get("result"):
                        result_data = execution_result.get("result", {})
                        if isinstance(result_data, dict) and result_data:
                            # Use the first available key as fallback
                            first_key = next(iter(result_data.keys()), None)
                            if first_key:
                                fallback_value = result_data[first_key]
                                # IMPROVED: Ensure we extract the actual value
                                if isinstance(fallback_value, (str, int, float, bool, list, dict)):
                                    globals_schema[write_key] = fallback_value
                                    print(f"🔄 Fallback: Using {first_key} for {write_key}: {fallback_value}")
                                else:
                                    globals_schema[write_key] = str(fallback_value)
                                    print(f"🔄 Fallback: Using {first_key} for {write_key} (converted): {str(fallback_value)}")
                                extracted = True
                    
                    # IMPROVED: Try to find any meaningful data in output
                    if not extracted and output and isinstance(output, dict):
                        for key, value in output.items():
                            if value and isinstance(value, (str, int, float, bool, list, dict)):
                                globals_schema[write_key] = value
                                print(f"🔄 Output fallback: Using {key} for {write_key}: {value}")
                                extracted = True
                                break
                            elif value:
                                globals_schema[write_key] = str(value)
                                print(f"🔄 Output fallback: Using {key} for {write_key} (converted): {str(value)}")
                                extracted = True
                                break
                    
                    if not extracted:
                        # IMPROVED: Only use empty list as absolute last resort
                        print(f"❌ No data available for {write_key}, using empty list as last resort")
                        globals_schema[write_key] = []
        
        # Store results
        node_data['status'] = 'completed'
        node_data['end_time'] = datetime.utcnow().isoformat()
        node_data['output'] = output
        node_data['cost'] = cost or 0.0
        node_data['input_tokens'] = input_tokens or 0
        node_data['output_tokens'] = output_tokens or 0
        node_data['total_tokens'] = (input_tokens or 0) + (output_tokens or 0)
        
        # Calculate execution time
        if 'start_time' in node_data and node_data['start_time']:
            start = datetime.fromisoformat(node_data['start_time'])
            end = datetime.fromisoformat(node_data['end_time'])
            node_data['execution_time'] = (end - start).total_seconds()
        
        print(f"✅ {step_id} completed successfully")
        self._auto_save()

    def _save_formatter_report(self, step_id: str, output: dict, writes: list):
        """Save FormatterAgent reports to media folder"""
        session_id = self.plan_graph.graph['session_id']
        original_query = self.plan_graph.graph['original_query']
        
        # Create session directory
        output_dir = Path(f"media/generated/{session_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Look for formatted output fields
        saved_files = []
        
        # First try exact matches from writes
        for write_key in writes:
            if write_key in output and output[write_key]:
                content = output[write_key]
                
                # Determine file extension based on format
                if output.get("final_format") == "html":
                    extension = "html"
                    filename = f"report_{step_id}.html"
                elif output.get("final_format") == "markdown":
                    extension = "md"
                    filename = f"report_{step_id}.md"
                else:
                    # Default to HTML if format not specified
                    extension = "html"
                    filename = f"report_{step_id}.html"
                
                # Create safe filename
                safe_filename = Path(filename).name
                filepath = output_dir / safe_filename
                
                try:
                    # Write file with UTF-8 encoding
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Track file size
                    file_size = len(content.encode('utf-8'))
                    saved_files.append({
                        "filename": safe_filename,
                        "filepath": str(filepath),
                        "size_bytes": file_size,
                        "format": output.get("final_format", "html")
                    })
                    
                    print(f"💾 Saved FormatterAgent report: {safe_filename} ({file_size:,} bytes)")
                    
                except Exception as e:
                    print(f"❌ Failed to save {safe_filename}: {str(e)}")
        
        # If no files saved from writes, look for common FormatterAgent output patterns
        if not saved_files:
            # Look for common FormatterAgent output field patterns
            formatter_patterns = [
                f"formatted_report_{step_id}",
                f"formatted_html_{step_id}",
                f"formatted_output_{step_id}",
                "formatted_report",
                "formatted_html",
                "formatted_output"
            ]
            
            for pattern in formatter_patterns:
                if pattern in output and output[pattern]:
                    content = output[pattern]
                    
                    # Determine file extension based on format
                    if output.get("final_format") == "html":
                        extension = "html"
                        filename = f"report_{step_id}.html"
                    elif output.get("final_format") == "markdown":
                        extension = "md"
                        filename = f"report_{step_id}.md"
                    else:
                        # Default to HTML if format not specified
                        extension = "html"
                        filename = f"report_{step_id}.html"
                    
                    # Create safe filename
                    safe_filename = Path(filename).name
                    filepath = output_dir / safe_filename
                    
                    try:
                        # Write file with UTF-8 encoding
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Track file size
                        file_size = len(content.encode('utf-8'))
                        saved_files.append({
                            "filename": safe_filename,
                            "filepath": str(filepath),
                            "size_bytes": file_size,
                            "format": output.get("final_format", "html")
                        })
                        
                        print(f"💾 Saved FormatterAgent report: {safe_filename} ({file_size:,} bytes)")
                        break  # Found and saved, no need to check other patterns
                        
                    except Exception as e:
                        print(f"❌ Failed to save {safe_filename}: {str(e)}")
        
        # Also save a summary JSON file with metadata
        if saved_files:
            summary_data = {
                "session_id": session_id,
                "step_id": step_id,
                "original_query": original_query,
                "timestamp": datetime.utcnow().isoformat(),
                "saved_files": saved_files,
                "formatter_output": {
                    "final_format": output.get("final_format"),
                    "reasoning": output.get("reasoning"),
                    "call_self": output.get("call_self", False)
                }
            }
            
            summary_file = output_dir / f"report_summary_{step_id}.json"
            try:
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, indent=2, ensure_ascii=False)
                print(f"💾 Saved report summary: {summary_file.name}")
            except Exception as e:
                print(f"❌ Failed to save summary: {str(e)}")
        else:
            print(f"⚠️  No FormatterAgent output found to save for step {step_id}")
            print(f"   Available keys: {list(output.keys())}")
            print(f"   Writes: {writes}")
        
        return saved_files

    def mark_failed(self, step_id, error=None):
        """Mark step as failed"""
        node_data = self.plan_graph.nodes[step_id]
        node_data['status'] = 'failed'
        node_data['end_time'] = datetime.utcnow().isoformat()
        node_data['error'] = str(error) if error else None
        
        if node_data['start_time']:
            start = datetime.fromisoformat(node_data['start_time'])
            end = datetime.fromisoformat(node_data['end_time'])
            node_data['execution_time'] = (end - start).total_seconds()
            
        self._auto_save()

    def get_step_data(self, step_id):
        """Get all step data from graph"""
        return self.plan_graph.nodes[step_id]

    def _debug_data_structure(self, data, name="data", max_depth=3, current_depth=0):
        """Helper method to debug data structures"""
        if current_depth >= max_depth:
            return f"{name}: <max depth reached>"
        
        if isinstance(data, dict):
            result = f"{name}: dict with keys {list(data.keys())}"
            if current_depth < max_depth - 1:
                for key, value in list(data.items())[:5]:  # Limit to first 5 items
                    result += f"\n  {key}: {self._debug_data_structure(value, f'{name}.{key}', max_depth, current_depth + 1)}"
        elif isinstance(data, list):
            result = f"{name}: list with {len(data)} items"
            if data and current_depth < max_depth - 1:
                result += f"\n  First item: {self._debug_data_structure(data[0], f'{name}[0]', max_depth, current_depth + 1)}"
        else:
            result = f"{name}: {type(data).__name__} = {str(data)[:100]}"
        
        return result

    def get_inputs(self, reads):
        """Get input data from graph globals_schema with improved debugging"""
        inputs = {}
        globals_schema = self.plan_graph.graph['globals_schema']
        
        print(f"🔍 DEBUG: Getting inputs for reads: {reads}")
        print(f"🔍 DEBUG: Available globals_schema keys: {list(globals_schema.keys())}")
        
        for read_key in reads:
            if read_key in globals_schema:
                value = globals_schema[read_key]
                inputs[read_key] = value
                # IMPROVED: Show actual content for better debugging
                if isinstance(value, (str, int, float, bool)):
                    print(f"✅ Found input '{read_key}' = {type(value).__name__}: {value}")
                elif isinstance(value, list):
                    print(f"✅ Found input '{read_key}' = list with {len(value)} items: {value[:3] if len(value) > 3 else value}")
                elif isinstance(value, dict):
                    print(f"✅ Found input '{read_key}' = dict with keys: {list(value.keys())[:5]}")
                else:
                    print(f"✅ Found input '{read_key}' = {type(value).__name__}: {str(value)[:100]}")
            else:
                print(f"⚠️  Missing dependency: '{read_key}' not found in globals_schema")
                print(f"📋 Available keys: {list(globals_schema.keys())}")
                # IMPROVED: Provide more helpful debugging information
                similar_keys = [key for key in globals_schema.keys() if read_key.lower() in key.lower() or key.lower() in read_key.lower()]
                if similar_keys:
                    print(f"💡 Similar keys found: {similar_keys}")
        
        print(f"🔍 DEBUG: Final inputs: {list(inputs.keys())}")
        return inputs

    def all_done(self):
        """Check if all steps are completed or failed"""
        return all(
            self.plan_graph.nodes[node_id]['status'] in ['completed', 'failed']
            for node_id in self.plan_graph.nodes
        )

    def get_execution_summary(self):
        """Get execution summary with cost and token breakdown"""
        completed = sum(1 for node_id in self.plan_graph.nodes 
                       if node_id != "ROOT" and 
                       self.plan_graph.nodes[node_id].get('status') == 'completed')
        failed = sum(1 for node_id in self.plan_graph.nodes 
                    if node_id != "ROOT" and 
                    self.plan_graph.nodes[node_id].get('status') == 'failed')
        total = len(self.plan_graph.nodes) - 1
        
        # Calculate costs
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        cost_breakdown = {}
        
        for node_id in self.plan_graph.nodes:
            if node_id != "ROOT":
                node_data = self.plan_graph.nodes[node_id]
                node_cost = node_data.get('cost', 0.0)
                node_input_tokens = node_data.get('input_tokens', 0)
                node_output_tokens = node_data.get('output_tokens', 0)
                
                if node_cost > 0:
                    agent = node_data.get('agent', 'Unknown')
                    cost_breakdown[f"{node_id} ({agent})"] = {
                        "cost": node_cost,
                        "input_tokens": node_input_tokens,
                        "output_tokens": node_output_tokens
                    }
                
                total_cost += node_cost
                total_input_tokens += node_input_tokens
                total_output_tokens += node_output_tokens
        
        # Get final outputs
        final_outputs = {}
        all_reads = set()
        all_writes = set()
        
        for node_id in self.plan_graph.nodes:
            node_data = self.plan_graph.nodes[node_id]
            all_reads.update(node_data.get("reads", []))
            all_writes.update(node_data.get("writes", []))
        
        final_write_keys = all_writes - all_reads
        globals_schema = self.plan_graph.graph['globals_schema']
        for key in final_write_keys:
            if key in globals_schema:
                final_outputs[key] = globals_schema[key]

        return {
            "session_id": self.plan_graph.graph['session_id'],
            "original_query": self.plan_graph.graph['original_query'],
            "completed_steps": completed,
            "failed_steps": failed,
            "total_steps": total,
            "total_cost": total_cost,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "cost_breakdown": cost_breakdown,
            "final_outputs": final_outputs,
            "globals_schema": globals_schema
        }

    def set_file_profiles(self, file_profiles):
        """Store file profiles in graph attributes"""
        self.plan_graph.graph['file_profiles'] = file_profiles

    def set_multi_mcp(self, multi_mcp):
        """Set multi_mcp reference for code execution"""
        self.multi_mcp = multi_mcp

    def set_step_output(self, step_id, output_dict):
        """Set the output for a specific step in the plan graph"""
        if step_id in self.plan_graph.nodes:
            self.plan_graph.nodes[step_id]['output'] = output_dict
        else:
            print(f"[WARN] Tried to update unknown step ID: {step_id}")

    def _auto_save(self):
        """Auto-save graph to disk"""
        if self.debug_mode:
            return
        try:
            self._save_session()
        except Exception as e:
            print(f"⚠️  Auto-save failed: {e}")

    def _save_session(self):
        """Save the NetworkX graph as session"""
        base_dir = Path("memory/session_summaries_index")
        today = datetime.now()
        date_dir = base_dir / str(today.year) / f"{today.month:02d}" / f"{today.day:02d}"
        date_dir.mkdir(parents=True, exist_ok=True)
        
        session_id = self.plan_graph.graph['session_id']
        session_file = date_dir / f"session_{session_id}.json"
        
        graph_data = nx.node_link_data(self.plan_graph)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, default=str, ensure_ascii=False)

    @classmethod
    def load_session(cls, session_file: Path, debug_mode: bool = False):
        """Load a NetworkX graph session from disk"""
        with open(session_file, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        plan_graph = nx.node_link_graph(graph_data, edges="links")
        
        context = cls.__new__(cls)
        context.plan_graph = plan_graph
        context.debug_mode = debug_mode
        return context

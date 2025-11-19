"""
AI Agent Module: Handle natural language understanding and command generation
"""
import os
import json
from typing import Optional, Dict, List, Tuple
import requests
from config import (
    AI_MODEL, 
    AI_API_KEY, 
    AI_API_URL, 
    AI_API_PROVIDER,
    API_TIMEOUT,
    DEBUG_MODE
)
from rich.console import Console

console = Console()


class AIAgent:
    """AI Agent, responsible for understanding natural language and generating commands"""
    
    def __init__(self):
        if not AI_API_KEY:
            console.print(
                "[yellow]Warning: AI_API_KEY environment variable not set. "
                "Please set the environment variable or create a .env file.[/yellow]"
            )
            self.api_configured = False
        else:
            self.api_configured = True
        
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = """You are a command-line AI assistant. Your task is to understand user's natural language requests and convert them into appropriate Linux/Unix commands.

Rules:
1. Only return executable commands, do not add explanatory text
2. If the user request requires multiple commands, return one command (you can use && to connect)
3. If you cannot determine the user's intent, return "UNKNOWN"
4. If the user is just asking a question and doesn't need to execute a command, return "QUESTION: [your answer]"
5. If the command is dangerous (such as deleting files, modifying permissions, system control, etc.), you must add "NEEDS_APPROVAL: " prefix before the command
6. Safe commands should be returned directly without prefix

Command format:
- Safe commands: Return command string directly
- Dangerous commands: Return "NEEDS_APPROVAL: [command]"
- Do not use code blocks

Examples:
User: "List files in current directory"
You: ls -la

User: "Create a file named test.txt"
You: touch test.txt

User: "What is Python?"
You: QUESTION: Python is a high-level programming language...

User: "Delete test.txt file"
You: NEEDS_APPROVAL: rm test.txt

User: "Delete all .log files"
You: NEEDS_APPROVAL: find . -name "*.log" -type f -delete

User: "Delete file using sudo"
You: NEEDS_APPROVAL: sudo rm file.txt
"""
    
    def _build_headers(self) -> Dict[str, str]:
        """Build API request headers"""
        headers = {
            "Content-Type": "application/json",
        }
        
        # Set authentication header according to API provider
        if AI_API_PROVIDER == 'openai':
            headers["Authorization"] = f"Bearer {AI_API_KEY}"
        else:
            # Custom API, can support multiple authentication methods
            # If API requires Bearer token
            if AI_API_KEY:
                headers["Authorization"] = f"Bearer {AI_API_KEY}"
            # Or use API-Key header
            # headers["X-API-Key"] = AI_API_KEY
        
        return headers
    
    def _build_request_payload(self, messages: List[Dict[str, str]]) -> Dict:
        """Build API request payload"""
        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 500
        }
        return payload
    
    def _parse_response(self, response: requests.Response) -> str:
        """Parse API response"""
        try:
            response.raise_for_status()
            data = response.json()
            
            # Support OpenAI-compatible format
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "").strip()
                return content
            
            # Support other possible response formats
            if "content" in data:
                return data["content"].strip()
            
            if "text" in data:
                return data["text"].strip()
            
            if "response" in data:
                return data["response"].strip()
            
            # If none match, return the entire response (for debugging)
            console.print(f"[yellow]Warning: Unable to parse API response format[/yellow]")
            return json.dumps(data, ensure_ascii=False, indent=2)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"API HTTP Error: {e.response.status_code} - {e.response.text}"
            console.print(f"[red]{error_msg}[/red]")
            return f"Error: {error_msg}"
        except json.JSONDecodeError as e:
            error_msg = f"API response parsing error: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            return f"Error: {error_msg}"
        except Exception as e:
            error_msg = f"API response processing error: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            return f"Error: {error_msg}"
    
    def chat(self, user_input: str) -> Tuple[str, bool]:
        """
        Process user input, return AI-generated command or answer, and whether approval is needed
        
        Args:
            user_input: User's natural language input
            
        Returns:
            Tuple of (command/answer, whether approval is needed)
        """
        if not self.api_configured:
            return ("Error: AI service not configured. Please set AI_API_KEY environment variable.", False)
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            # Build message list
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history[-10:]  # Keep only the last 10 messages to save tokens
            
            # Build request
            headers = self._build_headers()
            payload = self._build_request_payload(messages)
            
            # Send HTTP request
            if DEBUG_MODE:
                console.print(f"[dim]Sending request to: {AI_API_URL}[/dim]")
                console.print(f"[dim]Request body: {json.dumps(payload, ensure_ascii=False, indent=2)}[/dim]")
            
            response = requests.post(
                AI_API_URL,
                headers=headers,
                json=payload,
                timeout=API_TIMEOUT
            )
            
            # Parse response
            ai_response = self._parse_response(response)
            
            # Check if approval is needed
            needs_approval = False
            if ai_response.startswith("NEEDS_APPROVAL:"):
                needs_approval = True
                ai_response = ai_response.replace("NEEDS_APPROVAL:", "").strip()
            
            # Add AI reply to history (save original response)
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            return ai_response, needs_approval
            
        except requests.exceptions.Timeout:
            error_msg = f"API request timeout (exceeded {API_TIMEOUT} seconds)"
            console.print(f"[red]{error_msg}[/red]")
            return (f"Error: {error_msg}", False)
        except requests.exceptions.ConnectionError:
            error_msg = "Unable to connect to API server, please check network connection and API_URL configuration"
            console.print(f"[red]{error_msg}[/red]")
            return (f"Error: {error_msg}", False)
        except Exception as e:
            error_msg = f"AI service error: {str(e)}"
            console.print(f"[red]{error_msg}[/red]")
            if DEBUG_MODE:
                import traceback
                console.print(traceback.format_exc())
            return (f"Error: {error_msg}", False)
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()


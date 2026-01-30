#!/usr/bin/env python3
"""
Command-line AI Agent Main Program
"""
import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv
from prompt_toolkit import prompt as pt_prompt
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles import Style
from ai_agent import AIAgent
from command_executor import CommandExecutor

# Load environment variables
load_dotenv()

console = Console()


def get_user_input(prompt_text: str = "") -> str:
    """
    Get user input with cursor movement support using prompt_toolkit
    
    Args:
        prompt_text: Optional prompt text to display
        
    Returns:
        User input string
    """
    try:
        # Use prompt_toolkit for input with full cursor support
        user_input = pt_prompt(
            prompt_text,
            style=Style.from_dict({
                'prompt': 'bold cyan',
            })
        )
        return user_input.strip() if user_input else ""
    except (KeyboardInterrupt, EOFError):
        return ""


def get_confirmation(prompt_text: str, default: bool = False) -> bool:
    """
    Get user confirmation with cursor movement support.
    Note: default is kept for API compatibility; prompt_toolkit confirm has no default param.

    Args:
        prompt_text: Prompt text to display
        default: Reserved for API compatibility (not used by underlying library)

    Returns:
        True if user confirms, False otherwise
    """
    try:
        # prompt_toolkit confirm() only accepts message and suffix, no default param
        return confirm(message=prompt_text, suffix="")
    except (KeyboardInterrupt, EOFError):
        return False


def print_welcome():
    """Display welcome message"""
    welcome_text = """
# Command-line AI Agent

Welcome to the Command-line AI Agent! You can chat with me in natural language, and I will help you execute corresponding commands.

**Features:**
- 🤖 Natural language interaction
- ⚠️ Sensitive command detection and confirmation
- 📝 Command execution history
- 🔒 Safe command execution

**Usage:**
- Directly input your needs, e.g., "List files in current directory"
- Type `help` to view help
- Type `history` to view command history
- Type `clear` to clear conversation history
- Type `exit` or `quit` to exit program

**Note:** Sensitive commands (such as deletion, permission modification, etc.) require your explicit approval before execution.
"""
    console.print(Panel(Markdown(welcome_text), title="[bold blue]Welcome[/bold blue]", border_style="blue"))
    console.print()


def print_help():
    """Display help information"""
    help_text = """
**Available Commands:**

- `help` - Show this help information
- `history` - Show executed command history
- `clear` - Clear conversation history
- `exit` / `quit` - Exit program

**Usage Examples:**

- "List all files in current directory" → `ls -la`
- "Create a file named test.txt" → `touch test.txt`
- "Show current directory" → `pwd`
- "Find all .py files" → `find . -name "*.py"`
"""
    console.print(Panel(Markdown(help_text), title="[bold green]Help[/bold green]", border_style="green"))


def main():
    """Main function"""
    print_welcome()
    
    # Initialize AI agent and command executor
    ai_agent = AIAgent()
    executor = CommandExecutor()
    
    # Check AI configuration
    if not os.getenv('AI_API_KEY'):
        console.print(
            "[yellow]Note: AI_API_KEY environment variable not detected.[/yellow]\n"
            "[yellow]Please create .env file and add: AI_API_KEY=your_api_key[/yellow]\n"
            "[yellow]Optional configuration: AI_API_URL, AI_MODEL, AI_API_PROVIDER[/yellow]\n"
            "[yellow]Or set environment variables directly.[/yellow]\n"
        )
        console.print("[dim]Continuing (some features may be unavailable)...[/dim]\n")
    
    # Main loop
    while True:
        try:
            # Get user input with cursor support
            console.print("\n[bold cyan]You[/bold cyan]", end="")
            user_input = get_user_input(": ")
            
            if not user_input:
                continue
            
            # Handle special commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            elif user_input.lower() == 'history':
                history = executor.get_command_history()
                if history:
                    console.print("\n[bold]Command Execution History:[/bold]")
                    for i, cmd in enumerate(history, 1):
                        console.print(f"  {i}. {cmd}")
                else:
                    console.print("[dim]No command history[/dim]")
                continue
            
            elif user_input.lower() == 'clear':
                ai_agent.clear_history()
                console.print("[green]Conversation history cleared[/green]")
                continue
            
            # Process natural language input
            console.print(f"[dim]Thinking...[/dim]")
            ai_response, needs_approval = ai_agent.chat(user_input)
            
            # Check if it's a question answer
            if ai_response.startswith("QUESTION:"):
                answer = ai_response.replace("QUESTION:", "").strip()
                console.print(Panel(answer, title="[bold green]Answer[/bold green]", border_style="green"))
                continue
            
            # Check if it's an unknown request
            if ai_response == "UNKNOWN":
                console.print("[yellow]Sorry, I cannot understand your request. Please try a more specific description.[/yellow]")
                continue
            
            # Check if it's an error message
            if ai_response.startswith("Error:"):
                console.print(f"[red]{ai_response}[/red]")
                continue
            
            # Display AI-generated command
            console.print(f"\n[bold]AI Suggested Command:[/bold] [cyan]{ai_response}[/cyan]")
            
            # Determine if approval is needed based on API
            if needs_approval:
                # Command requires approval, ask user
                console.print("\n[red bold]⚠️  This is a dangerous command, continue execution?[/red bold]")
                should_execute = get_confirmation("(y/n): ", default=False)
                
                if should_execute:
                    # Execute command
                    success, stdout, stderr = executor.execute_command(ai_response, auto_approve=True)
                else:
                    console.print("[yellow]Command execution cancelled[/yellow]")
            else:
                # Safe command, execute directly
                console.print("[green]Executing safe command...[/green]")
                success, stdout, stderr = executor.execute_command(ai_response, auto_approve=True)
        
        except KeyboardInterrupt:
            console.print("\n[yellow]\nProgram interrupted, goodbye![/yellow]")
            break
        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error occurred: {str(e)}[/red]")
            if os.getenv('DEBUG', 'false').lower() == 'true':
                import traceback
                console.print(traceback.format_exc())


if __name__ == "__main__":
    main()


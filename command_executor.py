"""
Command Executor Module: Handle command display, sensitive command approval and execution
"""
import subprocess
import re
from typing import Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from config import SENSITIVE_COMMAND_KEYWORDS, DANGEROUS_PATTERNS, COMMAND_TIMEOUT

console = Console()


class CommandExecutor:
    """Command executor, responsible for displaying commands, checking sensitivity and executing commands"""
    
    def __init__(self):
        self.command_history = []
    
    def is_sensitive_command(self, command: str) -> bool:
        """
        Check if command is sensitive
        
        Args:
            command: Command string to check
            
        Returns:
            True if sensitive command, False otherwise
        """
        command_lower = command.lower().strip()
        
        # Check if contains sensitive keywords
        for keyword in SENSITIVE_COMMAND_KEYWORDS:
            if keyword in command_lower:
                return True
        
        # Check if matches dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower):
                return True
        
        return False
    
    def display_command(self, command: str, is_sensitive: bool = False):
        """
        Display command to be executed
        
        Args:
            command: Command to display
            is_sensitive: Whether it is a sensitive command
        """
        if is_sensitive:
            console.print(
                Panel(
                    f"[yellow]⚠️  Sensitive command detected[/yellow]\n\n"
                    f"[bold]Command:[/bold] {command}",
                    title="[red]Sensitive Command[/red]",
                    border_style="red"
                )
            )
        else:
            console.print(
                Panel(
                    f"[bold]Command to execute:[/bold]\n\n{command}",
                    title="[blue]Command Execution[/blue]",
                    border_style="blue"
                )
            )
    
    def execute_command(self, command: str, auto_approve: bool = False) -> Tuple[bool, str, str]:
        """
        Execute command
        
        Args:
            command: Command to execute
            auto_approve: Whether to auto-approve (True to skip local sensitivity check, decided by API)
            
        Returns:
            Tuple of (success flag, stdout, stderr)
        """
        # Display command (if auto_approve=True, already judged by API, skip local detection)
        if auto_approve:
            # Already judged by API, display command directly
            self.display_command(command, is_sensitive=False)
        else:
            # Keep local detection as backup (if API didn't return NEEDS_APPROVAL marker)
            is_sensitive = self.is_sensitive_command(command)
            self.display_command(command, is_sensitive)
            
            # If sensitive command, require user approval
            if is_sensitive:
                approved = Confirm.ask(
                    "[red bold]This is a sensitive command, continue execution?[/red bold]",
                    default=False
                )
                if not approved:
                    console.print("[yellow]Command execution cancelled[/yellow]")
                    return False, "", "User cancelled command execution"
        
        # Record command history
        self.command_history.append(command)
        
        try:
            # Execute command
            console.print(f"[dim]Executing...[/dim]")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT,
                cwd=None  # Use current working directory
            )
            
            # Display results
            if result.returncode == 0:
                console.print("[green]✓ Command executed successfully[/green]")
                if result.stdout:
                    console.print(f"[dim]Output:[/dim]\n{result.stdout}")
            else:
                console.print(f"[red]✗ Command execution failed (exit code: {result.returncode})[/red]")
                if result.stderr:
                    console.print(f"[red]Error:[/red]\n{result.stderr}")
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command execution timeout (exceeded {COMMAND_TIMEOUT} seconds)"
            console.print(f"[red]✗ {error_msg}[/red]")
            return False, "", error_msg
        except Exception as e:
            error_msg = f"Error occurred while executing command: {str(e)}"
            console.print(f"[red]✗ {error_msg}[/red]")
            return False, "", error_msg
    
    def get_command_history(self) -> list:
        """Get command history"""
        return self.command_history.copy()


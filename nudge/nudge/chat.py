#!/usr/bin/env python3
"""
Terminal chat interface for interacting with the Bouncer negotiator.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from bouncer import BouncerAgent

console = Console()

def print_welcome():
    """Print welcome message."""
    welcome_text = Text()
    welcome_text.append("Welcome to Nudge!\n", style="bold cyan")
    welcome_text.append("Chat with The Bouncer - your witty negotiation assistant.\n", style="dim")
    welcome_text.append("Type 'exit' or 'quit' to end the conversation.", style="dim italic")
    
    console.print(Panel(welcome_text, border_style="cyan"))

def print_message(sender: str, message: str, is_user: bool = False):
    """Print a formatted chat message."""
    if is_user:
        console.print(f"[bold green]You:[/bold green] {message}")
    else:
        console.print(f"[bold yellow]Bouncer:[/bold yellow] {message}")

def main():
    """Main chat loop."""
    print_welcome()
    
    try:
        bouncer = BouncerAgent()
        console.print("\n[dim]Bouncer is ready to chat...[/dim]\n")
        
        while True:
            # Get user input
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\n[dim]Exiting...[/dim]")
                break
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print("\n[dim]Bouncer: Thanks for chatting! See you next time.[/dim]")
                break
            
            # Get response from Bouncer
            try:
                response, consent_request = bouncer.chat(user_input)
                print_message("Bouncer", response)
                
                # Handle consent request if present
                if consent_request:
                    console.print(f"[bold yellow]Bouncer:[/bold yellow] {consent_request}")
                    try:
                        consent_response = input("\nYou: ").strip()
                        if consent_response:
                            final_response, _ = bouncer.chat(consent_response)
                            print_message("Bouncer", final_response)
                    except (EOFError, KeyboardInterrupt):
                        console.print("\n[dim]Exiting...[/dim]")
                        break
                
                console.print()  # Add spacing
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                console.print()
    
    except Exception as e:
        console.print(f"[bold red]Failed to initialize Bouncer:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()


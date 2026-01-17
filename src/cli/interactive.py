"""
Interactive mode for answering clarifying questions.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.prompt import Prompt, Confirm


class InteractiveMode:
    """
    Handles interactive clarifying questions.
    """
    
    def __init__(self, use_rich: bool = True):
        """
        Initialize interactive mode.
        
        Args:
            use_rich: Whether to use Rich formatting
        """
        self.use_rich = use_rich
        self.console = Console() if use_rich else None
    
    def get_brief(self) -> str:
        """
        Get the user's brief in interactive mode.
        
        Returns:
            User's brief
        """
        if not self.use_rich:
            print("\nWhat would you like to know or create?")
            return input("> ")
        
        self.console.print("\n[bold cyan]What would you like to know or create?[/bold cyan]")
        return Prompt.ask("Brief")
    
    def ask_clarifying_questions(
        self,
        questions: List[str]
    ) -> Dict[str, str]:
        """
        Ask clarifying questions and collect responses.
        
        Args:
            questions: List of questions to ask
        
        Returns:
            Dictionary mapping questions to answers
        """
        if not questions:
            return {}
        
        if not self.use_rich:
            print("\nI have some clarifying questions:")
            answers = {}
            for i, question in enumerate(questions, 1):
                print(f"\n{i}. {question}")
                answer = input("> ")
                answers[question] = answer
            return answers
        
        self.console.print("\n[bold yellow]I have some clarifying questions:[/bold yellow]\n")
        
        answers = {}
        for i, question in enumerate(questions, 1):
            self.console.print(f"[cyan]{i}. {question}[/cyan]")
            answer = Prompt.ask("Your answer")
            answers[question] = answer
            print()
        
        return answers
    
    def confirm_execution(self, summary: Dict[str, Any]) -> bool:
        """
        Ask user to confirm execution plan.
        
        Args:
            summary: Summary of the execution plan
        
        Returns:
            True if user confirms
        """
        if not self.use_rich:
            print("\nExecution Plan:")
            print(f"  Mode: {summary.get('mode', 'unknown')}")
            print(f"  Agents: {summary.get('agents', 'unknown')}")
            response = input("\nProceed? (y/n) ")
            return response.lower() in ['y', 'yes']
        
        self.console.print("\n[bold]Execution Plan:[/bold]")
        self.console.print(f"  Mode: [cyan]{summary.get('mode', 'unknown')}[/cyan]")
        self.console.print(f"  Agents: [cyan]{summary.get('agents', 'unknown')}[/cyan]")
        
        return Confirm.ask("\nProceed?", default=True)

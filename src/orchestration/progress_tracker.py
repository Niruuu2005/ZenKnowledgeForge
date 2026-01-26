"""
Enhanced Progress Tracking with Time Estimates
"""

import time
from typing import List, Optional
from datetime import datetime, timedelta


class ProgressTracker:
    """
    Track execution progress with detailed timing and estimates.
    """
    
    def __init__(self, total_agents: int, agent_names: List[str]):
        """
        Initialize progress tracker.
        
        Args:
            total_agents: Total number of agents in pipeline
            agent_names: List of agent names in order
        """
        self.total_agents = total_agents
        self.agent_names = agent_names
        self.current_agent_index = 0
        self.start_time = time.time()
        self.agent_start_time = None
        
        # Track timing for each agent
        self.agent_timings = []
        self.current_agent_name = None
    
    def start_agent(self, agent_name: str):
        """Mark agent start"""
        self.current_agent_name = agent_name
        self.agent_start_time = time.time()
        
        # Find index
        if agent_name in self.agent_names:
            self.current_agent_index = self.agent_names.index(agent_name)
        
        self._print_progress("Starting")
    
    def update_status(self, status: str):
        """Update current agent status"""
        self._print_progress(status)
    
    def complete_agent(self, agent_name: str):
        """Mark agent completion"""
        if self.agent_start_time:
            duration = time.time() - self.agent_start_time
            
            self.agent_timings.append({
                'agent': agent_name,
                'duration': duration,
                'timestamp': datetime.now()
            })
            
            self.current_agent_index += 1
            self._print_progress(f"✓ Complete ({duration:.1f}s)")
    
    def _print_progress(self, status: str):
        """Print formatted progress update"""
        # Calculate progress percentage
        progress_pct = (self.current_agent_index / self.total_agents) * 100
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_duration(elapsed)
        
        # Estimate remaining time
        if self.agent_timings:
            avg_time = sum(t['duration'] for t in self.agent_timings) / len(self.agent_timings)
            remaining_agents = self.total_agents - self.current_agent_index
            est_remaining = avg_time * remaining_agents
            remaining_str = self._format_duration(est_remaining)
        else:
            remaining_str = "calculating..."
        
        # Progress bar
        bar_width = 30
        filled = int(bar_width * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        print(f"\n{'='*70}")
        print(f"Progress: [{bar}] {progress_pct:.0f}%")
        print(f"Agent: {self.current_agent_name} ({self.current_agent_index + 1}/{self.total_agents})")
        print(f"Status: {status}")
        print(f"Elapsed: {elapsed_str} | Remaining: ~{remaining_str}")
        print(f"{'='*70}")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds / 3600)
            mins = int((seconds % 3600) / 60)
            return f"{hours}h {mins}m"
    
    def generate_report(self) -> str:
        """
        Generate final timing report.
        
        Returns:
            Formatted timing report
        """
        total_time = time.time() - self.start_time
        
        report = "\n" + "="*70 + "\n"
        report += "EXECUTION TIMING REPORT\n"
        report += "="*70 + "\n\n"
        
        report += "Agent Timings:\n"
        report += "-" * 70 + "\n"
        
        for timing in self.agent_timings:
            duration_str = self._format_duration(timing['duration'])
            report += f"  {timing['agent']:.<50} {duration_str:>10}\n"
        
        report += "-" * 70 + "\n"
        report += f"  {'TOTAL':.<50} {self._format_duration(total_time):>10}\n"
        report += "="*70 + "\n"
        
        # Performance analysis
        if self.agent_timings:
            slowest = max(self.agent_timings, key=lambda x: x['duration'])
            fastest = min(self.agent_timings, key=lambda x: x['duration'])
            avg_time = sum(t['duration'] for t in self.agent_timings) / len(self.agent_timings)
            
            report += "\nPerformance Analysis:\n"
            report += f"  Slowest agent: {slowest['agent']} ({self._format_duration(slowest['duration'])})\n"
            report += f"  Fastest agent: {fastest['agent']} ({self._format_duration(fastest['duration'])})\n"
            report += f"  Average time per agent: {self._format_duration(avg_time)}\n"
        
        return report

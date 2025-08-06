"""Main planner module for the Endoscope AI project."""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import date

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import load_config
from core.models import Config, SchedulerStrategy
from schedulers.base import BaseScheduler
from core.constraints import validate_schedule_comprehensive
from output.console import print_schedule_summary, print_metrics_summary
from output.reports import generate_schedule_report
from output.tables import generate_monthly_table, generate_simple_monthly_table
from output.formatters.tables import format_schedule_table, format_deadline_table
from output.plots import plot_schedule, plot_utilization_chart, plot_deadline_compliance


def generate_and_save_output(schedule: Dict[str, date], config: Config, output_dir: str = "test_output") -> None:
    """
    Generate and save all output files for a schedule.
    
    Parameters
    ----------
    schedule : Dict[str, date]
        Mapping of submission_id to start_date
    config : Config
        Configuration object
    output_dir : str
        Directory to save output files
    """
    import os
    from datetime import datetime
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate reports
    report = generate_schedule_report(schedule, config)
    
    # Save report to JSON
    report_path = os.path.join(output_dir, f"schedule_report_{timestamp}.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Generate and save tables
    try:
        schedule_table_data = format_schedule_table(schedule, config)
        table_path = os.path.join(output_dir, f"schedule_table_{timestamp}.txt")
        with open(table_path, 'w', encoding='utf-8') as f:
            for row in schedule_table_data:
                f.write(" | ".join(f"{k}: {v}" for k, v in row.items()) + "\n")
    except Exception as e:
        print(f"Warning: Could not generate schedule table: {e}")
    
    try:
        deadline_table_data = format_deadline_table(schedule, config)
        deadline_path = os.path.join(output_dir, f"deadline_table_{timestamp}.txt")
        with open(deadline_path, 'w', encoding='utf-8') as f:
            for row in deadline_table_data:
                f.write(" | ".join(f"{k}: {v}" for k, v in row.items()) + "\n")
    except Exception as e:
        print(f"Warning: Could not generate deadline table: {e}")
    
    # Generate and save plots
    try:
        plot_path = os.path.join(output_dir, f"schedule_gantt_{timestamp}.png")
        plot_schedule(schedule, config.submissions, save_path=plot_path)
    except Exception as e:
        print(f"Warning: Could not generate schedule plot: {e}")
    
    try:
        util_path = os.path.join(output_dir, f"utilization_{timestamp}.png")
        plot_utilization_chart(schedule, config, save_path=util_path)
    except Exception as e:
        print(f"Warning: Could not generate utilization plot: {e}")
    
    try:
        deadline_plot_path = os.path.join(output_dir, f"deadline_compliance_{timestamp}.png")
        plot_deadline_compliance(schedule, config, save_path=deadline_plot_path)
    except Exception as e:
        print(f"Warning: Could not generate deadline compliance plot: {e}")
    
    print(f"Output files saved to: {output_dir}")
    print(f"Report: {report_path}")


class Planner:
    """Simple facade for the paper planning system."""
    
    def __init__(self, config_path: str):
        try:
            # Load the raw config for backward compatibility
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

            # Add missing config values
            self.config.setdefault("default_paper_lead_time_months", 3)
            self.config.setdefault("max_concurrent_papers", 2)

            # Load the new Config structure
            self.cfg: Config = load_config(config_path)

            # Load mods and papers for backward compatibility
            config_dir = os.path.dirname(os.path.abspath(config_path))
            
            # Load mods
            mods_path = os.path.join(config_dir, self.config["data_files"]["mods"])
            if not os.path.exists(mods_path):
                raise FileNotFoundError(f"Mods file not found: {mods_path}")
            with open(mods_path, "r", encoding="utf-8") as f:
                self.mods = json.load(f)
            
            # Load papers
            papers_path = os.path.join(config_dir, self.config["data_files"]["papers"])
            if not os.path.exists(papers_path):
                raise FileNotFoundError(f"Papers file not found: {papers_path}")
            with open(papers_path, "r", encoding="utf-8") as f:
                self.papers = json.load(f)

            # Load conferences for backward compatibility
            conferences_path = os.path.join(config_dir, self.config["data_files"]["conferences"])
            if not os.path.exists(conferences_path):
                raise FileNotFoundError(f"Conferences file not found: {conferences_path}")
            with open(conferences_path, "r", encoding="utf-8") as f:
                self.config["conferences"] = json.load(f)

            # Create papers dict for easy access by ID
            self.papers_dict = {p["id"]: p for p in self.papers}
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Configuration file error: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize planner: {e}")

    def validate_config(self):
        """Validate the configuration."""
        pass  # no-op for backward compatibility

    def schedule(self, strategy: SchedulerStrategy = SchedulerStrategy.GREEDY) -> tuple[Dict[Any, Any], Dict[Any, Any]]:
        """Generate a schedule using the specified strategy."""
        try:
            # Create scheduler using the base scheduler
            scheduler = BaseScheduler(self.cfg)

            # Generate schedule
            full_schedule = scheduler.schedule()
            
            if not full_schedule:
                raise RuntimeError("Failed to generate schedule - no submissions scheduled")
            
            # Convert to backward-compatible format
            mod_sched, paper_sched = {}, {}
            
            # Find the earliest date to use as base for month offsets
            all_dates = list(full_schedule.values())
            if all_dates:
                base_date = min(all_dates)
            else:
                base_date = date(2025, 1, 1)  # fallback

            for sid, dt in full_schedule.items():
                # Convert date to month offset from base date
                month_offset = (dt.year - base_date.year) * 12 + (dt.month - base_date.month)
                
                if sid.endswith("-wrk"):
                    # mod##-wrk → integer key
                    mod_id = sid.replace("-wrk", "")
                    mod_sched[int(mod_id)] = month_offset
                elif sid.endswith("-pap"):
                    # pid-pap → pid key
                    paper_sched[sid.replace("-pap", "")] = month_offset

            return mod_sched, paper_sched
            
        except ValueError as e:
            raise ValueError(f"Schedule generation failed: {e}")
        except RuntimeError as e:
            raise RuntimeError(f"Schedule generation failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during schedule generation: {e}")

    def greedy_schedule(self) -> tuple[Dict[Any, int], Dict[Any, int]]:
        """Legacy method for backward compatibility."""
        return self.schedule(SchedulerStrategy.GREEDY)



    def generate_monthly_table(self) -> List[Dict[str, Any]]:
        """Generate monthly table for backward compatibility."""
        return generate_simple_monthly_table(self.cfg)

import json
import os
from typing import Dict, Any, List
from datetime import date
from core.config import load_config
from core.types import Config
from schedulers.greedy import GreedyScheduler
from schedulers.stochastic import StochasticGreedyScheduler
from schedulers.lookahead import LookaheadGreedyScheduler
from schedulers.backtracking import BacktrackingGreedyScheduler
from output.tables import generate_simple_monthly_table


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

    def schedule(self, strategy: str = "greedy") -> tuple[Dict[Any, Any], Dict[Any, Any]]:
        """Generate a schedule using the specified strategy."""
        try:
            # Create scheduler based on strategy
            if strategy == "greedy":
                scheduler = GreedyScheduler(self.cfg)
            elif strategy == "stochastic":
                scheduler = StochasticGreedyScheduler(self.cfg)
            elif strategy == "lookahead":
                scheduler = LookaheadGreedyScheduler(self.cfg)
            elif strategy == "backtracking":
                scheduler = BacktrackingGreedyScheduler(self.cfg)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

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
        return self.schedule("greedy")

    def concurrent_schedule(self) -> tuple[Dict[Any, int], Dict[Any, int]]:
        """Legacy method for backward compatibility."""
        return self.schedule("greedy")



    def generate_monthly_table(self) -> List[Dict[str, Any]]:
        """Generate monthly table for backward compatibility."""
        return generate_simple_monthly_table(self.config)

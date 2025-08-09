# Paper Planner - Quick Start Guide

A comprehensive quick start guide for the Paper Planner academic scheduling system.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Installation

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd Paper-Planner
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 📊 Web Dashboard (Recommended)

The web dashboard provides an interactive interface with real-time schedule generation and visualization.

### Start the Dashboard
```bash
python run_web_charts.py --mode dashboard
```

**Access:** http://127.0.0.1:8050

### Features
- **Interactive Gantt Charts**: Zoom, pan, and hover for details
- **Strategy Selection**: Dropdown to choose scheduling algorithms
- **Real-time Updates**: Live chart updates when strategy changes
- **Export Options**: Save charts as HTML, PNG, or SVG
- **Responsive Design**: Works on desktop and mobile

### Dashboard Modes
```bash
# Full dashboard with all features
python run_web_charts.py --mode dashboard

# Timeline-only view (simplified)
python run_web_charts.py --mode timeline

# Capture screenshots of all strategies
python run_web_charts.py --mode dashboard --capture
```

## 🖥️ Command Line Interface

For script-based schedule generation and analysis.

### Basic Usage
```bash
# Generate schedule with greedy strategy
python generate_schedule.py --strategy greedy

# Compare all available strategies
python generate_schedule.py --compare

# List all available strategies
python generate_schedule.py --list-strategies
```

### Available Strategies
- **Greedy**: Fast, basic scheduling (default)
- **Stochastic**: Greedy with random perturbations
- **Lookahead**: Considers future implications
- **Backtracking**: Explores multiple paths
- **Random**: Random valid schedules
- **Heuristic**: Rule-based optimization
- **Optimal**: Mathematical optimization (when feasible)

### Advanced CLI Options
```bash
# Use custom configuration
python generate_schedule.py --strategy greedy --config custom_config.json

# Save comparison results
python generate_schedule.py --compare --output comparison.json

# Quiet mode (suppress verbose output)
python generate_schedule.py --strategy greedy --quiet
```

## ⚙️ Configuration

The system uses `config.json` in the root directory for all settings.

### Key Configuration Options
```json
{
  "max_concurrent_submissions": 2,
  "min_paper_lead_time_days": 60,
  "priority_weights": {
    "engineering_paper": 2.0,
    "medical_paper": 1.0
  },
  "scheduling_options": {
    "enable_working_days_only": true,
    "enable_blackout_periods": true
  }
}
```

### Data Files
- `data/conferences.json`: Conference definitions and deadlines
- `data/papers.json`: Full paper submissions
- `data/mods.json`: Modification/abstract submissions
- `data/blackout.json`: Blackout dates

## 📈 Understanding the Output

### Schedule Quality Metrics
- **Overall Score (0-100)**: Combined quality and efficiency
- **Quality Score**: Deadline compliance, dependencies, constraints
- **Efficiency Score**: Resource utilization, timeline efficiency
- **Penalty Breakdown**: Detailed violation costs

### Visualization Types
1. **Interactive Gantt Charts**: Timeline with submission details
2. **Resource Utilization**: Daily workload distribution
3. **Metrics Dashboard**: Real-time performance indicators
4. **Schedule Tables**: Detailed tabular views

## 🔧 Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'dash'**
```bash
pip install -r requirements.txt
```

**Port Already in Use**
```bash
# Kill process using port 8050
netstat -ano | findstr :8050
taskkill /PID <PID> /F
```

**PowerShell Execution Policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Virtual Environment Not Activated**
```bash
# Windows
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

### Debug Mode
```bash
# Enable debug logging
python run_web_charts.py --mode dashboard --debug
```

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Run all tests
pytest -q

# Run specific test categories
pytest tests/schedulers/ -v
pytest tests/core/ -v
```

## 📋 Business Rules Overview

The system enforces comprehensive academic scheduling constraints:

### Core Constraints
- **Deadline Compliance**: All submissions must meet conference deadlines
- **Dependencies**: Papers may require corresponding abstracts
- **Resource Limits**: Maximum concurrent submissions (default: 2)
- **Conference Compatibility**: Submission preferences must match conference opportunities

### Submission Types & Preferences
- **Mods & Ed Papers**: Both are papers in the data model with unified handling
- **Conference Preference**: Use `candidate_kind` to specify preferred submission type (paper/abstract/poster)
- **Conference Selection**: Use `candidate_conferences` to specify target conferences (empty = any appropriate)
- **Smart Matching**: System respects preferences while following conference rules

### Advanced Features
- **Working Days Only**: Optional business day restriction
- **Blackout Periods**: Federal holidays and custom unavailable dates
- **Priority Weighting**: Engineering papers weighted higher than medical
- **Conference Response Time**: Buffer time for conference processing

## 🎯 Quick Examples

### Generate and View Schedule
```bash
# 1. Start the web dashboard
python run_web_charts.py --mode dashboard

# 2. Open browser to http://127.0.0.1:8050

# 3. Select strategy from dropdown and view results
```

### Compare Strategies
```bash
# Generate comparison report
python generate_schedule.py --compare --output strategy_comparison.json

# View results in browser
python run_web_charts.py --mode dashboard
```

### Custom Configuration
```bash
# Edit config.json to adjust settings
# Then run with custom config
python generate_schedule.py --strategy greedy --config custom_config.json
```

## 📊 Performance

- **Schedule Generation**: < 1 second for 37 submissions
- **Web Dashboard**: Real-time updates, responsive design
- **Memory Usage**: < 100MB for full system
- **Validation**: All constraints checked in < 100ms

## 🔗 Key Files

### Main Entry Points
- `run_web_charts.py`: Web dashboard and timeline interface
- `generate_schedule.py`: Command-line schedule generation
- `config.json`: Main configuration file

### Core Components
- `src/planner.py`: Main planning interface
- `src/schedulers/`: Scheduling algorithms
- `src/validation/`: Constraint validation
- `app/main.py`: Web application

### Data Files
- `data/conferences.json`: Conference definitions
- `data/papers.json`: Paper submissions
- `data/mods.json`: Abstract/modification submissions

## 🆘 Getting Help

### Logs
- Check `web_charts_server.log` for web application errors
- Console output shows detailed error messages

### Debug Information
- Browser console (F12) for client-side issues
- Server logs for backend problems
- Test suite for validation issues

### Common Commands
```bash
# Check if all dependencies are installed
pip list

# Verify Python path
python -c "import sys; print(sys.path)"

# Test import of main modules
python -c "from src.planner import Planner; print('OK')"
```

## 🚀 Next Steps

1. **Explore the Web Dashboard**: Start with `python run_web_charts.py --mode dashboard`
2. **Try Different Strategies**: Use the dropdown to compare algorithms
3. **Customize Configuration**: Edit `config.json` for your specific needs
4. **Add Your Data**: Update data files with your conferences and submissions
5. **Run Tests**: Ensure everything works with `pytest -q`

---

**Need more help?** Check the main [README.md](README.md) for comprehensive documentation, advanced features, and detailed explanations of all business rules and constraints.

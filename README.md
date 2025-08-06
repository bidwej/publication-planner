# Endoscope AI Paper Scheduler

A comprehensive paper scheduling system for the Endoscope AI project, featuring interactive Gantt charts and web-based visualization.

## 🎯 Overview

This system schedules **20 research papers** and **17 engineering mods** across **14 conferences** with complex constraints including:
- Dependencies between papers and mods
- Conference deadline compliance
- Resource utilization limits
- Priority-based scheduling

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Command Line Usage
```bash
# Generate schedule with greedy strategy
python generate_schedule.py greedy

# Interactive mode
python generate_schedule.py
```

### Web Interface (Interactive)
```bash
# Start the web dashboard
python src/web_app.py

# Open browser to: http://127.0.0.1:8050
```

## 📊 Interactive Features

### Plotly-Based Visualization (Free & Open Source)

**✅ Interactive Gantt Charts:**
- Zoom and pan through schedules
- Hover for detailed information
- Color-coded by priority and type
- Export to HTML/PNG/SVG

**✅ Real-time Analytics:**
- Resource utilization tracking
- Deadline compliance analysis
- Strategy comparison

**✅ Web Dashboard:**
- Dropdown strategy selection
- Live chart updates
- Responsive design

## 🏗️ Architecture

```
src/
├── core/           # Data models and configuration
├── schedulers/     # Multiple scheduling algorithms
├── scoring/        # Quality and efficiency metrics
├── output/         # Visualization and reporting
│   ├── plots.py    # Matplotlib (static)
│   └── plots_plotly.py  # Plotly (interactive)
└── web_app.py      # Dash web interface
```

## 📈 Scheduling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **Greedy** | Fast, priority-based | Quick scheduling |
| **Optimal** | MILP optimization | Best quality |
| **Stochastic** | Randomized greedy | Exploration |
| **Random** | Random assignment | Baseline testing |
| **Heuristic** | Rule-based | Custom logic |

## 🎨 Visualization Options

### 1. Plotly (Recommended - Free)
```python
from output.plots_plotly import create_interactive_gantt

fig = create_interactive_gantt(schedule, submissions, config)
fig.show()  # Opens in browser
fig.write_html("schedule.html")  # Save for sharing
```

**Features:**
- ✅ **Interactive**: Zoom, pan, hover
- ✅ **Web-ready**: HTML files work anywhere
- ✅ **Free**: MIT license
- ✅ **Easy integration**: Works with your existing code

### 2. Matplotlib (Static)
```python
from output.plots import plot_schedule

plot_schedule(schedule, submissions, save_path="schedule.png")
```

**Features:**
- ✅ **Fast**: Quick generation
- ✅ **Static**: Good for reports
- ✅ **Lightweight**: No web dependencies

### 3. Web Dashboard (Dash)
```bash
python src/web_app.py
```

**Features:**
- ✅ **Interactive web interface**
- ✅ **Real-time updates**
- ✅ **Strategy comparison**
- ✅ **Export capabilities**

## 📋 Data Structure

### Papers (20 submissions)
```json
{
  "id": "J1-pap",
  "title": "User Experience Analysis",
  "kind": "paper",
  "conference_id": "ICML2025",
  "depends_on": ["J1-abs"],
  "draft_window_months": 3
}
```

### Conferences (14 venues)
```json
{
  "id": "ICML2025",
  "name": "ICML 2025",
  "conf_type": "ENGINEERING",
  "deadlines": {
    "abstract": "2025-01-15",
    "paper": "2025-02-15"
  }
}
```

## 🔧 Configuration

### Core Settings (`data/config.json`)
```json
{
  "max_concurrent_submissions": 2,
  "min_paper_lead_time_days": 60,
  "priority_weights": {
    "engineering_paper": 2.0,
    "medical_paper": 1.0
  }
}
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/schedulers/ -v
pytest tests/core/ -v
pytest tests/output/ -v
```

## 📊 Output Examples

### Interactive Gantt Chart
- **Zoom**: Click and drag to zoom into time periods
- **Pan**: Drag to move around the timeline
- **Hover**: See paper details, deadlines, conferences
- **Export**: Save as HTML for sharing

### Resource Utilization
- **Real-time**: Shows daily resource usage
- **Capacity**: Red line indicates limits
- **Trends**: Visualize workload patterns

### Deadline Compliance
- **Pie Chart**: On-time vs late submissions
- **Bar Chart**: Days late for each submission
- **Analysis**: Identify problematic schedules

## 🆚 Framework Comparison

| Framework | License | Cost | Interactivity | Learning Curve | Recommendation |
|-----------|---------|------|---------------|----------------|----------------|
| **Plotly** | MIT | Free | ✅ Excellent | ⭐⭐ Easy | **Best Choice** |
| **Dash** | MIT | Free | ✅ Full Web | ⭐⭐ Easy | **Perfect for Web** |
| **ApexCharts** | MIT | Free | ✅ Good | ⭐⭐⭐ Medium | Good Alternative |
| **DHTMLX Gantt** | GPL v2 | Free | ✅ Best | ⭐⭐⭐ Hard | Overkill |
| **Bryntum Gantt** | Commercial | $999 | ✅ Excellent | ⭐⭐ Easy | Too Expensive |

## 🚀 Deployment

### Local Development
```bash
python src/web_app.py
```

### Production Deployment
```bash
# Using Gunicorn
pip install gunicorn
gunicorn src.web_app:app.server --bind 0.0.0.0:8050

# Using Docker
docker build -t scheduler .
docker run -p 8050:8050 scheduler
```

## 📈 Performance

- **Schedule Generation**: < 1 second for 37 submissions
- **Interactive Charts**: Real-time updates
- **Web Dashboard**: Responsive, mobile-friendly
- **Memory Usage**: < 100MB for full system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Plotly**: Free interactive visualization
- **Dash**: Free web framework for data apps
- **MIT License**: Enables commercial use and modification

---

**Built with ❤️ using free and open-source tools**
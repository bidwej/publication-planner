# Paper Planner - TODO List

A comprehensive list of planned features and improvements for the Paper Planner academic scheduling system.

## 🚧 High Priority - Core Missing Features

### 1. **MILP Optimization Implementation** 
**Status**: Partially implemented but not functional
**Priority**: 🔴 CRITICAL

**Current State**:
- `src/schedulers/optimal.py` exists but has significant issues
- Uses PuLP library but implementation is incomplete
- Falls back to greedy scheduler when MILP fails
- Resource constraint modeling is overly complex and likely incorrect

**Issues Found**:
```python
# In src/schedulers/optimal.py lines 200-220
# Resource constraint modeling is overly complex and likely incorrect
for day in range(horizon_days + 1):
    day_active_vars = []
    for submission_id in self.submissions:
        var_name = f"active_{submission_id}_day_{day}"
        if var_name in resource_vars:
            day_active_vars.append(resource_vars[var_name])
    
    if day_active_vars:
        prob += pulp.lpSum(day_active_vars) <= self.max_concurrent
```

**Required Work**:
- [ ] **Fix Resource Constraint Modeling**: Simplify binary variable approach
- [ ] **Implement Proper MILP Formulation**: Use standard scheduling MILP patterns
- [ ] **Add OR-Tools Alternative**: Implement Google OR-Tools as alternative to PuLP
- [ ] **Optimization Objectives**: Implement minimize_makespan, minimize_penalties, minimize_total_time
- [ ] **Constraint Validation**: Ensure all business rules are properly modeled
- [ ] **Performance Optimization**: Add time limits and solver configuration
- [ ] **Fallback Mechanism**: Improve fallback to greedy when MILP fails

**Implementation Plan**:
```python
# Proposed MILP structure
class OptimalScheduler(BaseScheduler):
    def _setup_milp_model(self):
        # 1. Decision variables: start_time[submission_id]
        # 2. Binary variables: active[submission_id][day]
        # 3. Constraints: dependencies, deadlines, resources, working days
        # 4. Objective: minimize makespan/penalties/total_time
        pass
```

### 2. **Quarterly Re-solve System**
**Status**: Not implemented
**Priority**: 🔴 CRITICAL

**Description**: Automated re-scheduling as real-world dates slip and progress is made.

**Required Components**:
- [ ] **Progress Tracking**: Track actual vs. planned completion dates
- [ ] **Dynamic Rescheduling**: Re-schedule remaining submissions based on actual progress
- [ ] **Slip Detection**: Detect when submissions are behind schedule
- [ ] **Cascade Rescheduling**: Handle dependency chain updates
- [ ] **Notification System**: Alert when rescheduling is needed
- [ ] **Version Control**: Track schedule versions and changes

**Implementation Plan**:
```python
class QuarterlyResolver:
    def __init__(self, original_schedule, actual_progress):
        self.original_schedule = original_schedule
        self.actual_progress = actual_progress
    
    def detect_slips(self):
        """Detect submissions that are behind schedule"""
        pass
    
    def reschedule_remaining(self):
        """Re-schedule remaining submissions"""
        pass
    
    def update_dependencies(self):
        """Update dependency chains based on actual progress"""
        pass
```

### 3. **Advanced Penalty Terms**
**Status**: Basic penalties implemented, advanced terms missing
**Priority**: 🟡 HIGH

**Current Penalties** (from `config.json`):
```json
{
  "penalty_costs": {
    "default_mod_penalty_per_day": 1000.0,
    "default_paper_penalty_per_day": 500.0,
    "default_monthly_slip_penalty": 1000.0,
    "default_full_year_deferral_penalty": 5000.0,
    "missed_abstract_penalty": 3000.0,
    "resource_violation_penalty": 200.0
  }
}
```

**Missing Advanced Penalties**:
- [ ] **SlackCost Penalties**: More sophisticated slack cost calculations
  - Monthly slip penalties with compound interest
  - Full-year deferral penalties with exponential scaling
  - Missed opportunity costs for abstract-only windows
- [ ] **VenuePenalty**: Conference-specific penalties
  - Prestige-based penalties (top-tier vs. lower-tier conferences)
  - Audience mismatch penalties
  - Publication impact penalties
- [ ] **FDA Delay Terms**: Special penalties for FDA-related delays
  - Regulatory review delays
  - Clinical trial delays
  - Approval process delays
- [ ] **Risk-Based Penalties**: Penalties based on submission risk
  - High-risk vs. low-risk submissions
  - Novelty factor penalties
  - Technical complexity penalties

**Implementation Plan**:
```python
class AdvancedPenaltyCalculator:
    def calculate_slack_cost(self, submission, actual_start, planned_start):
        """Calculate sophisticated slack cost with compound interest"""
        pass
    
    def calculate_venue_penalty(self, submission, conference):
        """Calculate venue-specific penalties"""
        pass
    
    def calculate_fda_penalty(self, submission):
        """Calculate FDA-related delay penalties"""
        pass
```

### 4. **CSV Export Functionality**
**Status**: Partially implemented
**Priority**: 🟡 HIGH

**Current State**:
- JSON export exists in `src/output/`
- Basic table generation in `src/output/tables.py`
- No direct CSV export functionality

**Missing Features**:
- [ ] **Direct CSV Export**: Export schedules to CSV format
- [ ] **Multiple CSV Formats**: Different CSV layouts for different use cases
- [ ] **Schedule CSV**: Export schedule with dates and assignments
- [ ] **Metrics CSV**: Export performance metrics and scores
- [ ] **Violations CSV**: Export constraint violations and penalties
- [ ] **Comparison CSV**: Export strategy comparison results

**Implementation Plan**:
```python
# In src/output/generators/
class CSVExporter:
    def export_schedule_csv(self, schedule, config, filename):
        """Export schedule to CSV format"""
        pass
    
    def export_metrics_csv(self, metrics, filename):
        """Export metrics to CSV format"""
        pass
    
    def export_comparison_csv(self, comparison_results, filename):
        """Export strategy comparison to CSV"""
        pass
```

## 🟡 Medium Priority - Enhancement Features

### 5. **Real-time Monitoring System**
**Status**: Not implemented
**Priority**: 🟡 MEDIUM

**Description**: Live tracking of actual vs. planned schedules with automated adjustments.

**Required Components**:
- [ ] **Progress Tracking**: Track actual completion dates
- [ ] **Deviation Detection**: Detect when actual dates differ from planned
- [ ] **Dashboard Integration**: Real-time updates in web dashboard
- [ ] **Historical Tracking**: Track schedule changes over time

### 6. **Advanced Analytics Features**
**Status**: Basic analytics implemented, advanced features missing
**Priority**: 🟡 MEDIUM

**Current State**:
- Basic efficiency and quality scoring
- Resource utilization metrics
- Constraint violation tracking

**Missing Features**:
- [ ] **Dependency Graph Analysis**: Use NetworkX for complex dependency analysis
- [ ] **Performance Prediction**: Predict schedule success probability
- [ ] **Optimization Recommendations**: ML-based suggestions for improvements

**Implementation Plan**:
```python
# Uncomment in requirements.txt
# networkx>=3.1  # For dependency graph analysis

class AdvancedAnalytics:
    def analyze_dependency_graph(self, submissions):
        """Analyze dependency graph for bottlenecks"""
        pass
    
    def recommend_optimizations(self, schedule, config):
        """Recommend schedule optimizations"""
        pass
```

### 7. **Enhanced Configuration Management**
**Status**: Basic configuration implemented
**Priority**: 🟡 MEDIUM

**Missing Features**:
- [ ] **Dynamic Configuration Updates**: Update config without restart
- [ ] **Configuration Validation**: Enhanced validation with detailed error messages
- [ ] **Configuration Templates**: Pre-built templates for different scenarios
- [ ] **Configuration Versioning**: Track configuration changes
- [ ] **Environment-Specific Configs**: Different configs for dev/prod

### 8. **Performance Optimizations**
**Status**: Basic performance implemented
**Priority**: 🟡 MEDIUM

**Current Performance**:
- Schedule generation: < 1 second for 37 submissions
- Memory usage: < 100MB for full system
- Validation: All constraints checked in < 100ms

**Optimization Targets**:
- [ ] **Faster MILP Solving**: Optimize for large datasets
- [ ] **Efficient Constraint Validation**: Optimize for complex scenarios
- [ ] **Memory Optimization**: Reduce memory usage for large datasets
- [ ] **Parallel Processing**: Use multiprocessing for strategy comparison
- [ ] **Caching**: Cache validation results and intermediate calculations

## 🟢 Low Priority - Nice-to-Have Features

### 9. **Advanced Export Capabilities**
**Status**: Basic export implemented
**Priority**: 🟢 LOW

**Missing Features**:

- [ ] **Excel Export**: Export to Excel with multiple sheets
- [ ] **Calendar Integration**: Export to calendar formats (iCal, Google Calendar)
- [ ] **Email Integration**: Send schedules via email
- [ ] **API Endpoints**: REST API for external integrations

### 10. **Advanced Web Dashboard Features**
**Status**: Basic dashboard implemented
**Priority**: 🟢 LOW

**Missing Features**:
- [ ] **Real-time Collaboration**: Multiple users can view/edit schedules
- [ ] **Schedule Templates**: Pre-built schedule templates
- [ ] **Advanced Filtering**: Filter by submission type, conference, etc.
- [ ] **Drag-and-Drop Rescheduling**: Visual schedule editing
- [ ] **Mobile Optimization**: Better mobile experience

### 11. **Advanced Testing Features**
**Status**: Basic testing implemented
**Priority**: 🟢 LOW

**Missing Features**:
- [ ] **Performance Testing**: Load testing for large datasets
- [ ] **Stress Testing**: Test with extreme constraint scenarios
- [ ] **Integration Testing**: End-to-end workflow testing
- [ ] **User Acceptance Testing**: Real-world scenario testing

## 🔧 Technical Debt & Improvements

### 12. **Code Quality Improvements**
**Status**: Good code quality, some areas for improvement
**Priority**: 🟡 MEDIUM

**Areas for Improvement**:
- [ ] **Type Hints**: Complete type hint coverage
- [ ] **Documentation**: Improve docstring coverage
- [ ] **Error Handling**: More robust error handling
- [ ] **Logging**: Comprehensive logging system
- [ ] **Code Coverage**: Increase test coverage to 95%+

### 13. **Architecture Improvements**
**Status**: Good architecture, some areas for improvement
**Priority**: 🟡 MEDIUM

**Areas for Improvement**:
- [ ] **Dependency Injection**: Implement proper DI container
- [ ] **Event System**: Implement event-driven architecture
- [ ] **Plugin System**: Allow custom schedulers and validators
- [ ] **Configuration Management**: More flexible configuration system

## 📊 Implementation Timeline

### Phase 1 (Critical - 2-3 weeks)
1. **Fix MILP Optimization** - Make optimal scheduler functional
2. **Implement CSV Export** - Complete export functionality
3. **Add Advanced Penalty Terms** - Implement sophisticated penalty calculations

### Phase 2 (High Priority - 4-6 weeks)
1. **Quarterly Re-solve System** - Implement dynamic rescheduling
2. **Real-time Monitoring** - Add progress tracking and alerts
3. **Advanced Analytics** - Integrate ML and graph analysis

### Phase 3 (Medium Priority - 6-8 weeks)
1. **Performance Optimizations** - Optimize for large datasets
2. **Enhanced Configuration** - Improve configuration management
3. **Advanced Testing** - Comprehensive testing suite

### Phase 4 (Low Priority - 8-12 weeks)
1. **Advanced Export Features** - Excel, calendar integration
2. **Advanced Dashboard Features** - Collaboration, templates, mobile
3. **Architecture Improvements** - DI, events, plugins

## 🎯 Success Metrics

### Technical Metrics
- **MILP Success Rate**: > 80% of problems solved optimally
- **Performance**: < 5 seconds for 100+ submissions
- **Memory Usage**: < 200MB for large datasets
- **Test Coverage**: > 95% code coverage

### User Experience Metrics
- **Schedule Quality**: Average quality score > 85/100
- **Constraint Compliance**: < 5% constraint violations
- **User Satisfaction**: > 4.5/5 rating from users

## 🚀 Getting Started

### For Developers
1. **Start with MILP Optimization**: Fix the optimal scheduler first
2. **Add CSV Export**: Implement basic CSV export functionality
3. **Implement Advanced Penalties**: Add sophisticated penalty calculations
4. **Build Quarterly Re-solve**: Implement dynamic rescheduling

### For Contributors
1. **Pick a Priority Item**: Choose from the high-priority list
2. **Create Feature Branch**: Work on isolated feature branches
3. **Add Tests**: Ensure comprehensive test coverage
4. **Update Documentation**: Keep documentation current

## 📝 Notes

- **Dependencies**: Some features require additional libraries (scikit-learn, NetworkX)
- **Performance**: Consider performance impact of new features
- **Backward Compatibility**: Maintain compatibility with existing configurations
- **Testing**: All new features must have comprehensive tests
- **Documentation**: Update README and quickstart guide as features are implemented

---

**Last Updated**: Current date
**Next Review**: Monthly review of progress and priority adjustments

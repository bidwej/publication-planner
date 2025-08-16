# Paper Planner Demo Data

This directory contains simplified demo data designed to test the core Paper Planner functionality with a focused dependency chain.

## 🎯 **Demo Objectives**

The demo data is designed to test:

1. **Concurrency Limits** - Max 2 concurrent submissions per author
2. **Dependency Chains** - Paper-to-paper dependencies
3. **Abstract→Paper Workflows** - Conferences requiring abstracts first
4. **Resource Conflicts** - Limited experts and GPU clusters

## 📁 **File Structure**

```
demo/
├── README.md
└── data/
    ├── config.json          # Demo configuration with strict limits
    ├── conferences.json     # 3 conferences with various submission types
    ├── mod_papers.json      # 2 engineering work items (mods)
    ├── ed_papers.json       # 2 research papers with dependency chain
    └── blackout.json        # 3 blackout dates (holidays)
```

## 🔧 **Configuration Features**

### **Strict Concurrency Control**
- `max_concurrent_submissions: 2` - Tight limit to test violations
- `strict_concurrency_enforcement: true` - Enforce limits strictly
- `enable_resource_balancing: true` - Balance resource usage

### **Resource Constraints**
- Limited experts (CV_expert, anatomy_expert, AI_expert)
- Limited GPU clusters
- Team-specific resource requirements

## 📊 **Data Complexity**

### **Conferences (3 total)**
- **ICML_DEMO**: Abstract + Paper (Jan 31 deadline)
- **MICCAI_DEMO**: Abstract + Paper (Feb 28 deadline)  
- **NeurIPS_DEMO**: Paper Only (Feb 15 deadline)

### **Mods (2 engineering work items)**
- **mod_1**: Computer Vision endoscopy (ICML_DEMO)
- **mod_2**: Middle Turbinate analysis (MICCAI_DEMO)

### **Papers (2 research papers)**
- **J1**: CV endoscopy review (abstract+paper, depends on mod_1)
- **J2**: AI endoscopy support (paper only, depends on J1)

## 🔗 **Dependency Chain**

### **Simple Dependencies**
- J1 depends on mod_1
- J2 depends on J1 (paper dependency!)

### **Test Scenario**
1. **mod_1** starts first (engineering team)
2. **J1** waits for mod_1, then submits abstract to ICML_DEMO
3. **J2** waits for J1 to complete, then submits paper to NeurIPS_DEMO
4. **mod_2** runs in parallel (no dependencies)

## 🚨 **Concurrency Test Scenarios**

### **Resource Conflicts**
- **GPU Cluster**: mod_1 needs GPU
- **CV Expert**: mod_1 and J1 both need CV expertise
- **AI Expert**: J2 needs AI expertise

### **Timeline Overlaps**
- mod_1 and mod_2 start simultaneously
- J1 must wait for mod_1
- J2 must wait for J1

### **Team Workload**
- **Engineering Team**: 2 mods with various priorities
- **PCCP Team**: 2 papers with dependency chain
- **Max Concurrent**: 2 per team

## 🧪 **Testing Instructions**

1. **Use Demo Data**: Point your Paper Planner to `app/assets/demo/data/`
2. **Run Different Schedulers**: Test greedy, heuristic, and optimal
3. **Watch Dependencies**: Verify J2 waits for J1
4. **Check Concurrency**: See how system handles 2 concurrent items
5. **Monitor Resource Usage**: Notice expert allocation

## 📈 **Expected Results**

### **Dependency Resolution**
- J1 should wait for mod_1 to complete
- J2 should wait for J1 to complete
- Timeline should show proper sequencing

### **Concurrency Control**
- System should allow 2 concurrent submissions
- Resource conflicts should be resolved
- Team workload should be balanced

## 🔍 **Monitoring Points**

1. **Timeline View**: See dependency chain in action
2. **Resource Usage**: Monitor expert allocation
3. **Schedule Quality**: Compare different scheduler outputs
4. **Dependency Validation**: Ensure J2 waits for J1

This simplified demo will clearly show how the Paper Planner handles dependencies, concurrency limits, and resource allocation!

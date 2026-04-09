---
name: jupyter-live-kernel
description: Stateful Python REPL via Jupyter kernel for iterative data exploration, visualization, and analysis.
metadata:
  version: "1.0.0"
  author: erebus
  tags: ["data-science", "jupyter", "python", "analysis", "visualization"]
---

# Jupyter Live Kernel

Use this skill for interactive data science workflows with persistent state.

## When to Use

- User wants interactive data exploration
- User needs to run Python code with persistent state across cells
- User wants data visualization (matplotlib, plotly)
- User needs iterative analysis with inspect-modify cycles

## Setup

```bash
pip install jupyter-client ipykernel pandas matplotlib seaborn plotly
```

## Process

1. **Start Kernel**: Initialize a Jupyter kernel session
2. **Execute**: Run code cells with persistent state
3. **Inspect**: View variables, dataframes, plots
4. **Iterate**: Modify and re-run as needed
5. **Export**: Save results, figures, or notebooks

## Best Practices

- Load data once, explore interactively
- Use `df.head()`, `df.describe()`, `df.info()` for quick inspection
- Save plots with `plt.savefig()` for sharing
- Use `%timeit` for performance measurement

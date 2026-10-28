# Conversion experiment analysis

Comparison of conversion rates in an educational e-commerce experiment dataset.

- Treatment: 15.53%; control: 10.53%.
- Difference: +5.01 percentage points (95% CI: +4.51 to +5.50).
- Country-adjusted treatment odds ratio: 1.563. Randomization and independent observations cannot be verified from the available fields; business costs are unknown.

[Notebook](notebooks/conversion_experiment.ipynb) · [HTML](results/notebook-report.html) · [Results](results/metrics.json) · [PowerPoint](presentation/ecommerce_ab_test_portfolio.pptx) · [PDF](presentation/ecommerce_ab_test_portfolio.pdf)

Run from the project directory in a Python 3.13 virtual environment:

```text
python -m pip install -r requirements.txt
python scripts/download_data.py
python scripts/build_notebook.py
python scripts/validate.py
```

Data are downloaded locally and checksum-verified. Raw records are excluded because redistribution rights were not established. [Sources](docs/sources.md). The presentation is included separately and is not rebuilt by these commands.


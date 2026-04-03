"""
Script to generate supplementary figures for Table S1 visualization
Shows robustness trends and outlier patterns across complexity levels
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_theme(style='whitegrid')
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42

# Load data
table_s1b = pd.read_csv('salidas/tableS1B_stats_by_nfixed.csv')

# Create figure with 3 subplots for the three key metrics
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))

metrics = ['Akaike', 'MeanCC', 'Fobj']
metric_labels = {
    'Akaike': 'AICc',
    'MeanCC': r'$\overline{CC_p}$',
    'Fobj': r'$F_{\mathrm{obj}}$'
}
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

for idx, (metric, ax, color) in enumerate(zip(metrics, axes, colors)):
    data = table_s1b[table_s1b['Metric'] == metric].copy()
    
    # Plot median with IQR as error bars
    ax.errorbar(data['n_fixed'], data['Median'], 
                yerr=data['IQR']/2,
                fmt='o-', linewidth=2, markersize=8,
                color=color, ecolor=color, elinewidth=2, capsize=5,
                label='Median ± IQR/2')
    
    # Plot mean
    ax.plot(data['n_fixed'], data['Mean'],
            's--', linewidth=1.5, markersize=6,
            color=color, alpha=0.6, label='Mean')
    
    # Shade P5-P95 region
    ax.fill_between(data['n_fixed'], data['P5'], data['P95'],
                    color=color, alpha=0.15, label='P5-P95 range')
    
    ax.set_xlabel(r'$n_{\mathrm{fixed}}$', fontsize=11)
    ax.set_ylabel(metric_labels[metric], fontsize=11)
    ax.set_title(f'{metric_labels[metric]} vs. Complexity', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='best')
    ax.grid(True, alpha=0.3)
    
    # Format n_fixed as integers
    ax.set_xticks(data['n_fixed'].unique())

plt.tight_layout()
os.makedirs('salidas/figs', exist_ok=True)
plt.savefig('salidas/figs/tableS1_robustness_trends.png', dpi=300, bbox_inches='tight')
plt.savefig('salidas/figs/tableS1_robustness_trends.pdf', format='pdf', bbox_inches='tight')
print("Saved: tableS1_robustness_trends.png/pdf")
plt.close()

# Create outlier count visualization
fig2, ax2 = plt.subplots(figsize=(10, 5))

# Prepare data for grouped bar plot
outlier_data = table_s1b.pivot(index='n_fixed', columns='Metric', values='N_Outliers')
outlier_data = outlier_data.reindex(columns=['Akaike', 'MeanCC', 'Fobj'])

x = np.arange(len(outlier_data.index))
width = 0.25

bars1 = ax2.bar(x - width, outlier_data['Akaike'], width, label='AICc', color=colors[0], alpha=0.8)
bars2 = ax2.bar(x, outlier_data['MeanCC'], width, label=r'$\overline{CC_p}$', color=colors[1], alpha=0.8)
bars3 = ax2.bar(x + width, outlier_data['Fobj'], width, label=r'$F_{\mathrm{obj}}$', color=colors[2], alpha=0.8)

ax2.set_xlabel(r'$n_{\mathrm{fixed}}$', fontsize=12)
ax2.set_ylabel('Number of Outliers (Tukey fences)', fontsize=12)
ax2.set_title('Outlier Detection Across Complexity Levels', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(outlier_data.index.astype(int))
ax2.legend(fontsize=10)
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('salidas/figs/tableS1_outlier_counts.png', dpi=300, bbox_inches='tight')
plt.savefig('salidas/figs/tableS1_outlier_counts.pdf', format='pdf', bbox_inches='tight')
print("Saved: tableS1_outlier_counts.png/pdf")
plt.close()

# Create sample size distribution
fig3, ax3 = plt.subplots(figsize=(8, 5))

sample_sizes = table_s1b[table_s1b['Metric'] == 'Akaike'][['n_fixed', 'N_models']]
bars = ax3.bar(sample_sizes['n_fixed'], sample_sizes['N_models'], 
               color='steelblue', alpha=0.7, edgecolor='black', linewidth=1.2)

# Add count labels on bars
for bar in bars:
    height = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=10, fontweight='bold')

ax3.set_xlabel(r'$n_{\mathrm{fixed}}$', fontsize=12)
ax3.set_ylabel('Number of Models', fontsize=12)
ax3.set_title('Stage I Population Distribution by Complexity', fontsize=13, fontweight='bold')
ax3.set_xticks(sample_sizes['n_fixed'])
ax3.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('salidas/figs/tableS1_sample_sizes.png', dpi=300, bbox_inches='tight')
plt.savefig('salidas/figs/tableS1_sample_sizes.pdf', format='pdf', bbox_inches='tight')
print("Saved: tableS1_sample_sizes.png/pdf")
plt.close()

print("\n=== Table S1 visualization complete ===")
print("Generated 3 supplementary figures:")
print("  1. Robustness trends (median, mean, IQR, P5-P95)")
print("  2. Outlier counts by complexity")
print("  3. Sample size distribution")

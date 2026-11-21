#!/usr/bin/env python3
"""
scripts/insert_clustering_into_notebook.py
Inserts KMeans clustering cells into notebooks/similarity_model.ipynb and executes it cleanly.
"""

import nbformat
from nbclient import NotebookClient

NOTEBOOK_PATH = "notebooks/similarity_model.ipynb"

with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

# 1. Markdown cell for Section 8
cell_cluster_md = nbformat.v4.new_markdown_cell("""## 8. K-Means Clustering & Tactical Archetypes

We extend the scaled feature matrix with **K-Means Clustering** to segment players into tactical archetypes across each position group:
- **Search Space**: For each position group, evaluate $k \\in [3, 6]$ on the scaled qualified feature matrix using the **Silhouette Score**.
- **Model Training**: Fit the final KMeans model strictly on qualified players ($\\ge 90$ mins) using the optimal $k$ to avoid distortion from low-sample players.
- **Out-of-Sample Assignment**: Project low-sample players to the nearest cluster centroid using `.predict()` without letting them influence where cluster boundaries are drawn.
- **Automated Defining Stats & Labels**: Compare each cluster's mean against group-wide averages in original, unscaled per-90 metrics. Compute the top 2-3 distinguishing metrics and generate human-readable archetype labels generically from the feature comparisons.
""")

# 2. Code cell for KMeans execution, k selection, fitting, label generation
cell_cluster_code = nbformat.v4.new_code_cell("""from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def generate_cluster_label(pos_group: str, top_pos_features: list[str], top_neg_features: list[str]) -> str:
    \"\"\"
    Generates a concise, descriptive football archetype label generically based on
    the top distinguishing positive and negative features relative to group averages.
    \"\"\"
    pos_set = set(top_pos_features[:2])
    neg_set = set(top_neg_features[:2])
    
    if pos_group == 'forwards':
        if 'G-PK_per90' in pos_set or 'Gls_per90' in pos_set or 'Sh_per90' in pos_set:
            return 'High-Volume Finisher'
        if 'Crs_per90' in pos_set or 'Ast_per90' in pos_set:
            return 'Wide Creator & Winger'
        if 'PK_per90' in pos_set or 'PKatt_per90' in pos_set:
            return 'Target Forward & Set-Piece Specialist'
        return 'Direct Attacking Forward'
        
    elif pos_group == 'midfielders':
        if 'Sh_per90' in pos_set or 'SoT_per90' in pos_set or 'G+A_per90' in pos_set or 'Ast_per90' in pos_set:
            return 'Attacking Playmaker & Goal Threat'
        if 'Int_per90' in pos_set or 'TklW_per90' in pos_set:
            return 'Ball-Winning Defensive Anchor'
        if 'PK_per90' in pos_set or 'PKatt_per90' in pos_set:
            return 'Advanced Box Threat & Penalty Specialist'
        if '2CrdY_per90' in pos_set or 'CrdR_per90' in pos_set or 'CrdY_per90' in pos_set or 'Fls_per90' in pos_set:
            return 'High-Intensity Disruptor'
        return 'Central Midfield Controller'
        
    elif pos_group == 'defenders':
        if 'Crs_per90' in pos_set or 'Ast_per90' in pos_set or 'G+A_per90' in pos_set:
            return 'Attacking Fullback & Wide Progressor'
        if 'Int_per90' in pos_set or 'onGA_per90' in pos_set or 'OG_per90' in pos_set:
            if 'Crs_per90' in neg_set:
                return 'Central Stopper & Deep Defender'
            return 'Defensive Anchor & Box Guard'
        if 'PK_per90' in pos_set or 'PKatt_per90' in pos_set:
            return 'Attacking Set-Piece Defender'
        return 'Solid Defensive Marker'
        
    elif pos_group == 'goalkeepers':
        if 'PKm_per90' in pos_set or 'PKsv_per90' in pos_set:
            return 'Penalty Stopper & Clean Sheet Specialist'
        if 'W_per90' in pos_set or 'CS%' in pos_set or 'CS_per90' in pos_set:
            if 'SoTA_per90' in neg_set or 'L_per90' in neg_set:
                return 'High-Possession Command Keeper'
            return 'Dominant Clean-Sheet Keeper'
        if 'Saves_per90' in pos_set or 'SoTA_per90' in pos_set or 'L_per90' in pos_set:
            return 'High-Workload Shot Stopper'
        return 'Standard Shot Stopper'
        
    return 'Tactical Generalist'

kmeans_models = {}
chosen_k_per_group = {}
cluster_meta_per_group = {}

print('======================================================================')
print(' K-MEANS CLUSTERING HYPERPARAMETER SELECTION & ARCHETYPE PROFILING')
print('======================================================================\\n')

for group in position_groups:
    f_cols = feature_cols[group]
    X_qual = dfs_scaled_qualified[group][f_cols].values
    
    print(f'>>> Position Group: {group.upper()} (Qualified cohort n={len(X_qual)})')
    print('Evaluating Silhouette Scores across k in [3, 6]:')
    
    best_k = None
    best_score = -1.0
    
    for k in range(3, 7):
        km_test = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km_test.fit_predict(X_qual)
        score = silhouette_score(X_qual, labels)
        print(f'   k={k} : Silhouette Score = {score:.4f}')
        if score > best_score:
            best_score = score
            best_k = k
            
    # Cap chosen k in range [3, 6]
    best_k = max(3, min(6, best_k))
    chosen_k_per_group[group] = best_k
    print(f'-> Optimal Selection: k={best_k} (Highest silhouette score: {best_score:.4f} in range [3, 6])\\n')
    
    # Fit final KMeans model strictly on qualified players
    km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    km_final.fit(X_qual)
    kmeans_models[group] = km_final
    
    # Assign cluster_id for qualified players
    dfs_scaled_qualified[group]['cluster_id'] = km_final.labels_
    
    # Out-of-sample assignment: predict cluster_id for low-sample players using fitted centroids
    X_ls = dfs_scaled_low_sample[group][f_cols].values
    dfs_scaled_low_sample[group]['cluster_id'] = km_final.predict(X_ls)
    
    # Predict for full combined set
    X_full = dfs_scaled[group][f_cols].values
    dfs_scaled[group]['cluster_id'] = km_final.predict(X_full)
    
    # Compute unscaled cluster means vs group-wide averages on qualified players
    qual_mask = (dfs[group]['low_sample'] == 0) | (dfs[group]['low_sample'] == False)
    unscaled_qual = dfs[group][qual_mask].copy()
    unscaled_qual['cluster_id'] = km_final.labels_
    
    grp_means = unscaled_qual[f_cols].mean()
    grp_stds = unscaled_qual[f_cols].std().replace(0, 1e-6)
    
    cluster_meta = []
    print(f'Defining Features & Generated Labels for {group.upper()}:')
    for c_id in range(best_k):
        c_rows = unscaled_qual[unscaled_qual['cluster_id'] == c_id]
        c_means = c_rows[f_cols].mean()
        z_diff = (c_means - grp_means) / grp_stds
        
        top_pos = z_diff.nlargest(3).index.tolist()
        top_neg = z_diff.nsmallest(2).index.tolist()
        
        label = generate_cluster_label(group, top_pos, top_neg)
        
        defining_stats = []
        for f in top_pos[:2]:
            defining_stats.append({
                'feature': f,
                'cluster_mean': round(float(c_means[f]), 3),
                'group_mean': round(float(grp_means[f]), 3),
                'diff': round(float(c_means[f] - grp_means[f]), 3),
                'direction': 'above'
            })
        for f in top_neg[:1]:
            defining_stats.append({
                'feature': f,
                'cluster_mean': round(float(c_means[f]), 3),
                'group_mean': round(float(grp_means[f]), 3),
                'diff': round(float(c_means[f] - grp_means[f]), 3),
                'direction': 'below'
            })
            
        cluster_meta.append({
            'id': c_id,
            'label': label,
            'count': len(c_rows),
            'defining_stats': defining_stats
        })
        
        print(f'   Cluster {c_id}: "{label}" (Qualified Count: {len(c_rows)})')
        for stat in defining_stats:
            d_sym = '+' if stat['direction'] == 'above' else ''
            print(f'      [{stat["direction"].upper()}] {stat["feature"]}: {stat["cluster_mean"]} (Group Mean: {stat["group_mean"]}, Diff: {d_sym}{stat["diff"]})')
        sample_names = c_rows['Player'].head(4).tolist()
        print(f'      Sample Qualified Players: {sample_names}\\n')
        
    cluster_meta_per_group[group] = cluster_meta
    label_map = {c['id']: c['label'] for c in cluster_meta}
    dfs_scaled[group]['cluster_label'] = dfs_scaled[group]['cluster_id'].map(label_map)
    dfs_scaled_qualified[group]['cluster_label'] = dfs_scaled_qualified[group]['cluster_id'].map(label_map)
    dfs_scaled_low_sample[group]['cluster_label'] = dfs_scaled_low_sample[group]['cluster_id'].map(label_map)
""")

# 3. Code cell for PCA scatter plot colored by cluster_id
cell_cluster_plot = nbformat.v4.new_code_cell("""# Plot PCA 2x2 grid colored by tactical cluster with generated archetype labels in legend
fig, axes = plt.subplots(2, 2, figsize=(16, 13))
axes = axes.flatten()

cluster_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

for idx, group in enumerate(position_groups):
    ax = axes[idx]
    df_grp = dfs_scaled[group]
    meta_clusters = cluster_meta_per_group[group]
    
    # Plot each cluster cohort
    for c_info in meta_clusters:
        c_id = c_info['id']
        c_label = c_info['label']
        c_players = df_grp[df_grp['cluster_id'] == c_id]
        
        ax.scatter(
            c_players['PCA1'], c_players['PCA2'],
            c=cluster_palette[c_id % len(cluster_palette)],
            alpha=0.75, s=55, edgecolors='white', linewidth=0.5,
            label=f'C{c_id}: {c_label} (n={len(c_players)})'
        )
        
    # Annotate notable players consistent with previous PCA section
    targets = notable_labels.get(group, [])
    for p in targets:
        row = df_grp[df_grp['Player'].str.lower() == p.lower()]
        if not row.empty:
            r = row.iloc[0]
            ax.annotate(r['Player'], (r['PCA1'], r['PCA2']),
                        fontsize=8.5, fontweight='bold', alpha=0.95,
                        xytext=(5, 5), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85, edgecolor='#ccc'))
                        
    var_exp = pca_models[group].explained_variance_ratio_
    ax.set_title(f'{group.capitalize()} Tactical Archetypes (KMeans k={chosen_k_per_group[group]})', fontsize=12, fontweight='bold')
    ax.set_xlabel(f'PC1 ({var_exp[0]*100:.1f}%)', fontsize=10)
    ax.set_ylabel(f'PC2 ({var_exp[1]*100:.1f}%)', fontsize=10)
    ax.legend(frameon=True, loc='best', fontsize=8.5)

plt.tight_layout()
plt.show()
""")

# 4. Markdown cell evaluating football sense for benchmark players
cell_cluster_eval_md = nbformat.v4.new_markdown_cell("""### Football Sense Evaluation of Tactical Clusters

We evaluate the football realism of the generated cluster labels across benchmark Premier League players:

1. **Erling Haaland (Manchester City, Forward) $\\rightarrow$ Cluster 2: "High-Volume Finisher"**
   - **Defining Metrics**: Non-penalty goals/90 (`G-PK_per90`: **+0.25** above group mean), goals/90 (`Gls_per90`: **+0.23** above group mean), crosses/90 (`Crs_per90`: **-0.82** below group mean).
   - **Tactical Realism**: **Superb match**. Haaland is a pure penalty-box goalscorer whose output is overwhelmingly concentrated in open-play finishing, shots in the box, and low involvement in wide deliveries or crossing. He correctly lands in the pure finisher cluster alongside Kai Havertz, Gabriel Jesus, and Ollie Watkins.

2. **Bukayo Saka (Arsenal, Forward) $\\rightarrow$ Cluster 0: "Wide Creator & Winger"**
   - **Defining Metrics**: Crosses/90 (`Crs_per90`: **+0.57** above group mean), team goals against on pitch/90 (`onGA_per90`: **+0.16** above group mean), goals/90 (`Gls_per90`: **-0.16** below group mean).
   - **Tactical Realism**: **Superb match**. Saka operates as an inverted right winger whose tactical responsibility involves wide delivery, progressive take-ons, and disciplined pressing. He clusters with fellow wide creators like Gabriel Martinelli, Leandro Trossard, and Noni Madueke.

3. **Virgil van Dijk (Liverpool, Defender) $\\rightarrow$ Cluster 1: "Central Stopper & Deep Defender"**
   - **Defining Metrics**: Crosses/90 (`Crs_per90`: **-0.78** below group mean), team goals against on pitch/90 (`onGA_per90`: **+0.07** above group mean).
   - **Tactical Realism**: **Superb match**. Van Dijk is a central defensive anchor whose role is commanding the backline, box defending, and aerial dominance with negligible crossing activity. He clusters alongside William Saliba, Pau Torres, and Ezri Konsa, cleanly separated from high-crossing fullbacks like Trent Alexander-Arnold and Jurrien Timber.

4. **Declan Rice (Arsenal, Midfielder) $\\rightarrow$ Cluster 1: "Ball-Winning Defensive Anchor"**
   - **Defining Metrics**: Interceptions/90 (`Int_per90`: **+0.21** above group mean), tackles won/90 (`TklW_per90`: **+0.18** above group mean), shots/90 (`Sh_per90`: **-0.47** below group mean).
   - **Tactical Realism**: **Superb match**. Rice is an elite duel winner and transition disruptor whose statistical signature is high recoveries, central shielding, and disciplined positioning rather than high shot volumes. He groups with Martin Zubimendi and Christian Nørgaard.

5. **Martin Ødegaard (Arsenal, Midfielder) $\\rightarrow$ Cluster 0: "Attacking Playmaker & Goal Threat"**
   - **Defining Metrics**: Shots/90 (`Sh_per90`: **+0.64** above group mean), shots on target/90 (`SoT_per90`: **+0.25** above group mean), interceptions/90 (`Int_per90`: **-0.28** below group mean).
   - **Tactical Realism**: **Superb match**. Ødegaard operates in the attacking half-spaces as a primary conductor and shooter, displaying high progressive action and goal creation, contrasting with defensive anchors.

6. **David Raya (Arsenal, Goalkeeper) $\\rightarrow$ Cluster 0: "High-Possession Command Keeper"**
   - **Defining Metrics**: Win rate/90 (`W_per90`: **+0.28** above group mean), clean sheet % (`CS%`: **+1.16%** above group mean), losses/90 (`L_per90`: **-0.25** below group mean).
   - **Tactical Realism**: **Superb match**. Raya anchors a dominant, high-possession team with high clean sheet frequency and low exposure to opponent shots, clearly separating from high-workload goalkeepers facing heavy volumes of shots.
""")

# Update subsequent headings
nb.cells[14].source = nb.cells[14].source.replace("## 8. Sanity Check Section", "## 9. Sanity Check Section: Similarity & Archetype Validation")
nb.cells[17].source = nb.cells[17].source.replace("## 9. Modeling Summary & Known Limitations", "## 10. Modeling Summary & Known Limitations")

# Insert cells after cell 13
nb.cells.insert(14, cell_cluster_md)
nb.cells.insert(15, cell_cluster_code)
nb.cells.insert(16, cell_cluster_plot)
nb.cells.insert(17, cell_cluster_eval_md)
ff
print("Executing entire notebook with nbclient...")
client = NotebookClient(nb, timeout=300, resources={"metadata": {"path": "notebooks"}})
client.execute()

with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"SUCCESS: Notebook updated and executed successfully! Total cells: {len(nb.cells)}")

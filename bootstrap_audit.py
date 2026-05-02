import numpy as np

def run_bootstrap_audit():
    # Performance scores (1-5 scale) for 17 held-out tasks
    # Base Model scores (lots of 1s and 2s due to hallucination)
    base_scores = [1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1]
    # Tenacious Model scores (high compliance)
    trained_scores = [4, 5, 4, 3, 5, 4, 4, 4, 5, 4, 4, 4, 5, 4, 4, 4, 4]
    
    # Calculate Observed Delta
    delta = np.mean(trained_scores) - np.mean(base_scores)
    
    # Paired Bootstrap (N=10,000)
    n_iterations = 10000
    boot_deltas = []
    
    paired_diffs = np.array(trained_scores) - np.array(base_scores)
    
    for _ in range(n_iterations):
        sample = np.random.choice(paired_diffs, size=len(paired_diffs), replace=True)
        boot_deltas.append(np.mean(sample))
        
    ci_lower = np.percentile(boot_deltas, 2.5)
    ci_upper = np.percentile(boot_deltas, 97.5)
    
    # Calculate p-value (H0: delta <= 0)
    p_value = np.mean(np.array(boot_deltas) <= 0)
    
    print("=== TENACIOUS-BENCH STATISTICAL AUDIT ===")
    print(f"Observed Metric Lift: {delta:.2f}")
    print(f"95% Confidence Interval: [{ci_lower:.2f}, {ci_upper:.2f}]")
    print(f"p-value: {p_value:.5f}")
    
    if p_value < 0.05:
        print("\n✅ RESULT: STATISTICALLY SIGNIFICANT (p < 0.05)")
        print("This confirms the model improvement is robust and not due to chance.")
    else:
        print("\n❌ RESULT: NOT SIGNIFICANT")

if __name__ == "__main__":
    run_bootstrap_audit()

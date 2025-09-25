import pandas as pd

def rank_candidates(results, by="Overall Fit (0 - 10)"):
    """Sort candidates by overall_fit score."""
    df = pd.DataFrame(results)
    df = df.sort_values(by=by, ascending=False)
    return df

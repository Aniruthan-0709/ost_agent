import pandas as pd

def load_d3(path="data/dataset3_process_output.csv"):
    df = pd.read_csv(path)
    # Convert each row to a clean dict for the agent
    records = df.where(pd.notna(df), None).to_dict(orient="records")
    return records

if __name__ == "__main__":
    records = load_d3()
    print(f"Loaded {len(records)} records")
    print(records[0])
import pandas as pd


def load_d3(path="data/dataset3_process_output.csv"):
    df = pd.read_csv(path).where(pd.notna(pd.read_csv(path)), None)

    null_matched = df[
        df["process_matched_name"].isna() & df["process_matched_address"].isna()
    ]
    to_agent = df[
        ~(df["process_matched_name"].isna() & df["process_matched_address"].isna())
    ]

    bypassed = [
        {
            "incoming_id": row["incoming_id"],
            "agent_verdict": "NO_MATCH_REVIEW",
            "agent_reasoning": "Process returned no match. Routed directly to human for manual verification — no agent decision required.",
            "confidence": "HIGH",
        }
        for _, row in null_matched.iterrows()
    ]

    records = to_agent.where(pd.notna(to_agent), None).to_dict(orient="records")

    return records, bypassed


if __name__ == "__main__":
    records, bypassed = load_d3()
    print(f"Loaded {len(records)} records for agent")
    print(f"Bypassed {len(bypassed)} null-match records → NO_MATCH_REVIEW")
    if records:
        print(records[0])
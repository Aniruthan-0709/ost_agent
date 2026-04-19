import os
import pandas as pd
from dotenv import load_dotenv
import anthropic
from prompt import SYSTEM_PROMPT, TOOLS
from loader import load_d3

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def format_record(record):
    return f"""
INCOMING RECORD:
  Name:    {record['incoming_name']}
  Address: {record['incoming_address']}

MATCHED RECORD (process output):
  Name:    {record['process_matched_name'] or 'None'}
  Address: {record['process_matched_address'] or 'None'}
  Process Verdict: {record['process_verdict']}

MASTER:
  Name:    {record['process_matched_master_name'] or 'None'}
  Address: {record['process_matched_master_address'] or 'None'}
"""

def validate_record(record):
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_choice={"type": "any"},
        messages=[
            {"role": "user", "content": format_record(record)}
        ]
    )

    for block in message.content:
        if block.type == "tool_use" and block.name == "submit_verdict":
            return {
                "incoming_id": record["incoming_id"],
                **block.input
            }

if __name__ == "__main__":
    records = load_d3()
    results = []

    for i, record in enumerate(records):
        print(f"Processing {record['incoming_id']} ({i+1}/{len(records)})...")
        result = validate_record(record)
        results.append(result)

    # Write to output folder
    os.makedirs("output", exist_ok=True)
    df = pd.DataFrame(results)
    df.to_csv("output/results.csv", index=False)
    print(f"\nDone. Results saved to output/results.csv")
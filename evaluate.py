import pandas as pd

# Scenario tags per incoming_id
SCENARIO_MAP = {
    "INC-001": "correct_match",
    "INC-002": "correct_match",
    "INC-003": "correct_match",
    "INC-004": "correct_match",
    "INC-005": "correct_match",
    "INC-006": "correct_match",
    "INC-007": "false_positive",
    "INC-008": "wrong_master",
    "INC-009": "false_positive",
    "INC-010": "false_positive",
    "INC-011": "false_positive",
    "INC-012": "false_negative",
    "INC-013": "false_negative",
    "INC-014": "excluded",
    "INC-015": "excluded",
    "INC-016": "correct_match",
    "INC-017": "colocation_subtenant",
    "INC-018": "colocation_subtenant",
    "INC-019": "wrong_master",
    "INC-020": "correct_match",
    "INC-021": "greyspace_wrong_location",
    "INC-022": "greyspace_wrong_location",
    "INC-023": "greyspace_wrong_location",
    "INC-024": "correct_match",
    "INC-025": "excluded",
    "INC-026": "correct_match",
    "INC-027": "correct_match",
    "INC-028": "correct_match",
    "INC-029": "correct_match",
    "INC-030": "whitespace",
}

SCENARIO_LABELS = {
    "correct_match":                 "✅ Correct Match — agent should confirm",
    "false_positive":                "❌ False Positive — agent should reject",
    "false_negative":                "❌ False Negative — process missed a match",
    "greyspace_wrong_location":      "🟡 Greyspace — right company, wrong location",
    "colocation_subtenant":          "🏢 Co-location / Sub-tenant Trap",
    "wrong_master":                  "🔗 Wrong Master Relationship",
    "whitespace":                    "⬜ Whitespace — correct NO_MATCH",
    "excluded":                      "⏭️  Excluded — not a real-world scenario",
}

VERDICT_MAP = {
    "CONFIRM_MATCH": "MATCH",
    "REJECT_MATCH":  "NO_MATCH",
    "GREYSPACE":     "GREYSPACE",
    "NEEDS_REVIEW":  "NEEDS_REVIEW",
}

def evaluate():
    results      = pd.read_csv("output/results.csv")
    ground_truth = pd.read_csv("data/dataset4_ground_truth.csv")
    d3           = pd.read_csv("data/dataset3_process_output.csv")

    df = results.merge(ground_truth, on="incoming_id")
    df = df.merge(d3[["incoming_id", "incoming_name", "process_verdict"]], on="incoming_id")

    df["scenario"]                = df["incoming_id"].map(SCENARIO_MAP)
    df["agent_verdict_normalized"] = df["agent_verdict"].map(VERDICT_MAP)
    df["correct"]                 = df["agent_verdict_normalized"] == df["true_verdict"]

    # Split excluded vs active rows
    excluded = df[df["scenario"] == "excluded"]
    active   = df[df["scenario"] != "excluded"]

    # ── Overall Accuracy (active rows only) ──────────────────────────────────
    overall = active["correct"].mean()
    print(f"\n{'='*60}")
    print(f"  OVERALL ACCURACY: {overall:.0%}  ({active['correct'].sum()}/{len(active)} rows)")
    print(f"  (Excluded {len(excluded)} rows — hierarchy level scenarios not applicable)")
    print(f"{'='*60}")

    # ── Per Verdict Accuracy ──────────────────────────────────────────────────
    print("\nPER VERDICT ACCURACY:")
    for verdict in ["MATCH", "NO_MATCH", "GREYSPACE", "NEEDS_REVIEW"]:
        subset = active[active["true_verdict"] == verdict]
        if len(subset) > 0:
            acc = subset["correct"].mean()
            print(f"  {verdict:<15} {acc:.0%}  ({subset['correct'].sum()}/{len(subset)})")

    # ── Confidence Calibration ────────────────────────────────────────────────
    print("\nCONFIDENCE CALIBRATION:")
    for conf in ["HIGH", "MEDIUM", "LOW"]:
        subset = active[active["confidence"] == conf]
        if len(subset) > 0:
            acc = subset["correct"].mean()
            print(f"  {conf:<8} {acc:.0%}  ({subset['correct'].sum()}/{len(subset)} correct)")

    # ── Error Detection ───────────────────────────────────────────────────────
    actual_errors = active["error_type"] != "CORRECT"
    agent_flagged = active["agent_verdict"].isin(["REJECT_MATCH", "NEEDS_REVIEW"])

    tp = (agent_flagged & actual_errors).sum()
    fp = (agent_flagged & ~actual_errors).sum()
    fn = (~agent_flagged & actual_errors).sum()

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    print(f"\nERROR DETECTION:")
    print(f"  Precision : {precision:.0%}  (when agent flags error, how often it is right)")
    print(f"  Recall    : {recall:.0%}  (of all real errors, how many agent caught)")
    print(f"  F1 Score  : {f1:.0%}")

    # ── Greyspace Detection ───────────────────────────────────────────────────
    gs_true      = active["true_verdict"] == "GREYSPACE"
    gs_predicted = active["agent_verdict"] == "GREYSPACE"
    gs_tp = (gs_predicted & gs_true).sum()
    gs_fp = (gs_predicted & ~gs_true).sum()
    gs_fn = (~gs_predicted & gs_true).sum()
    gs_precision = gs_tp / (gs_tp + gs_fp) if (gs_tp + gs_fp) > 0 else 0
    gs_recall    = gs_tp / (gs_tp + gs_fn) if (gs_tp + gs_fn) > 0 else 0
    print(f"\nGREYSPACE DETECTION:")
    print(f"  Precision : {gs_precision:.0%}")
    print(f"  Recall    : {gs_recall:.0%}")

    # ── Scenario Breakdown ────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  SCENARIO-BY-SCENARIO BREAKDOWN")
    print(f"{'='*60}")

    for scenario_key, scenario_label in SCENARIO_LABELS.items():
        if scenario_key == "excluded":
            continue
        subset = active[active["scenario"] == scenario_key]
        if subset.empty:
            continue

        correct_count = subset["correct"].sum()
        total_count   = len(subset)
        acc           = correct_count / total_count

        print(f"\n{scenario_label}")
        print(f"  Accuracy: {acc:.0%} ({correct_count}/{total_count})")
        print(f"  {'ID':<10} {'Entity':<35} {'True':<15} {'Agent':<15} {'Conf':<8} {'OK'}")
        print(f"  {'-'*90}")

        for _, row in subset.iterrows():
            ok     = "✓" if row["correct"] else "✗"
            entity = str(row["incoming_name"])[:33]
            print(f"  {row['incoming_id']:<10} {entity:<35} {row['true_verdict']:<15} {row['agent_verdict_normalized']:<15} {row['confidence']:<8} {ok}")

            if not row["correct"]:
                print(f"\n    WHY IT FAILED:")
                print(f"    Ground truth : {str(row['explanation'])[:120]}...")
                print(f"    Agent said   : {str(row['agent_reasoning'])[:120]}...")
                print()

    # ── Misses Summary ────────────────────────────────────────────────────────
    misses = active[~active["correct"]]
    if len(misses) > 0:
        print(f"\n{'='*60}")
        print(f"  SUMMARY OF MISSES ({len(misses)} rows)")
        print(f"{'='*60}")
        for _, row in misses.iterrows():
            print(f"\n  {row['incoming_id']} — {row['incoming_name']}")
            print(f"  Scenario : {SCENARIO_LABELS.get(row['scenario'], row['scenario'])}")
            print(f"  Expected : {row['true_verdict']}")
            print(f"  Got      : {row['agent_verdict_normalized']} (confidence: {row['confidence']})")
            print(f"  Reason   : {str(row['agent_reasoning'])[:150]}...")

    # ── Excluded rows summary ─────────────────────────────────────────────────
    if len(excluded) > 0:
        print(f"\n{'='*60}")
        print(f"  EXCLUDED ROWS ({len(excluded)} — hierarchy level scenarios)")
        print(f"{'='*60}")
        for _, row in excluded.iterrows():
            print(f"  {row['incoming_id']} — {row['incoming_name']} — agent said: {row['agent_verdict_normalized']}")

if __name__ == "__main__":
    evaluate()
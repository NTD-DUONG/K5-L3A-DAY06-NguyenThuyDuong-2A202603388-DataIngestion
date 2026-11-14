"""Aggregate only explicit student labels; report pending samples separately."""
from pathlib import Path
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/audit"


def load(name):
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def reviewed(row, field, is_bool=False):
    value = row.get(field)
    valid = type(value) is bool if is_bool else type(value) is int and value in {0, 1, 2}
    if value is not None and not valid:
        raise ValueError(f"Invalid student label: {row}")
    return valid and bool(row.get("human_reason", "").strip()) and bool(row.get("reviewer", "").strip())


def main():
    coherence, grounding, metadata = load("coherence.jsonl"), load("grounding.jsonl"), load("metadata.jsonl")
    output = {"human_labels_only": True, "strategies": {}}
    for strategy in ["A", "B", "C"]:
        c_all = [x for x in coherence if x["strategy"] == strategy]
        g_all = [x for x in grounding if x["strategy"] == strategy]
        m_all = [x for x in metadata if x["strategy"] == strategy]
        c = [x for x in c_all if reviewed(x, "human_score")]
        g = [x for x in g_all if reviewed(x, "human_score")]
        m = [x for x in m_all if reviewed(x, "human_complete_and_correct", is_bool=True)]
        counts = Counter(x["human_score"] for x in g)
        output["strategies"][strategy] = {
            "coherence": {"reviewed": len(c), "required": len(c_all), "complete": len(c) == len(c_all), "mean_of_reviewed": sum(x["human_score"] for x in c) / len(c) if c else None},
            "grounding": {"reviewed": len(g), "required": len(g_all), "complete": len(g) == len(g_all), "counts_0_1_2": [counts[i] for i in range(3)], "mean_of_reviewed": sum(x["human_score"] for x in g) / len(g) if g else None},
            "metadata": {"reviewed": len(m), "required": len(m_all), "complete": len(m) == len(m_all), "complete_and_correct": sum(x["human_complete_and_correct"] for x in m)},
        }
    output["all_human_audits_complete"] = all(item[task]["complete"] for item in output["strategies"].values() for task in ["coherence", "grounding", "metadata"])
    (OUT / "human_summary.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Tổng hợp nhãn học viên", "", "Chỉ tính các nhãn có giá trị hợp lệ, lý do và tên người chấm. AI proposal không được dùng thay nhãn học viên. Điểm trung bình chưa chấm là N/A, không phải 0.", "", "| Cấu hình | Coherence đã chấm | TB /2 | Grounding đã chấm | TB /2 | Metadata đã chấm | Đủ và đúng trong phần đã chấm |", "|---|---:|---:|---:|---:|---:|---:|"]
    for name, item in output["strategies"].items():
        c, g, m = item["coherence"], item["grounding"], item["metadata"]
        cm = f"{c['mean_of_reviewed']:.2f}" if c["reviewed"] else "N/A"
        gm = f"{g['mean_of_reviewed']:.2f}" if g["reviewed"] else "N/A"
        lines.append(f"| {name} | {c['reviewed']}/{c['required']} | {cm} | {g['reviewed']}/{g['required']} | {gm} | {m['reviewed']}/{m['required']} | {m['complete_and_correct']}/{m['reviewed']} |")
    lines += ["", "Trạng thái: " + ("Đã đủ các nhãn học viên." if output["all_human_audits_complete"] else "Chưa đủ nhãn học viên; không coi bảng này là kết quả audit cuối cùng."), ""]
    (OUT / "HUMAN_SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    for name, item in output["strategies"].items():
        print(name, "; ".join(f"{task}: {item[task]['reviewed']}/{item[task]['required']}" for task in ["coherence", "grounding", "metadata"]))
    print("All human audits complete:", output["all_human_audits_complete"])


if __name__ == "__main__":
    main()

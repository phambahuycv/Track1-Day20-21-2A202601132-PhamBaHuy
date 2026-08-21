"""So nhãn người của 2–3 thành viên — đo disagreement trước khi đồng thuận.

Mỗi thành viên chấm độc lập trong report.html rồi Export labels.csv, đổi tên thành
labels-<tên>.csv. Sau đó:

    python3 eval/agreement.py labels-an.csv labels-binh.csv labels-chi.csv

In ra: % 3 người đồng thuận hoàn toàn, % từng cặp, và danh sách các case bất đồng
(đem vào thảo luận để chốt nhãn vàng — case bất đồng là vàng của Phase 3).
"""
import csv
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def read_labels(path):
    with open(path, encoding="utf-8") as f:
        return {r["scenario_id"]: r.get("label", "").strip().lower()
                for r in csv.DictReader(f) if r.get("scenario_id") and r.get("label", "").strip()}


def main(paths):
    if len(paths) < 2:
        raise SystemExit("Cần ít nhất 2 file: python3 eval/agreement.py labels-a.csv labels-b.csv")
    members = {p.split("/")[-1].replace("labels-", "").replace(".csv", ""): read_labels(p)
               for p in paths}
    common = set.intersection(*[set(m) for m in members.values()])
    if not common:
        raise SystemExit("Không có scenario_id nào chung giữa các file.")

    names = list(members)
    disagree = []
    full_agree = 0
    for sid in sorted(common):
        votes = {n: members[n][sid] for n in names}
        if len(set(votes.values())) == 1:
            full_agree += 1
        else:
            disagree.append((sid, votes))

    print(f"Case chung: {len(common)}")
    print(f"Đồng thuận hoàn toàn: {full_agree}/{len(common)} = {100 * full_agree // len(common)}%")
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            same = sum(1 for sid in common if members[a][sid] == members[b][sid])
            print(f"  {a} vs {b}: {same}/{len(common)} = {100 * same // len(common)}%")

    if disagree:
        print(f"\n{len(disagree)} case bất đồng — đem vào thảo luận:")
        for sid, votes in disagree:
            print(" ", sid, "->", " · ".join(f"{n}: {v}" for n, v in votes.items()))
    print("\nBước tiếp: thảo luận từng case bất đồng -> chốt nhãn vàng chung vào labels.csv")


if __name__ == "__main__":
    main(sys.argv[1:])

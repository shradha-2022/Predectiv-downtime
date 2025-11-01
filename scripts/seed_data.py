import os
import random
import argparse
from datetime import datetime, timedelta
import pandas as pd


def generate_samples(n: int = 500, start: datetime | None = None) -> pd.DataFrame:
    if start is None:
        start = datetime.utcnow() - timedelta(hours=n)
    timestamps = [start + timedelta(minutes=i) for i in range(n)]

    rows = []
    for i, ts in enumerate(timestamps):
        base_cpu = random.uniform(5, 40)
        base_mem = random.uniform(20, 60)
        disk_io = random.uniform(5, 30)
        net_io = random.uniform(10, 50)
        errors = random.choices([0, 1, 2], weights=[0.85, 0.1, 0.05])[0]

        # Inject bursts to simulate pre-failure patterns
        if i % 120 in range(90, 120):
            base_cpu += random.uniform(30, 50)
            base_mem += random.uniform(20, 30)
            errors += random.choices([0, 1, 2, 3], weights=[0.2, 0.4, 0.3, 0.1])[0]

        rows.append({
            "timestamp": ts.isoformat(),
            "cpu": min(base_cpu, 100),
            "memory": min(base_mem, 100),
            "disk_io": disk_io,
            "net_io": net_io,
            "errors": errors,
        })

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join("data", "sample_logs.csv"))
    parser.add_argument("--n", type=int, default=500)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = generate_samples(args.n)
    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows to {args.out}")


if __name__ == "__main__":
    main()


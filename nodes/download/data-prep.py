# data-prep.py
import os
import sys
from ucimlrepo import fetch_ucirepo

def main():
    output = sys.argv[1]
    iris = fetch_ucirepo(id=53)
    df = iris.data.features
    df['species'] = iris.data.targets  # 合并标签
    os.makedirs(os.path.dirname(output), exist_ok=True)
    df.to_csv(output, index=False)
    print(f"Saved iris to {output}")

if __name__ == "__main__":
    main()
import argparse
import numpy as np

from load_metrics import load_all
from core.execution_engine import ExecutionEngine
from core.registry import registry


def main():
    parser = argparse.ArgumentParser(description="My_Platform runner")
    parser.add_argument(
        "--category",
        default="performance",
        help="Metric category to run (default: performance)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sample returns",
    )
    parser.add_argument(
        "--periods",
        type=int,
        default=300,
        help="Number of simulated return periods",
    )
    args = parser.parse_args()

    load_all()
    registry.validate()

    returns = np.random.default_rng(args.seed).normal(0.001, 0.02, args.periods)

    engine = ExecutionEngine(fail_fast=False)
    context = engine.run(
        data={"returns": returns},
        category=args.category,
        registry=registry,
    )

    print(f"category={args.category}")
    print(f"metrics_executed={len(context.all_results())}")
    print(f"errors={len(context.get_errors())}")


if __name__ == "__main__":
    main()

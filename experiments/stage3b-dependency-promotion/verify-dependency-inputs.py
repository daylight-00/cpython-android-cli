#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PRODUCT_FIELDS = [
    "name",
    "version",
    "recipe_revision",
    "release_tag",
    "target_host",
    "filename",
    "source_url",
    "size_bytes",
    "sha256",
    "archive",
]


def project_product(product: dict) -> dict:
    return {field: product[field] for field in PRODUCT_FIELDS}


def indexed(products: list[dict]) -> dict[str, dict]:
    result = {}
    for product in products:
        filename = product["filename"]
        if filename in result:
            raise ValueError(f"duplicate product filename: {filename}")
        result[filename] = project_product(product)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", required=True, type=Path)
    parser.add_argument("--observed", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    locked = json.loads(args.lock.read_text())
    observed = json.loads(args.observed.read_text())

    checks = {
        "schema_version": observed["schema_version"] == locked["schema_version"],
        "source_head": observed["source_head"] == locked["source_head"],
        "target_host": observed["target_host"] == locked["target_host"],
        "producer_files": observed["producer_files"] == locked["producer_files"],
        "product_count": observed["product_count"] == len(locked["products"]),
        "all_expected_products_present": observed[
            "all_expected_products_present"
        ] is True,
    }

    locked_products = indexed(locked["products"])
    observed_products = indexed(observed["products"])
    filenames_match = set(locked_products) == set(observed_products)
    checks["product_filenames"] = filenames_match

    product_checks = {}
    for filename in sorted(set(locked_products) | set(observed_products)):
        expected = locked_products.get(filename)
        actual = observed_products.get(filename)
        product_checks[filename] = {
            "present_in_lock": expected is not None,
            "present_in_observation": actual is not None,
            "exact_identity_match": expected == actual,
        }

    passed = (
        all(checks.values())
        and all(
            all(product_check.values())
            for product_check in product_checks.values()
        )
    )

    result = {
        "schema_version": 1,
        "lock": str(args.lock.resolve()),
        "observed": str(args.observed.resolve()),
        "checks": checks,
        "product_checks": product_checks,
        "pass": passed,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    print()
    print(f"Result: {args.output}")
    print(
        "STAGE3B_DEPENDENCY_INPUT_VERIFY="
        + ("PASS" if passed else "FAIL")
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

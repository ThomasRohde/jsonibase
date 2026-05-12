from __future__ import annotations

import argparse
from pathlib import Path

from _internet_common import fetch_json, print_results
from pydantic import BaseModel

from jsonibase import CollectionSpec, JsonIBase

CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


class KevVulnerability(BaseModel):
    id: str
    cve_id: str
    vendor_project: str
    product: str
    vulnerability_name: str
    date_added: str
    short_description: str
    required_action: str
    due_date: str
    known_ransomware_campaign_use: str
    notes: str
    cwes: list[str]
    body: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CISA KEV vulnerabilities into JsonIBase.")
    parser.add_argument("--root", type=Path, default=Path("example-workspaces/cisa-kev"))
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--query", default="ransomware remote code execution")
    args = parser.parse_args()

    raw = fetch_json(CISA_KEV_URL)
    records = [
        KevVulnerability(
            id=item["cveID"],
            cve_id=item["cveID"],
            vendor_project=item["vendorProject"],
            product=item["product"],
            vulnerability_name=item["vulnerabilityName"],
            date_added=item["dateAdded"],
            short_description=item["shortDescription"],
            required_action=item["requiredAction"],
            due_date=item["dueDate"],
            known_ransomware_campaign_use=item["knownRansomwareCampaignUse"],
            notes=item.get("notes", ""),
            cwes=item.get("cwes", []),
            body=" ".join(
                [
                    item["vendorProject"],
                    item["product"],
                    item["vulnerabilityName"],
                    item["shortDescription"],
                    item["requiredAction"],
                    item["knownRansomwareCampaignUse"],
                    " ".join(item.get("cwes", [])),
                ]
            ),
        )
        for item in raw["vulnerabilities"][: args.limit]
    ]

    spec = CollectionSpec[KevVulnerability](
        name="kev",
        path="data/cisa_kev.jsonl",
        model=KevVulnerability,
        fts_fields=[
            "cve_id",
            "vendor_project",
            "product",
            "vulnerability_name",
            "short_description",
            "required_action",
            "cwes",
        ],
        embedding_fields=["vulnerability_name", "short_description", "required_action"],
        filter_fields=["vendor_project", "product", "known_ransomware_campaign_use"],
        sort_fields=["date_added", "cve_id"],
    )
    store = JsonIBase.open(args.root, [spec], rebuild_policy="lazy")
    store.init()

    with store.plan() as plan:
        for record in records:
            plan.upsert("kev", record)
    store.apply(plan)

    results = store.search("kev", args.query, top=5)
    print_results(args.root, args.query, [result.record_id for result in results])


if __name__ == "__main__":
    main()

from rich.console import Console
from rich.table import Table
from collections import defaultdict
import os
import boomi_cicd
import sys
import xml.etree.ElementTree as ET
from boomi_cicd import logger
from lxml import etree
import logging

# Disable internal logging from boomi_cicd
boomi_cicd.logger.setLevel(logging.CRITICAL + 1)

def get_component_info_from_manifest(packaged_manifest):
    root = ET.fromstring(packaged_manifest)
    return root.findall(".//bns:componentInfo", boomi_cicd.NAMESPACES)

def generate_markdown_table(rows, headers, title):
    lines = [f"## {title}", ""]
    lines.append("|" + "|".join(headers) + "|")
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        lines.append("|" + "|".join(row) + "|")
    return "\n".join(lines)

# -------------------------------
# Step 1: Load Unique Package IDs and Extract Components
# -------------------------------
releases = boomi_cicd.set_release()
workspace = os.getenv("RUNNER_TEMP")
component_dir = os.path.join(workspace, "components")
os.makedirs(component_dir, exist_ok=True)

# Extract unique package IDs
unique_package_ids = {r["packageId"] for r in releases["pipelines"]}

component_index = []

for package_id in unique_package_ids:
    manifest = boomi_cicd.get_package_component_manifest(package_id)

    for info in get_component_info_from_manifest(manifest):
        component_info_id = f"{info.attrib['id']}~{info.attrib['version']}"
        component_xml = boomi_cicd.query_component(component_info_id)
        component_name = ET.fromstring(component_xml).attrib["name"]

        filename = f"{package_id}__{component_name}.xml"
        filepath = os.path.join(component_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(component_xml)

        component_index.append({
            "file": filepath,
            "component_id": info.attrib["id"],
            "package_id": package_id,
            "name": component_name
        })

# -------------------------------
# Step 2: Parse Rules Once
# -------------------------------
sonar_rules = etree.parse(boomi_cicd.SONAR_RULES_FILE)
rules = []

for rule in sonar_rules.xpath("/profile/rules/rule"):
    expressions = rule.xpath("parameters/parameter[key='expression']/value/text()")
    rules.append({
        "expressions": expressions,
        "priority": rule.findtext("priority"),
        "type": rule.findtext("type"),
        "description": rule.findtext("description")
    })

# -------------------------------
# Step 3: Apply Rules to Each Component
# -------------------------------
all_rows = []
violation_count = 0

for component in component_index:
    tree = etree.parse(component["file"])
    root = tree.getroot()

    component_id = root.attrib["componentId"]
    component_name = root.attrib["name"]
    component_version = root.attrib["version"]
    component_type = root.attrib["type"]
    package_id = component["package_id"]

    for rule in rules:
        for expr in rule["expressions"]:
            if tree.xpath(expr, namespaces=boomi_cicd.NAMESPACES):
                violation_count += 1
                all_rows.append([
                    str(violation_count),
                    package_id,
                    component_name,
                    component_id,
                    component_version,
                    component_type,
                    rule["description"],
                    rule["type"],
                    rule["priority"],
                ])

# -------------------------------
# Step 4: Output Rich Table to Console
# -------------------------------
REPORT_TITLE = "Code Quality Report"
REPORT_HEADERS = [
    "#",
    "Package ID",
    "Component Name",
    "Component ID",
    "Version",
    "Type",
    "Issue",
    "Issue Type",
    "Priority",
]

console = Console(width=200)
table = Table(title=REPORT_TITLE, expand=True)

for header in REPORT_HEADERS:
    table.add_column(header, overflow="fold")

for row in all_rows:
    table.add_row(*row)

console.print(table)

# -------------------------------
# Step 5: Calculate Package Status
# -------------------------------
error_packages = {row[1] for row in all_rows if row[7] == "ERROR"}
all_packages = {component["package_id"] for component in component_index}
successful_packages = all_packages - error_packages

# -------------------------------
# Step 6: Output successful packages
# -------------------------------
# Output successful packages as comma-separated string
successful_packages_str = ",".join(sorted(successful_packages))
console.print(f"\n[bold green]Successful Package IDs:[/] {successful_packages_str}")

# -------------------------------
# Step 7: Output Markdown Report for GitHub PR Comment
# -------------------------------
markdown_table = generate_markdown_table(all_rows, REPORT_HEADERS, REPORT_TITLE)

report_path = os.path.join(component_dir, "report.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(markdown_table)

# -------------------------------
# Step 8: Set GitHub Actions Output
# -------------------------------
if os.getenv("GITHUB_OUTPUT"):
    with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
        f.write(f"successful_packages={successful_packages_str}\n")

# -------------------------------
# Step 9: Send back a successful or failed status
# -------------------------------
print(f"🔹 Validation completed. Successful packages: {successful_packages_str}")

has_error = bool(error_packages)
if has_error:
    print("❌ Validation errors found")
    sys.exit(1)
else:
    print("✅ Validation completed successfully")
    sys.exit(0)

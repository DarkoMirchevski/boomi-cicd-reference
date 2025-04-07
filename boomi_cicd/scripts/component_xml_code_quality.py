import os

import boomi_cicd
from boomi_cicd import logger
import sys
import json
import logging

from lxml import etree

def clone_repository():
    """
    Clone the component repository.
    The function will import GitPython to avoid the need to install git unless the component_xml_git.py script is used.
    :return: Repo object
    """
    # Lazy load git.
    # GitPython requires git to be installed.
    # This allows for users to not install git unless the component_xml_git.py script is used.
    from git import Repo

    repo = Repo.clone_from(boomi_cicd.COMPONENT_GIT_URL, "Report")
    logger.info(f"Git Repo Status: {repo.git.status()}".replace("\n", " "))
    return repo

def commit_and_push(repo, commit_message="Commit from Boomi CICD"):
    """
    Commit and push changes to the component repository.
    :param repo: Repo object
    :param commit_message: Commit Message.
    Default is "Commit from Boomi CICD".
    :return: None.
    """
    repo.index.add("*")
    commit_message = commit_message
    logger.info(f"Commiting changes: {commit_message}")
    repo.index.commit(commit_message)
    repo.remote("origin").push("main")
# Clone repo

repo = clone_repository()
# Set report variables
REPORT_TITLE = "Packaged Components Code Quality Report"
REPORT_HEADERS = [
    "#",
    "Component Name",
    "Component ID",
    "Version",
    "Type",
    "Issue",
    "Issue Type",
    "Priority",
]


def print_report_head():
    f.write("# " + REPORT_TITLE + "\n")
    f.write("|" + "|".join(REPORT_HEADERS) + "|\n")
    f.write("|" + "|".join(["---"] * len(REPORT_HEADERS)) + "|\n")


def print_report_row(row_local):
    f.write("|" + "|".join(row_local) + "|\n")


# Open file for report.
base_folder = "Report"
f = open(f"{base_folder}/report.md", "w")

sonar_rules = etree.parse(boomi_cicd.SONAR_RULES_FILE)

print_report_head()
rules_count = len(sonar_rules.xpath("/profile/rules/rule"))
h = 0
for root, _, filenames in os.walk(base_folder):
    for filename in filenames:
        if filename.endswith(".xml"):
            component_file = os.path.join(root, filename)
            component_tree = etree.parse(component_file)
            component_root = component_tree.getroot()
            component_id = component_root.attrib["componentId"]
            component_name = component_root.attrib["name"]
            component_version = component_root.attrib["version"]
            component_type = component_root.attrib["type"]

            for i in range(1, rules_count + 1):
                xpath = f"/profile/rules/rule[{i}]/parameters/parameter[key='expression']/value"
                expressions = sonar_rules.xpath(xpath)

                for expression in expressions:
                    component_validation = component_tree.xpath(
                        expression.text, namespaces=boomi_cicd.NAMESPACES
                    )
                    if component_validation:
                        export_violations_found = True
                        v_priority = sonar_rules.xpath(
                            f"/profile/rules/rule[{i}]/priority/text()"
                        )[0]
                        v_type = sonar_rules.xpath(
                            f"/profile/rules/rule[{i}]/type/text()"
                        )[0]
                        v_name = sonar_rules.xpath(
                            f"/profile/rules/rule[{i}]/description/text()"
                        )[0]
                        h += 1
                        # TODO: Make Component Name a link to the component XML in the report
                        row = [
                            str(h),
                            f"[{component_name}]({component_file})",
                            component_id,
                            component_version,
                            str(component_type),
                            str(v_name),
                            str(v_type),
                            str(v_priority),
                        ]
                        print_report_row(row)

f.close()

commit_and_push (repo)

logger = logging.getLogger(__name__)

#Temporary
def get_packaged_component(packaged_component_id):
    """
    Get a packaged component.

    :param packaged_component_id: The ID of the packaged component.
    :type packaged_component_id: str
    :return: The packaged component details.
    :rtype: dict
    """
    resource_path = f"/PackagedComponent/{packaged_component_id}"
    response = boomi_cicd.requests_get(resource_path)
    return response.json()
#Temporary

# Read release data
releases = boomi_cicd.set_release()

# Extract all folder paths into a set using Boomi API to get the XML
fullfolderpaths = set()

for release in releases["pipelines"]:
    packaged_component_id = "4bb49b73-9dd9-4e4c-a482-ceb774c03763"
    package = get_packaged_component(packaged_component_id)
    component_id = package.get("componentId")
    componentxml = boomi_cicd.query_component(component_id)

    # Parse the XML string
    root = ET.fromstring(componentxml)
    folder_path = root.attrib.get("folderFullPath")
    
    if folder_path:
        fullfolderpaths.add(f"/{folder_path}/")

# Check report file
report_path = "Report/report.md"

with open(report_path, "r") as f:
    for line in f:
        for folder_path in fullfolderpaths:
            if folder_path in line and "BUG" in line:
                # Ensure folder_path is the only path-like element in the line
                if line.count("/") == folder_path.count("/"):
                    logger.error("Bug detected in report.md for a component inside a tracked folder. Stopping deployment.")
                    sys.exit(1)

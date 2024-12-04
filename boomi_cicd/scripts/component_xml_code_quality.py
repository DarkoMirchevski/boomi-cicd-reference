import os
import boomi_cicd
from boomi_cicd import logger
from lxml import etree
import subprocess
from git import Repo
from boomi_cicd import logger

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
base_folder = boomi_cicd.COMPONENT_REPO_NAME
report_path = f"{base_folder}/report.md"
f = open(report_path, "w")

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
            logger.info(f"component_file: {component_file}")
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

# Print the report to the console
with open(report_path, "r") as report_file:
    print(report_file.read())

# GitHub integration
def commit_and_push_file(repo_path, file_path, commit_message="Updated report.md"):
    """
    Commit and push a single file to the GitHub repository.

    :param repo_path: Path to the local repository.
    :param file_path: Path to the file to commit, relative to the repository root.
    :param commit_message: Commit message. Defaults to "Updated report.md".
    :return: None
    """
    try:
        # Open the repository
        repo = Repo(repo_path)
        
        # Stage the specific file
        repo.git.add(file_path)
        
        # Create a commit
        logger.info(f"Committing changes with message: {commit_message}")
        repo.index.commit(commit_message)
        
        # Push changes to the remote repository
        origin = repo.remote(name="origin")
        logger.info(f"Pushing changes to the remote repository: {origin.url}")
        origin.push()
        
    except Exception as e:
        logger.error(f"An error occurred during commit and push: {e}")
        raise

repo_path = "/Das/report"  # Path to your local Git repository
commit_message = "Updated the report.md with the latest results"
commit_and_push_file(repo_path, report_path, commit_message)

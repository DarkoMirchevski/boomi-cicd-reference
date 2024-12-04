import os

import boomi_cicd
from boomi_cicd import logger
from git import Repo  # Import GitPython for managing the repository
from lxml import etree

# Added START
def add_report_to_repository(repo_path, report_file, commit_message="Added report.md"):
    """
    Add the report.md file to the GitHub repository.
    
    :param repo_path: Path to the cloned Git repository.
    :param report_file: Path to the report.md file.
    :param commit_message: Commit message for the changes.
    """
    try:
        # Initialize the repository object
        repo = Repo(repo_path)
        
        # Add the report.md file
        repo.index.add([report_file])
        logger.info(f"Staged {report_file} for commit.")
        
        # Commit the changes
        repo.index.commit(commit_message)
        logger.info(f"Committed changes with message: {commit_message}")
        
        # Push to the remote repository
        repo.remote("origin").push()
        logger.info("Changes pushed to the repository.")
        
    except Exception as e:
        logger.error(f"Failed to add report.md to the repository: {e}")


# Main script logic
base_folder = boomi_cicd.COMPONENT_REPO_NAME  # Base folder for the repository
report_file = os.path.join(base_folder, "report.md")  # Path to the generated report.md

# Generate the report file (reuse the provided logic)
f = open(report_file, "w")
print_report_head()

#Added END

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
            #TODO
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
# Add the report to the repository
add_report_to_repository(base_folder, report_file)

with open(f"{base_folder}/report.md", "r") as report_file:
    print(report_file.read())

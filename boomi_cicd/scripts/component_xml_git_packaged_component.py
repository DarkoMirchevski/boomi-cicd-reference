import logging
import boomi_cicd
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.DEBUG)


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

packaged_component_id = "c52b35c5-3a74-4e67-88b9-ba80c1ff840f"
package = get_packaged_component(packaged_component_id)

logging.info(f"Retrieved package: {package}")

component_id = package.get("componentId")
print(f"Component ID: {component_id}")


componentxml = boomi_cicd.query_component(component_id)
print(f"Compnent XML: {componentxml}")


# Clone repo
repo = boomi_cicd.clone_repository()

# Get parent folder name and component ID mapping
file_components = boomi_cicd.get_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME)

# Open release json
releases = boomi_cicd.set_release()

# Process each release to update the Git repository with the component XMLs
for release in releases["pipelines"]:
    print("packageVersion:", package.get("packageVersion"))
    release["packageVersion"] = package.get("packageVersion")

    print("componentId:", package.get("componentId"))
    release["componentId"] = package.get("componentId")

    # Parse the XML string
    root = ET.fromstring(componentxml)
    
    # Find the 'name' attribute in the component XML
    processName = root.attrib.get('name')
    folderFullPath = root.attrib.get('folderFullPath')
    print("Process name:", processName)
    print("folderFullPath:", folderFullPath)

    release["processName"] = processName

    print("packageVersion:", package.get("packageVersion"))
    release["packageVersion"] = package.get("packageVersion")
    release["folderFullPath"] = folderFullPath
    boomi_cicd.process_git_release(repo, file_components, release)

# Save the updated component references
boomi_cicd.set_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME, file_components)

# Commit and push changes
boomi_cicd.commit_and_push(repo)

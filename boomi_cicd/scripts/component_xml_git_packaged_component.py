import logging
import boomi_cicd
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Clone repo
repo = boomi_cicd.clone_repository()

# Get parent folder name and component ID mapping
file_components = boomi_cicd.get_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME)

# Open release json
releases = boomi_cicd.set_release()

# Process each release to update the Git repository with the component XMLs
for release in releases["pipelines"]:
    package = boomi_cicd.get_packaged_component(release["packageId"])
    component_id = package.get("componentId")
    componentxml = boomi_cicd.query_component(component_id)
    release["packageVersion"] = package.get("packageVersion")
    release["componentId"] = package.get("componentId")

    # Parse the XML string
    root = ET.fromstring(componentxml)
    
    # Find the 'name' attribute in the component XML
    processName = root.attrib.get('name')
    folderFullPath = root.attrib.get('folderFullPath')
    release["processName"] = processName
    release["packageVersion"] = package.get("packageVersion")
    release["folderFullPath"] = folderFullPath
    boomi_cicd.process_git_release(repo, file_components, release)

# Save the updated component references
boomi_cicd.set_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME, file_components)

# Commit and push changes
boomi_cicd.commit_and_push(repo)

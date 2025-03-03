import boomi_cicd
from boomi_cicd import logger
import uuid  # Import UUID to generate unique IDs

# Open release json
releases = boomi_cicd.set_release()

# List to store packaged component IDs for later deletion
package_ids = []

# Create a dictionary to map process names to unique IDs
release_unique_ids = {}

# For each release in the pipelines, create a packaged component
for release in releases["pipelines"]:
    process_name = release["processName"]
    component_id = release["componentId"]
    automated_test_component_id = release["automatedTestId"]
    package_version = release["packageVersion"] + "-CODEVALIDATION"
    notes = release.get("notes")
    
    # Generate a unique UUID for this release
    unique_id = str(uuid.uuid4())
    release_unique_ids[process_name] = unique_id  # Store the unique ID based on process name
    
    # Append the unique ID to the package version
    package_version_with_unique_id = f"{package_version}-{unique_id}"

    # Create the packaged component for this release and store its package ID
    package_id = boomi_cicd.create_packaged_component(component_id, package_version_with_unique_id, notes)
    package_ids.append(package_id)

# Clone repo
repo = boomi_cicd.clone_repository()

# Get parent folder name and component ID mapping
file_components = boomi_cicd.get_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME)

# Process each release to update the Git repository with the component XMLs
for release in releases["pipelines"]:
    # Get the unique ID from the mapping and append it to packageVersion for each release
    unique_id = release_unique_ids[release["processName"]]  # Retrieve the same unique ID
    release["packageVersion"] = f"{release['packageVersion']}-CODEVALIDATION-{unique_id}"
    
    boomi_cicd.process_git_release(repo, file_components, release)

# Save the updated component references
boomi_cicd.set_component_xml_file_refs(boomi_cicd.COMPONENT_REPO_NAME, file_components)

# Commit and push changes
boomi_cicd.commit_and_push(repo)

# Delete each packaged component created
for package_id in package_ids:
    resource_path = f"/PackagedComponent/{package_id}"
    boomi_cicd.requests_delete(resource_path)

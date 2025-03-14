
import boomi_cicd


# Open release json
releases = boomi_cicd.set_release()

environment_id = boomi_cicd.query_environment(boomi_cicd.ENVIRONMENT_NAME)
atom_id = boomi_cicd.query_atom(boomi_cicd.ATOM_NAME)

for release in releases["pipelines"]:
    process_name = release["processName"]
    component_id = release["componentId"]
    automated_test_component_id = release["automatedTestId"]
    package_version = release["packageVersion"]
    notes = release.get("notes")
    package_id = ("packageId")

    automated_test_package_id = boomi_cicd.create_packaged_component(
        automated_test_component_id, package_version, notes
    )

    # Deploy the automated test harness
    automated_test_deploymentId = boomi_cicd.create_deployed_package(
        release, automated_test_package_id, environment_id
    )

    # Execute the test process
    request_id = boomi_cicd.create_execution_request(
        atom_id, automated_test_component_id
    )

    # Check the completed status. Anything other than COMPLETE means it did not pass.
    execution_response = boomi_cicd.get_completed_execution_status(request_id)

    # Raise an exception if the status of the execution is anything other than COMPLETE
    if execution_response["status"] != "COMPLETE":
        raise AssertionError(
            f"Automation test for {process_name}. Error message: {execution_response['message']}"
        )

    boomi_cicd.create_deployed_package(release, package_id, environment_id)

    boomi_cicd.delete_deployed_package(automated_test_deploymentId)

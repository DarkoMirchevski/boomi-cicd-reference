import json

import boomi_cicd
import boomi_cicd.util.json.packaged_component
from boomi_cicd import logger


# https://help.boomi.com/bundle/developer_apis/page/r-atm-Packaged_Component_object.html


def create_packaged_component(component_id, package_version, notes):
    """
    Create a packaged component.

    :param component_id: The ID of the component.
    :type component_id: str
    :param package_version: The version of the package.
    :type package_version: str
    :param notes: Additional notes for the package.
    :type notes: str
    :return: The ID of the created package.
    :rtype: str
    """
    resource_path = "/PackagedComponent"

    payload = boomi_cicd.util.json.packaged_component.create()
    payload["componentId"] = component_id
    payload["packageVersion"] = package_version
    payload["notes"] = notes

    response = boomi_cicd.requests_post(resource_path, payload)

    package_id = json.loads(response.text)["packageId"]
    return package_id


def query_packaged_component(component_id, package_version):
    """
    Query the packaged component to check if it has already been created.

    :param component_id: The ID of the component.
    :type component_id: str
    :param package_version: The version of the package.
    :type package_version: str
    :return: The ID of the existing package, or an empty string if not found.
    :rtype: str
    """
    resource_path = "/PackagedComponent/query"

    logger.info(f"ComponentId: {component_id}")
    logger.info(f"PackagedVersion: {package_version}")

    payload = boomi_cicd.util.json.packaged_component.query()
    payload["QueryFilter"]["expression"]["nestedExpression"][0]["argument"][
        0
    ] = component_id
    payload["QueryFilter"]["expression"]["nestedExpression"][1]["argument"][
        0
    ] = package_version

    response = boomi_cicd.requests_post(resource_path, payload)

    package_id = ""
    if json.loads(response.text)["numberOfResults"] > 0:
        logger.info(
            f"Packaged component has already been created. ComponentId: {component_id}, PackageId: {package_version}"
        )
        package_id = json.loads(response.text)["result"][0]["packageId"]

    return package_id


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

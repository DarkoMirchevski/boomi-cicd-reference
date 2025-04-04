import logging
import boomi_cicd


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

packaged_component_id = "4bb49b73-9dd9-4e4c-a482-ceb774c03763"
package = get_packaged_component(packaged_component_id)

logging.info(f"Retrieved package: {package}")

component_id = package.get("componentId")
print(f"Component ID: {component_id}")


componentxml = boomi_cicd.query_component(component_id)
print(f"Compnent XML: {componentxml}")

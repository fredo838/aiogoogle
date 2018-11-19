import pytest

from aiogoogle import DiscoveryClient
from aiogoogle.method import PRESERVED_KEYWORDS
from ..globals import SOME_APIS
from jsonschema import Draft4Validator, Draft3Validator

@pytest.mark.parametrize('name,version', SOME_APIS)
def test_parameters_not_included_twice(open_discovery_document, name, version):
    ''' 
    I was curious whether global parameters might have identical names
    to ResourceMethod.parameters.
    Fails if collision found
    '''
    discovery_document = open_discovery_document(name, version)
    client = DiscoveryClient(discovery_document=discovery_document)
    for resource_name, _ in discovery_document.get('resources').items():
        resource = getattr(client.resources, resource_name)
        for method_name in resource.methods:
            resource_method = getattr(resource, method_name)
            for parameter_name, _ in resource_method._method_specs.get('parameters', {}).items():
                assert parameter_name not in resource_method._global_parameters

@pytest.mark.parametrize('name,version', SOME_APIS)
def test_schemas_adhering_jsonschema_v4(open_discovery_document, name, version):
    discovery_document = open_discovery_document(name, version)
    for _, schema in discovery_document.get('schemas', {}).items():
        Draft3Validator.check_schema(schema)


@pytest.mark.parametrize('name,version', SOME_APIS)
def test_methods_schemas_adhering_jsonschema_v4(open_discovery_document, name, version):

    def check_schema(methods):
        for _,method in methods.items():
            if method.get('parameters'):
                for _, parameter in method['parameters'].items():
                    if parameter:
                        Draft3Validator.check_schema(parameter)

    def resolve_resource(resource):
        if resource.get('methods'):
            check_schema(resource['methods'])
        if resource.get('resources'):
            for _,resource in resource['resources'].items():
                resolve_resource(resource)

    discovery_document = open_discovery_document(name, version)
    for _, resource in discovery_document['resources'].items():
        resolve_resource(resource)



@pytest.mark.parametrize('name,version', SOME_APIS)
def test_parameters_not_colliding_with_resource_method__call__(open_discovery_document, name, version):
    discovery_document = open_discovery_document(name, version)
    client = DiscoveryClient(discovery_document=discovery_document)
    for resource_name, _ in discovery_document.get('resources').items():
        resource = getattr(client.resources, resource_name)
        for method_name in resource.methods:
            resource_method = getattr(resource, method_name)
            params = resource_method.parameters
            for param_name, _ in params.items():
                assert param_name not in PRESERVED_KEYWORDS


@pytest.mark.parametrize('name,version', SOME_APIS)
def test_parameters_not_colliding_with_resource_method__call__fails(open_discovery_document, name, version):
    ''' asserts previous test catches collisions if any'''

    COLLIDING_PRESERVED_KEYWORDS = ['alt', 'part']

    class CollisionError(Exception):
        pass
    
    def check_collision(param_name):
        if param_name in COLLIDING_PRESERVED_KEYWORDS:
            raise CollisionError()

    discovery_document = open_discovery_document(name, version)
    client = DiscoveryClient(discovery_document=discovery_document)
    for resource_name, _ in discovery_document.get('resources').items():
        resource = getattr(client.resources, resource_name)
        for method_name in resource.methods:
            resource_method = getattr(resource, method_name)
            params = resource_method.parameters
            with pytest.raises(CollisionError):
                for param_name, _ in params.items():
                    check_collision(param_name)

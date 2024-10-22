from typing import Annotated

import pytest
import strappy
from strappy import Container, Provider, RegistrationMode


@pytest.fixture(name="container")
def fixture_container() -> Container:
    return strappy.base.extend()


def test_resolving_respects_type_annotations(container: Container):
    container.add(
        Provider[str](instance="apple"),
        Provider[Annotated[str, "b"]](instance="banana"),
    )
    apple = container.resolve(str)

    banana = container.resolve(Annotated[str, "b"]) # pyright: ignore[reportArgumentType]

    assert apple == "apple"
    assert banana == "banana"


def test_can_resolve_subdependencies(container: Container):
    class Service:
        def __init__(self, value: str) -> None:
            self.value = value

    container.add(
        Provider[str](instance="bob"),
        Provider(Service),
    )

    service = container.resolve(Service)

    assert isinstance(service, Service)
    assert service.value == "bob"


def test_resolves_subdependency_using_annotated_type_hint(container: Container):
    class Service:
        def __init__(self, value: Annotated[str, "a"]) -> None:
            self.value = value

    container.add(
        Provider[Annotated[str, "a"]](instance="apple"),
        Provider(Service),
    )

    service = container.resolve(Service)

    assert isinstance(service, Service)
    assert service.value == "apple"


def test_resolves_subdependency_annotated_type_hint_falls_back_to_unwrapped(
    container: Container,
):
    @container.register
    class Service:
        def __init__(self, value: Annotated[str, "a"]) -> None:
            self.value = value

    container.add(Provider[str](instance="some string"))

    service = container.resolve(Service)

    assert isinstance(service, Service)
    assert service.value == "some string"


def test_resolve_list_of_registered_service(container: Container):
    class Service: ...

    container.add(
        Provider(Service),
        Provider(Service),
        mode=RegistrationMode.APPEND,
    )

    services = container.resolve(list[Service])

    assert len(services) == 2
    assert all(isinstance(service, Service) for service in services)


def test_resolve_list_of_registered_subclasses(container: Container):
    class BaseService: ...

    @container.register(provides=BaseService, mode=RegistrationMode.APPEND)
    class FooService(BaseService): ...

    @container.register(provides=BaseService, mode=RegistrationMode.APPEND)
    class BarService(BaseService): ...

    services = container.resolve(list[BaseService])

    assert len(services) == 2
    assert isinstance(services[0], FooService)
    assert isinstance(services[1], BarService)


def test_resolve_set_of_registered_service(container: Container):
    class Service: ...

    container.add(Provider(Service), mode=RegistrationMode.APPEND)
    instance = Service()
    container.add(Provider[Service](instance=instance), mode=RegistrationMode.APPEND)

    services = container.resolve(set[Service])

    assert isinstance(services, set)
    assert len(services) == 2
    assert all(isinstance(service, Service) for service in services)
    assert instance in services


def test_resolve_collection_subdependency(container: Container):
    class Handler: ...

    @container.register
    class Service:
        def __init__(self, handlers: list[Handler]) -> None:
            self.handlers = handlers

    container.add(Provider(Handler), mode=RegistrationMode.APPEND)
    container.add(Provider(Handler), mode=RegistrationMode.APPEND)

    service = container.resolve(Service)

    assert isinstance(service, Service)
    assert len(service.handlers) == 2
    assert all(isinstance(handler, Handler) for handler in service.handlers)

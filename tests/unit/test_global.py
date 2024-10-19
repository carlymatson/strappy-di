import pytest

import strappy


def test_global_inject_and_resolve():
    @strappy.base.inject
    class Service: ...

    service = strappy.base.resolve(Service)
    assert isinstance(service, Service)


def test_extend_global_keeps_registrations():
    @strappy.base.inject
    class Service: ...

    container = strappy.base.extend()
    service = container.resolve(Service)
    assert isinstance(service, Service)


def test_clearing_registrations_in_extension_does_not_affect_base():
    @strappy.base.inject
    class Service: ...

    container = strappy.base.extend()
    container.clear(Service)
    with pytest.raises(strappy.ResolutionError):
        service = container.resolve(Service)

    service = strappy.base.resolve(Service)
    assert isinstance(service, Service)


def test_overwriting_registrations_in_extension_does_not_affect_base():
    @strappy.base.inject
    class Service: ...

    container = strappy.base.extend()
    my_instance = Service()
    container.add(
        strappy.Provider[Service](instance=my_instance), mode=strappy.Mode.OVERWRITE
    )

    base_service = strappy.base.resolve(Service)
    assert isinstance(base_service, Service)
    assert base_service is not my_instance

    container_service = container.resolve(Service)
    assert isinstance(container_service, Service)
    assert container_service is my_instance

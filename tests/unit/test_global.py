import strappy


def test_global_register_and_resolve():
    @strappy.base.register
    class Service: ...

    service = strappy.base.resolve(Service)
    assert isinstance(service, Service)


def test_extend_global_keeps_registrations():
    @strappy.base.register
    class Service: ...

    container = strappy.base.extend()
    service = container.resolve(Service)
    assert isinstance(service, Service)


def test_clearing_registrations_in_extension_does_not_affect_base():
    @strappy.base.register
    class Service: ...

    container = strappy.base.extend()
    container.clear(Service)
    assert strappy.base.registry[Service]
    assert not container.registry.get(Service, None)


def test_overwriting_registrations_in_extension_does_not_affect_base():
    @strappy.base.register
    class Service: ...

    container = strappy.base.extend()
    my_instance = Service()
    container.add(
        strappy.Provider[Service](instance=my_instance),
        mode=strappy.RegistrationMode.OVERWRITE,
    )

    base_service = strappy.base.resolve(Service)
    assert isinstance(base_service, Service)
    assert base_service is not my_instance

    container_service = container.resolve(Service)
    assert isinstance(container_service, Service)
    assert container_service is my_instance

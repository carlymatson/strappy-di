from strappy import Container, Scope


def test_transient_returns_new_result():
    container = Container()

    @container.inject(scope=Scope.TRANSIENT)
    class Service: ...

    service_1 = container.resolve(Service)
    service_2 = container.resolve(Service)

    assert id(service_1) != id(service_2)


def test_singleton_returns_same_result():
    container = Container()

    @container.inject(scope=Scope.SINGLETON)
    class Service: ...

    service_1 = container.resolve(Service)
    service_2 = container.resolve(Service)

    assert id(service_1) == id(service_2)

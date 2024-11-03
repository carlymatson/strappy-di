"""End to end tests."""

from dataclasses import dataclass

import strappy


def test_complicated_example():
    @strappy.base.register(scope=strappy.Scope.SINGLETON)
    class SharedDependency: ...

    class AHandler: ...

    class BHandler: ...

    @strappy.base.register(provides=AHandler, mode=strappy.RegisterMode.APPEND)
    class AHandler1(AHandler): ...

    @strappy.base.register(provides=AHandler, mode=strappy.RegisterMode.APPEND)
    class AHandler2(AHandler): ...

    @strappy.base.register(provides=AHandler, mode=strappy.RegisterMode.APPEND)
    @strappy.base.register(provides=BHandler, mode=strappy.RegisterMode.APPEND)
    class ABHandler(AHandler, BHandler): ...

    @strappy.base.register(
        provides=BHandler,
        mode=strappy.RegisterMode.APPEND,
        scope=strappy.Scope.SINGLETON,
    )
    class BHandler1(BHandler): ...

    @strappy.base.register(provides=BHandler, mode=strappy.RegisterMode.APPEND)
    class BHandler2(BHandler): ...

    @dataclass
    class Credentials:
        username: str
        email: str

    class ServiceA:
        def __init__(
            self,
            shared: SharedDependency,
            handlers: list[AHandler],
        ) -> None:
            self.shared = shared
            self.handlers = handlers

    class ServiceB:
        def __init__(
            self,
            shared: SharedDependency,
            handlers: set[BHandler],
            credentials: Credentials | None = None,
        ) -> None:
            self.shared = shared
            self.handlers = handlers
            self.credentials = credentials

    providers = [
        strappy.Provider(
            instance=Credentials(
                username="username",
                email="email",
            ),
        ),
    ]
    container = strappy.base.extend()
    container.add(*providers)

    a_service = container.resolve(ServiceA)
    b_service = container.resolve(ServiceB)

    assert a_service.shared is b_service.shared
    assert isinstance(a_service.handlers, list)
    assert len(a_service.handlers) == 3

    assert b_service.credentials is not None
    assert b_service.credentials.username == "username"
    assert b_service.credentials.email == "email"
    assert isinstance(b_service.handlers, set)
    assert len(b_service.handlers) == 3

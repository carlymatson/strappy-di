from typing import Protocol
from unittest.mock import Mock

import pytest
from strappy import Container, Mode, Provider, Scope
from strappy.errors import RegistrationConflictError


def test_add_provider_once():
    container = Container()
    mock_provider = Mock()
    mock_provider.provides = str
    container.add(mock_provider)

    assert container.registry == {str: [mock_provider]}


def test_add_second_provider_same_key():
    container = Container()
    mock_provider = Mock()
    mock_provider.provides = str
    container.add(mock_provider)

    with pytest.raises(RegistrationConflictError):
        container.add(mock_provider)


def test_add_second_provider_with_append_mode():
    container = Container()
    mock_provider = Mock(provides=str)
    second_mock_provider = Mock(provides=str)
    container.add(mock_provider)

    container.add(second_mock_provider, mode=Mode.APPEND)

    assert container.registry == {str: [mock_provider, second_mock_provider]}


def test_add_second_provider_with_overwrite_mode():
    container = Container()
    mock_provider = Mock(provides=str)
    second_mock_provider = Mock(provides=str)
    container.add(mock_provider)

    container.add(second_mock_provider, mode=Mode.OVERWRITE)

    assert container.registry == {str: [second_mock_provider]}


def test_bare_register_calls_add_provider():
    container = Container()
    container.add = Mock()

    @container.register
    class Service: ...

    container.add.assert_called_once()
    assert len(container.add.call_args.args) == 1
    provider = container.add.call_args.args[0]
    assert isinstance(provider, Provider)
    assert provider.factory is Service
    assert provider.provides is Service
    assert provider.registration_kwargs is None
    assert provider.scope is Scope.TRANSIENT
    assert provider.instance is None


def test_registering_with_args_calls_add_provider_with_args():
    container = Container()
    container.add = Mock()

    class ServiceLike(Protocol):
        def get_foo(self) -> str: ...

    @container.register(
        provides=ServiceLike,
        kwargs={"a": 1},
        scope=Scope.SINGLETON,
        mode=Mode.OVERWRITE,
    )
    class Service:
        def get_foo(self) -> str:
            return "foo"

    container.add.assert_called_once()
    assert len(container.add.call_args.args) == 1
    provider = container.add.call_args.args[0]
    assert isinstance(provider, Provider)
    assert provider.factory is Service
    assert provider.provides is ServiceLike
    assert provider.registration_kwargs == {"a": 1}
    assert provider.scope is Scope.SINGLETON
    assert provider.instance is None
    assert container.add.call_args.kwargs["mode"] == Mode.OVERWRITE

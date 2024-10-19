import pytest
from pydantic import BaseModel

from strappy import Container
from strappy.provider import Provider


def test_can_resolve_with_kwargs():
    container = Container()

    @container.inject
    class Service:
        def __init__(self, value: int) -> None:
            self.value = value

    service = container.resolve(Service, kwargs={"value": 2})

    assert isinstance(service, Service)
    assert service.value == 2


def test_resolution_kwargs_take_precedence_over_registration():
    container = Container()

    @container.inject(kwargs={"a": 2, "b": "bobo"})
    class Service:
        def __init__(self, a: int, b: str, c: float) -> None:
            self.a = a
            self.b = b
            self.c = c

    container.add(Provider[int](instance=1))
    container.add(Provider[str](instance="bob"))
    container.add(Provider[float](instance=3.14))

    service = container.resolve(Service, kwargs={"a": 3})

    assert isinstance(service, Service)
    assert service.a == 3
    assert service.b == "bobo"
    assert service.c == 3.14


def test_can_use_default_for_unregistered_subdependencies():
    container = Container()

    @container.inject
    class Service:
        def __init__(self, value: int = 100) -> None:
            self.value = value

    service = container.resolve(Service)

    assert isinstance(service, Service)
    assert service.value == 100


def test_default_fields_are_not_passed_explicitly():
    container = Container()

    @container.inject
    class Person(BaseModel):
        name: str
        age: int = 0

    container.add(Provider[str](instance="carly"))

    person = container.resolve(Person)

    assert isinstance(person, Person)
    assert person.name == "carly"
    assert person.age == 0
    assert person.model_fields_set == {"name"}


# TODO Could use better clarity on this one
def test_can_call_function_with_container_context():
    container = Container()

    def my_function(a: int, b: str, c: bool = False) -> str:
        return f"{a} {b} {c}"

    container.add(Provider[int](instance=33))
    container.add(Provider[str](factory=lambda: "carly"))

    result = container.call(my_function, kwargs={"b": "carlita"})

    assert result == "33 carlita False"


def test_positional_only_and_keyword_only_args():
    container = Container()

    def add_integers(a: int, /, *, b: int = 10) -> int:
        return a + b

    result = container.call(add_integers, kwargs={"a": 1, "b": 2})

    assert result == 3


def test_unknown_args_raise_type_error():
    container = Container()

    def identity(a: int) -> int:
        return a

    with pytest.raises(TypeError):
        container.call(identity, kwargs={"a": 1, "b": 2})


def test_variable_posargs_and_kwargs():
    container = Container()

    def f(a: int, *args, b: int = 10, **kwargs) -> tuple[int, int, tuple, dict]:
        return a, b, args, kwargs

    a, b, args, kwargs = container.call(f, kwargs={"a": 1, "b": 2, "c": 3})

    assert a == 1
    assert b == 2
    assert args == ()
    assert kwargs == {"c": 3}

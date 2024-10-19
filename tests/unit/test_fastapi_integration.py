from typing import Annotated

from fastapi import Depends

from strappy import Container


def test_resolve_annotated_depends():
    container = Container()

    def get_foo() -> str:
        return "foo"

    def build_thing(foo: Annotated[str, Depends(get_foo)]):
        return "wrapped " + foo

    result = container.call(build_thing)
    assert result == "wrapped foo"


def test_resolve_default_depends():
    container = Container()

    def get_foo() -> str:
        return "foo"

    def build_thing(foo: str = Depends(get_foo)):
        return "wrapped " + foo

    result = container.call(build_thing)
    assert result == "wrapped foo"

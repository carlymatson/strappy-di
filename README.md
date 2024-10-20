
# Project Description

Strappy is a light, flexible, and pythonic dependency injection framework.  
It combines an intuitive API with robust and convenient features:
- No external dependencies
- Integrates with FastAPI out of the box
- Helpful and accurate type annotations
- Default functionality that covers the vast majority of use cases, and easy customization for the rest

# Installing

Strappy is available on [PyPI](https://pypi.org/project/strappy-di/0.1.0/).
```
python -m pip install strappy-di
```

# Quick Start

Strappy makes it easy to bootstrap your application by 
recursively resolving dependencies for any callable.
```
import strappy

class Client:
    ...

class Service:
    def __init__(self, client: Client) -> None:
        self.client = client

service = strappy.base.resolve(Service)
```
Strappy works by using _strategies_ to look up _providers_ within the context of a given _container_.
Providers fulfill your dependencies either by returning a registered instance or by 
calling a factory, which can itself recursivley resolve dependencies from the container's context.

# Using Containers

Strappy provides a global base container `strappy.base` that can be used to register and resolve shared needs.
This base container can also be extended to define
different contexts for different use cases, such as
having one for your deployed service and another for unit tests.
```
import strappy

deployment_container = strappy.base.extend()
test_container = strappy.base.extend()
```
Any changes to the base container will be reflected in its 
children unless explicitly overridden, but changes
to child containers do not affect their parents or siblings.

# Registering Providers

A `Provider` can fulfill a dependency either by returning 
an instance or by returning the result of calling
a factory.
```
from strappy import Provider

class Foo:
    ...

# Provider with an instance
Provider(instance=Foo(...))

# Provider with a factory class
Provider(Foo)

# Provider with a factory function
Provider(lambda: Foo(...))
```
Providers that use factories can also be configured with 
arguments and a scope that allows you to cache and reuse the result.

The return type of a provider determines how it is looked
up in a container's registry. This type can usually be 
inferred from its factory or instance, but in some cases
it can be useful to set this explicitly. 
This value can be used by type checkers to ensure that the 
provider's factory or instance is of the expected type.
```
from typing import Protocol

class FooLike(Protocol):
    ...

provider_1 = Provider[FooLike](...)
provider_2 = Provider(..., provides=FooLike)
```

These providers can be added to a container and will then be available in its registry.
```
container.add(provider_1)

container.registry # {FooLike: [provider_1]}
```
Strappy also exposes a decorator syntax for registering factories.
```
@container.register
class Service:
    ...

@container.register
def get_service() -> Service:
    ...
```

# Customizing Strategies

Strappy gives you full control over your container's strategies and their precedence.
It comes with a number of pre-defined strategies for common use cases, 
such as using a FastAPI-style dependency, looking 
up a registered provider by type, and using a type annotation as a factory class. 
But it is also easy to use custom strategies by passing in any callable
that accepts a parameter and a container and optionally returns a provider.
```
def my_custom_strategy(param: inspect.Parameter, container: ContainerLike) -> Provider | None:
    ...
```

# Project Description

Strappy is a light, flexible, and pythonic dependency injection framework.  
Inspired by libraries like `Punq`, Strappy combines an easy-to-understand API with robust and convenient features
and accurate, specific type annotations.

# Installation

Strappy is available on the cheese shop.
```
pip install strappy-di
```
(#) Documentation is available on Read the docs.

# Quick Start

Strappy allows you to provide and recursively resolve dependencies for callables by registering Providers within the context of a given Container.
Providers return a result either by calling a factory, which may be a type or any callable that returns that type, or by returning a provided instance.
```
from strappy import Provider

class Service:
    ...

def get_service() -> Service:
    return Service()

service_provider_1 = Provider(Service)
service_provider_2 = Provider(get_service)
service_provider_3 = Provider(instance=Service())
```
These providers may then be added to a container using `container.add`:
```
from strappy import Container, Provider

class Service:
    ...

container = Container()
container.add(Provider(Service))
```
Providers can also be simultaneously created and added by using a decorator syntax:
```
from strappy import Container

container = Container()

@container.inject
class Service:
    ...

@container.inject
def get_service() -> Service:
    ...

@container.inject(...)
class get_service_2() -> Service:
    ...
```
If provided, the 'type' of a provider will be determined by:
- The `provides` argument
- The parametrized type of `Provider[...]`

Otherwise, the provider's type will be determined using the following:
- Class factory: the class type
- Callable Factory: the return type of that callable
- Instance: the type of that instance

We can now resolve any registered dependencies from the container:
```
service = container.resolve(Service)
```
If a provider factory takes arguments, we can take these from arguemnts provided at resolution or registration or resolved from the container using the types of parameters in the function signature.
(See ... for more)
```
container.resolve(Service)
container.resolve(Service, args=(...), wargs={...}, mode=...)
```
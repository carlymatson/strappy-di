from unittest.mock import Mock

import strappy


def test_child_has_parents_registrations():
    parent = strappy.Container()
    mock_str_provider = Mock(provides=str)
    mock_int_provider = Mock(provides=int)

    parent.add(mock_str_provider)
    child = parent.extend()
    assert child.registry == {str: [mock_str_provider]}

    parent.add(mock_int_provider)
    assert child.registry == {
        str: [mock_str_provider],
        int: [mock_int_provider],
    }


def test_child_registry_overrides_parents():
    parent = strappy.Container()
    child = parent.extend()
    sibling = parent.extend()
    mock_provider_1 = Mock(provides=str)
    mock_provider_2 = Mock(provides=str)

    parent.add(mock_provider_1)
    assert child.registry == {str: [mock_provider_1]}

    child.add(mock_provider_2)

    assert child.registry == {str: [mock_provider_2]}

    # Parents and siblings are not affected
    assert parent.registry == {str: [mock_provider_1]}
    assert sibling.registry == {str: [mock_provider_1]}

    child.clear(str)
    assert child.registry == {str: []}

    # Once again, parents and siblings are not affected
    assert parent.registry == {str: [mock_provider_1]}
    assert sibling.registry == {str: [mock_provider_1]}

    child.unset(str)
    assert child.registry == {str: [mock_provider_1]}

    # Changes to the parent are propagated
    parent.unset(str)
    assert child.registry == {}

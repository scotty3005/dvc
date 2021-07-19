# pylint: disable=unidiomatic-typecheck
from mock import create_autospec

from dvc.utils.collections import apply_diff, chunk_dict, validate


class MyDict(dict):
    pass


class MyInt(int):
    pass


def test_apply_diff_is_inplace():
    dest = MyDict()
    dest.attr = 42  # pylint: disable=attribute-defined-outside-init
    apply_diff({}, dest)

    assert type(dest) is MyDict, "Preserves class"
    assert dest.attr == 42, "Preserves custom attrs"


def test_apply_diff_mapping():
    src = {"a": 1}
    dest = {"b": 2}
    apply_diff(src, dest)
    assert dest == src, "Adds and removes keys"

    src = {"a": 1}
    dest = {"a": MyInt(1)}
    apply_diff(src, dest)
    assert type(dest["a"]) is MyInt, "Does not replace equals"

    src = {"d": {"a": 1}}
    inner = {}
    dest = {"d": inner}
    apply_diff(src, dest)
    assert dest["d"] is inner, "Updates inner dicts"


def test_apply_diff_seq():
    src = [1]
    dest = [MyInt(1)]
    apply_diff(src, dest)
    assert type(dest[0]) is MyInt, "Does not replace equals"

    src = {"l": [1]}
    inner = []
    dest = {"l": inner}
    apply_diff(src, dest)
    assert dest["l"] is inner, "Updates inner lists"


def test_chunk_dict():
    assert chunk_dict({}) == []

    d = {"a": 1, "b": 2, "c": 3}
    assert chunk_dict(d) == [{"a": 1}, {"b": 2}, {"c": 3}]
    assert chunk_dict(d, 2) == [{"a": 1, "b": 2}, {"c": 3}]
    assert chunk_dict(d, 3) == [d]
    assert chunk_dict(d, 4) == [d]


# pylint: disable=unused-argument


def _test_func(x, y, *args, j=3, k=5, **kwargs):
    pass


def test_pre_validate_decorator_required_args(mocker):
    mock = mocker.MagicMock()

    func_mock = create_autospec(_test_func)
    func = validate(mock)(func_mock)

    func("x", "y")

    func_mock.assert_called_once_with("x", "y", j=3, k=5)
    mock.assert_called_once()

    (args,) = mock.call_args[0]
    assert args.x == "x"
    assert args.y == "y"
    assert args.args == ()
    assert args.j == 3
    assert args.k == 5
    assert args.kwargs == {}


def test_pre_validate_decorator_kwargs_args(mocker):
    mock = mocker.MagicMock()
    func_mock = create_autospec(_test_func)
    func = validate(mock)(func_mock)

    func("x", "y", "part", "of", "args", j=1, k=10, m=100, n=1000)

    func_mock.assert_called_once_with(
        "x", "y", "part", "of", "args", j=1, k=10, m=100, n=1000
    )
    mock.assert_called_once()
    (args,) = mock.call_args[0]
    assert args.x == "x"
    assert args.y == "y"
    assert args.args == ("part", "of", "args")
    assert args.j == 1
    assert args.k == 10
    assert args.kwargs == {"m": 100, "n": 1000}


def test_pre_validate_update_args():
    def test_validator(args):
        args.w += 50
        del args.x
        args.y = 100

    def test_func(w=1, x=5, y=10, z=15):
        pass

    mock = create_autospec(test_func)
    func = validate(test_validator)(mock)

    func(100, 100)
    mock.assert_called_once_with(w=150, y=100, z=15)


def test_post_validate_decorator(mocker):
    def none_filter(result):
        return list(filter(None, result))

    test_func = mocker.MagicMock(return_value=[1, None, 2])
    func = validate(none_filter, post=True)(test_func)

    result = func()
    test_func.assert_called_once()
    assert result == [1, 2]

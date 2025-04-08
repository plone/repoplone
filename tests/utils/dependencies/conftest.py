from _pytest.fixtures import SubRequest
from hashlib import md5

import pytest


@pytest.fixture
def default_cassette_name(request: SubRequest) -> str:
    marker = request.node.get_closest_marker("default_cassette")
    if marker is not None:
        assert marker.args, (
            "You should pass the cassette name as an argument to the "
            "`pytest.mark.default_cassette` marker"
        )
        return marker.args[0]
    if request.cls:
        name = f"{request.cls.__name__}.{request.node.name}"
    else:
        kw = request.node.callspec.params
        match orig_name := request.node.originalname:
            case "test_get_remote_uv_dependencies":
                url_hash = md5(
                    kw["url"].encode("utf-8"), usedforsecurity=False
                ).hexdigest()
                name = f"{orig_name}-{url_hash}"
            case "test_get_package_constraints":
                name = f"{orig_name}-{kw['core_package']}-{kw['core_package_version']}"
            case _:
                name = request.node.name
    for ch in r"<>?%*:|\"'/\\":
        name = name.replace(ch, "-")
    return name

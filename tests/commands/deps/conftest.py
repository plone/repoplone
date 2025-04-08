from _pytest.fixtures import SubRequest

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
        orig_name = request.node.originalname
        if orig_name.startswith("test_deps_"):
            version = kw.get("version", kw.get("current_version", "--"))
            name = f"{orig_name}-{kw['in_package_name']}-{version}"
        else:
            name = request.node.name
    for ch in r"<>?%*:|\"'/\\":
        name = name.replace(ch, "-")
    return name


@pytest.fixture
def pyproject_toml_plone(test_public_project):
    return test_public_project / "backend" / "pyproject.toml"


@pytest.fixture
def pyproject_toml_dist(test_internal_project_from_distribution):
    return test_internal_project_from_distribution / "backend" / "pyproject.toml"


@pytest.fixture
def in_pyproject_toml(
    request, test_public_project, test_internal_project_from_distribution, monkeypatch
):
    if request.param == "plone":
        path = test_public_project
    elif request.param == "dist":
        path = test_internal_project_from_distribution
    monkeypatch.chdir(path)
    return path / "backend" / "pyproject.toml"


@pytest.fixture
def in_package_name(request):
    if request.param == "plone":
        return "Products.CMFPlone"
    elif request.param == "dist":
        return "kitconcept.intranet"


@pytest.fixture
def in_latest_version(request):
    if request.param == "plone":
        return "6.1.1"
    elif request.param == "dist":
        return "1.0.0a17"


TEST_DATA = {
    "test_deps_info": {
        "argnames": "in_package_name,in_pyproject_toml,expected",
        "packages": {
            "plone": ["Products.CMFPlone"],
            "dist": ["kitconcept.intranet"],
        },
    },
    "test_deps_check": {
        "argnames": "in_package_name,in_pyproject_toml,current_version,in_latest_version",  # noQA: E501
        "packages": {
            "plone": ["6.0.13", "6.1.0a1", "6.1.0a2"],
            "dist": ["1.0.0a12", "1.0.0a13", "1.0.0a15"],
        },
    },
    "test_deps_upgrade": {
        "argnames": "in_package_name,in_pyproject_toml,version",
        "packages": {
            "plone": ["6.1.0rc1", "6.1.0"],
            "dist": ["1.0.0a12", "1.0.0a13", "1.0.0a15"],
        },
    },
}


def pytest_generate_tests(metafunc):
    func_name = metafunc.function.__name__
    if func_name in TEST_DATA:
        argnames = TEST_DATA[func_name]["argnames"]
        total_args = len(argnames.split(","))
        indirect = [arg for arg in argnames.split(",") if arg.startswith("in_")]
        args = []
        for package, values in TEST_DATA[func_name]["packages"].items():
            for value in values:
                params = [package, package, value]
                if len(params) < total_args:
                    params.append(package)
                args.append(params)
        metafunc.parametrize(argnames, args, indirect=indirect)

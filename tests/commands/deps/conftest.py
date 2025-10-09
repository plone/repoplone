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
def in_patch_sync(monkeypatch):
    from repoplone.commands import dependencies

    def func(*args, **kwargs):
        return None

    monkeypatch.setattr(dependencies, "_sync_dependencies", func)


@pytest.fixture
def in_project_path(
    request, test_public_project, test_internal_project_from_distribution, monkeypatch
):
    path = test_public_project
    if request.param == "dist":
        path = test_internal_project_from_distribution
    monkeypatch.chdir(path)
    return path


@pytest.fixture
def in_pyproject_toml(request, in_pyproject_path):
    return in_pyproject_path / "backend" / "pyproject.toml"


@pytest.fixture
def in_mrs_developer_json(
    request, test_public_project, test_internal_project_from_distribution, monkeypatch
):
    path = test_public_project
    if request.param == "dist":
        path = test_internal_project_from_distribution
    monkeypatch.chdir(path)
    return path / "frontend" / "mrs.developer.json"


@pytest.fixture
def in_package_json(
    request, test_public_project, test_internal_project_from_distribution, monkeypatch
):
    path = test_public_project
    if request.param == "dist":
        path = test_internal_project_from_distribution
    monkeypatch.chdir(path)
    return path / "frontend" / "packages" / "fake-project" / "package.json"


@pytest.fixture
def in_package_name(request):
    if getattr(request, "param", "plone") == "plone":
        return "Products.CMFPlone"
    elif request.param == "dist":
        return "kitconcept.intranet"


@pytest.fixture
def in_latest_version(request):
    match request.param:
        case "plone":
            return {"Backend": "6.1.1", "Frontend": "16.0.2"}
        case "dist":
            return {"Backend": "1.0.0a15", "Frontend": "1.0.0-alpha.15"}


TEST_DATA = {
    "test_deps_info": {
        "argnames": "in_project_path,in_package_name,idx,title,package_name",
        "packages": {
            "plone": (
                (4, "Backend", "Products.CMFPlone"),
                (5, "Frontend", "@plone/volto"),
            ),
            "dist": (
                (4, "Backend", "kitconcept.intranet"),
                (5, "Frontend", "@kitconcept/volto-intranet"),
            ),
        },
    },
    "test_deps_check": {
        "argnames": "in_project_path,in_package_name,idx,component,package_name,current_version,latest_version",  # noQA: E501
        "packages": {
            "plone": (
                (4, "Backend", "Products.CMFPlone", "6.1.0", "6.1.3"),
                (5, "Frontend", "@plone/volto", "18.14.1", "19.0.0-alpha.6"),
            ),
            "dist": (
                (4, "Backend", "kitconcept.intranet", "1.0.0a17", "1.0.0b15"),
                (
                    5,
                    "Frontend",
                    "@kitconcept/volto-intranet",
                    "1.0.0-alpha.17",
                    "1.0.0-beta.15",
                ),
            ),
        },
    },
    "test_deps_upgrade": {
        "argnames": "in_project_path,in_package_name,in_patch_sync,component,package_name,version,expected",  # noQA: E501
        "packages": {
            "plone": (
                (
                    "backend",
                    "Products.CMFPlone",
                    "6.1.0",
                    "Products.CMFPlone (Backend) already at version 6.1.0.",
                ),
                (
                    "frontend",
                    "@plone/volto",
                    "18.14.1",
                    "@plone/volto (Frontend) already at version 18.14.1.",
                ),
                (
                    "backend",
                    "Products.CMFPlone",
                    "latest",
                    "Upgrade Products.CMFPlone (Backend) from 6.1.0 to 6.1.3",
                ),
                (
                    "frontend",
                    "@plone/volto",
                    "latest",
                    "Upgrade @plone/volto (Frontend) from 18.14.1 to 19.0.0-alpha.6",
                ),
            ),
            "dist": (
                (
                    "backend",
                    "kitconcept.intranet",
                    "1.0.0a17",
                    "kitconcept.intranet (Backend) already at version 1.0.0a17.",
                ),
                (
                    "frontend",
                    "@kitconcept/volto-intranet",
                    "1.0.0-alpha.17",
                    "@kitconcept/volto-intranet (Frontend) already at version 1.0.0-alpha.17.",  # noQA: E501
                ),
                (
                    "backend",
                    "kitconcept.intranet",
                    "latest",
                    "Upgrade kitconcept.intranet (Backend) from 1.0.0a17 to 1.0.0b15",
                ),
                (
                    "frontend",
                    "@kitconcept/volto-intranet",
                    "latest",
                    "Upgrade @kitconcept/volto-intranet (Frontend) from 1.0.0-alpha.17 to 1.0.0-beta.15",  # noQA: E501
                ),
            ),
        },
    },
}


def pytest_generate_tests(metafunc):
    func_name = metafunc.function.__name__
    if func_name in TEST_DATA:
        all_argnames = TEST_DATA[func_name]["argnames"].split(",")
        argnames = [arg for arg in all_argnames if not arg.startswith("in_")]
        total_args = len(all_argnames)
        indirect = [arg for arg in all_argnames if arg not in argnames]
        args = []
        for package, values in TEST_DATA[func_name]["packages"].items():
            for params in values:
                diff = total_args - len(params)
                for _ in range(diff):
                    params = [package, *params]
                args.append(params)
        metafunc.parametrize(all_argnames, args, indirect=indirect)

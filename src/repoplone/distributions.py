from repoplone import _types as t


PACKAGE_CONSTRAINTS: dict[str, t.PackageConstraintInfo] = {
    # Official Plone releases
    "Plone": {
        "type": "pip",
        "url": "https://dist.plone.org/release/{version}/constraints.txt",
    },
    "plone": {
        "type": "pip",
        "url": "https://dist.plone.org/release/{version}/constraints.txt",
    },
    "Products.CMFPlone": {
        "type": "pip",
        "url": "https://dist.plone.org/release/{version}/constraints.txt",
    },
    # kitconcept distributions
    "kitconcept.core": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept-core/refs/tags/{version}/backend/pyproject.toml",
    },
    "kitconcept.intranet": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept.intranet/refs/tags/{version}/backend/pyproject.toml",
    },
    "kitconcept.site": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept-website/refs/tags/{version}/backend/pyproject.toml",
        "warning": "This package is deprecated, use kitconcept.website instead.",
    },
    "kitconcept.website": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept-website/refs/tags/{version}/backend/pyproject.toml",
    },
    # Portal Brasil distributions
    "portalbrasil.core": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/core/refs/tags/{version}/backend/pyproject.toml",
    },
    "portalbrasil.devsite": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/devsite/refs/tags/{version}/backend/pyproject.toml",
    },
    "portalbrasil.intranet": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/intranet/refs/tags/{version}/backend/pyproject.toml",
    },
    "portalbrasil.legislativo": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/legislativo/refs/tags/{version}/backend/pyproject.toml",
    },
}

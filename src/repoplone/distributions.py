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
        "repository": {
            "url": "https://github.com/kitconcept/kitconcept-core",
            "subdirectory": "backend",
        },
    },
    "kitconcept.intranet": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept.intranet/refs/tags/{version}/backend/pyproject.toml",
        "repository": {
            "url": "https://github.com/kitconcept/kitconcept.intranet",
            "subdirectory": "backend",
        },
    },
    "kitconcept.website": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/kitconcept/kitconcept-website/refs/tags/{version}/backend/pyproject.toml",
        "repository": {
            "url": "https://github.com/kitconcept/kitconcept-website",
            "subdirectory": "backend",
        },
    },
    # Portal Brasil distributions
    "portalbrasil.core": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/core/refs/tags/{version}/backend/pyproject.toml",
        "repository": {
            "url": "https://github.com/portal-br/core",
            "subdirectory": "backend",
        },
    },
    "portalbrasil.devsite": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/devsite/refs/tags/{version}/backend/pyproject.toml",
        "repository": {
            "url": "https://github.com/portal-br/devsite",
            "subdirectory": "backend",
        },
    },
    "portalbrasil.intranet": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/intranet/refs/tags/{version}/backend/pyproject.toml",
        "repository": {
            "url": "https://github.com/portal-br/intranet",
            "subdirectory": "backend",
        },
    },
    "portalbrasil.legislativo": {
        "type": "uv",
        "url": "https://raw.githubusercontent.com/portal-br/legislativo/refs/tags/{version}/backend/pyproject.toml",
        "repository": {
            "url": "https://github.com/portal-br/legislativo",
            "subdirectory": "backend",
        },
    },
}

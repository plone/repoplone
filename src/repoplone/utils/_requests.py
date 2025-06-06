from repoplone import exceptions

import requests


def get_remote_data(url: str) -> requests.Response:
    """Get external data from an external url."""
    try:
        response = requests.get(url, allow_redirects=True, timeout=(5, 5))
    except requests.ConnectionError as exc:
        raise exceptions.RepoPloneExternalException(
            f"Failed to connect to {url}: {exc}"
        ) from exc
    except requests.ReadTimeout as exc:
        raise exceptions.RepoPloneExternalException(
            f"Read timeout while connecting to {url}: {exc}"
        ) from exc
    if response.status_code != 200:
        raise exceptions.RepoPloneExternalException(
            f"Failed to fetch {url}: HTTP {response.status_code}"
        )
    return response

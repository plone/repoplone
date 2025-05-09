# Changes

<!-- towncrier release notes start -->

## 1.0.0a3 (2025-05-09)


### Feature

- Add kitconcept.core to list of PACKAGE_CONSTRAINTS. @ericof [#2](https://github.com/plone/repoplone/issues/2)
- Split release sub-commands into top-level commands changelog and release. @ericof [#3](https://github.com/plone/repoplone/issues/3)
- Deprecate `managed_by_uv` setting @ericof [#6](https://github.com/plone/repoplone/issues/6)
- Implement settings command and dump sub-command. @ericof [#9](https://github.com/plone/repoplone/issues/9)
- Report version information for base_packages @ericof [#10](https://github.com/plone/repoplone/issues/10)


### Bugfix

- pyproject.toml: Keep explicit dependency version when they are declared under [dependencies] @ericof [#8](https://github.com/plone/repoplone/issues/8)


### Internal

- repository.toml: Deprecate `backend.path` and `frontend.path` settings. @ericof [#7](https://github.com/plone/repoplone/issues/7)

## 1.0.0a2 (2025-04-08)


### Bugfix

- Fix packaging issue during wheel creation. @ericof 

## 1.0.0a1 (2025-04-08)


### Feature

- Initial release @ericof

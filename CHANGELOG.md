# Changes

<!-- towncrier release notes start -->

## 1.0.0b1 (2025-10-09)


### Feature

- Update frontend package using deps upgrade command. @ericof [#4](https://github.com/plone/repoplone/issues/4)
- Update backend uv lock, and frontend lock file when running upgrade deps command. @ericof [#27](https://github.com/plone/repoplone/issues/27)
- Use uv instead of hatch to build and publish backend packages. @ericof [#28](https://github.com/plone/repoplone/issues/28)
- Add zest.pocompile as a dependency (and generate .mo files when releasing the backend). @ericof [#30](https://github.com/plone/repoplone/issues/30)
- Add support to versioning with [Calendar versioning](https://calver.org/). @ericof 
- Improve repoplone settings dump to return the backend base package version even if the package is not managed by UV. @ericof 
- Support container_images_prefix in repository.toml. @ericof 


### Internal

- Remove License classifier -- as we explicitly set it with the license setting. @ericof 
- Update typer to version 0.19.2. @ericof 

## 1.0.0a7 (2025-09-09)


### Bugfix

- Fix release command issue due to settings guessing the wrong path to the top-level towncrier.toml file when run from a subdirectory. @ericof [#24](https://github.com/plone/repoplone/issues/24)

## 1.0.0a6 (2025-09-04)


### Feature

- Add support to devsite distribution (https://github.com/portal-br/devsite). @ericof [#21](https://github.com/plone/repoplone/issues/21)
- Rename kitconcept-site distribution to kitconcept-website (https://github.com/kitconcept-website). @ericof [#22](https://github.com/plone/repoplone/issues/22)

## 1.0.0a5 (2025-06-05)


### Feature

- Support more than one compose entry. @ericof [#5](https://github.com/plone/repoplone/issues/5)
- Support passing no-plonePrePublish.publish to frontend package release. @ericof [#13](https://github.com/plone/repoplone/issues/13)
- Support new distributions `kitconcept.site`, `portalbrasil.intranet` and `portalbrasil.legislativo`. @ericof 


### Bugfix

- Handle connection issues when resolving constraints files. @ericof [#12](https://github.com/plone/repoplone/issues/12)
- Handle error when running repoplone in a subfolder of a repository. @ericof [#15](https://github.com/plone/repoplone/issues/15)

## 1.0.0a4 (2025-05-09)


### Bugfix

- Fix path to constraints for `kitconcept.core` @ericof 

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

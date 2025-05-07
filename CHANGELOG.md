# CHANGELOG

## v1.0.1 (2025-05-07)

### Changed

- Bump package version to stable.

## v1.0.0 (2025-05-07)

### Changed

- Remove support for Django 3.2 and 4.0: their `get_app_list` methods lack the optional `app_label` parameter required by this package.
- Add safeguards to prevent infinite loops in custom admin classes.

## v0.2.0 (2025-05-06)

### YANKED

- **Yanked on 2025-05-07**: this release introduced a feature incompatible with Django 3.2 and 4.0. Please upgrade to ≥ 1.0.0.

### Added

- Support to reordering and toggling visibility of apps and models in admin pages.
- Include more apps and models in the demo project.
- Add CSS variables to simplify color customization.
- Enable auto-scroll on the "Edit layout" form dialog.
- Add CHANGELOG.

### Changed

- Change license from MIT to BSD.
- Update README.
- Update E2E test to cover new features.

### Fixed

- Correct logic to pull field descriptions from the original list as a source of truth. This way, it should reflect code changes.

### Refactored

- Add singleton pattern to classes.
- Split methods into more classes and files to improve cohesion.

## v0.1.1 (2025-04-14)

### Changed

- Bump development status from `Development Status :: 3 - Alpha` to `Development Status :: 4 - Beta`.
- Improve SEO metadata in `pyproject.toml`.

## v0.1.0 (2025-04-13)

### Added

- Initial release.

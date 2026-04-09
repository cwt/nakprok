# Changelog

All notable changes to this project will be documented in this file.

The format is based on
 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
 [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2.0] - 2026-04-09

### Added for v0.2.0

- **Immutable Constants**: UPPERCASE variables are now treated as constants and
  are enforced as immutable everywhere (module, local, function parameters,
  class/function names).
- **Match Pattern Binding**: Support for variable captures in `match` patterns
  via `as` and star patterns (`[*rest]`), provided the variables are
  pre-declared with a type annotation in the current scope.

### Changed for v0.2.0

- Improved error messages for `match` pattern captures to guide users toward
  pre-declaration.
- Updated `README.md` to reflect the new immutability rules and match pattern
  support.

## [v0.1.0] - 2026-04-09

### Added for v0.1.0

- Initial release of `nakprok`.
- **Function Signature Enforcement**: Mandatory type annotations for all
  parameters and return types (except `self`/`cls`).
- **Variable Declaration Enforcement**: Mandatory type annotations for all local
  variables.
- **Control Flow Validation**: Enforcement of typed variables in `for` loops and
  `with` statements.
- **Global Constants Exemption**: Allowed UPPERCASE module-level constants
  without explicit type annotations.
- **Prohibited Features**: Blocked `lambda` functions and untyped unpacking to
  maintain strict typing.
- CLI tool for checking and running strictly typed Python files.

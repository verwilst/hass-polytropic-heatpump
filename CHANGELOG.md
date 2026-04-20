# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.1.0] - 2026-04-20

- Batch reads instead of fetching each one separately. 7+ seconds to 1 second for each fetch.
- Clean up unused files
- Fix defrost status for climate entity
- Fix order in const.py to match modbus docs
- Make update interval configurable
- Start with an empty cache
- Share device_info from coordinator
- Validate ranges, return unknown instead of out of bounds values

## [1.0.6] - 2026-04-20

- Add debug logging toggle to options flow
- Improve CRC error visibility and add write retry

## [1.0.5] - 2026-04-16

- Add coordinator lock to avoid modbus conflicts

## [1.0.4] - 2026-04-10

- Ignore occasionally failed fetch

## [1.0.3] - 2026-04-10

- Name EEV opening 2 correctly

## [1.0.2] - 2026-04-09

- Make icon backgrounds transparent

## [1.0.1] - 2026-04-09

- Fix CRC errors
- Fix brand logo location

## [1.0.0] - 2026-04-09

- Initial release
# KidsWatch for Home Assistant

Unofficial Home Assistant custom integration for KidsWatch cloud-connected watches.

> This project is community-developed and is not affiliated with, endorsed by, or supported by KidsWatch or Home Assistant.

## Features

- UI configuration through **Settings → Devices & services**
- Automatic discovery of watches associated with the configured KidsWatch account
- Home Assistant device for each watch
- GPS `device_tracker` compatible with Home Assistant maps and zones
- Battery level, daily steps, latitude, longitude, address, last-location and GPS-accuracy entities
- **Refresh position** button that requests a fresh location and waits for the cloud service to publish it
- Cloud polling every 60 seconds
- Automatic stable 32-character `m2` client identifier; no manual `m2` configuration is required
- French and English configuration translations

## Important account/session note

The KidsWatch service can invalidate an existing session when the same account signs in from another client. If the mobile application and Home Assistant repeatedly disconnect each other, use a separate KidsWatch account for Home Assistant and grant that account access to the watch using the official KidsWatch application.

## Installation with HACS

Until this repository is included in the HACS default repositories:

1. Open **HACS** in Home Assistant.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/foucteau/home-assistant-kidswatch`.
4. Select **Integration** as the category.
5. Install **KidsWatch**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add integration**.
8. Search for **KidsWatch**.
9. Enter the country calling code, phone number and password for the KidsWatch account.

## Manual installation

Copy `custom_components/kidswatch/` into `<home-assistant-config>/custom_components/kidswatch/`, restart Home Assistant, then add **KidsWatch** from **Settings → Devices & services**.

## Entities

| Entity | Description |
| --- | --- |
| Position | GPS device tracker used by maps and zones |
| Battery | Last reported battery percentage |
| Steps | Last reported daily step count |
| Latitude | Last reported latitude |
| Longitude | Last reported longitude |
| Address | Address/POI returned by KidsWatch |
| Last location | Timestamp of the last reported location |
| GPS accuracy | Accuracy radius in metres; diagnostic entity |
| Refresh position | Requests a new location from the watch |

The refresh-position command can consume more watch battery because it asks the device/cloud service for a fresh position instead of only reading the last known point.

## How location refresh works

Normal polling reads the last position known by the KidsWatch cloud. Pressing **Refresh position** sends a current-position request, then checks the last-position endpoint every 3 seconds for up to 45 seconds. Home Assistant updates as soon as a new location timestamp is returned.

## Privacy and credentials

- Credentials are entered in the Home Assistant config flow and stored by Home Assistant as config-entry data.
- The repository contains no account credentials, phone numbers, watch identifiers, GPS positions, tokens, secrets or user-specific `m2` value.
- The integration generates its `m2` identifier locally from stable characteristics of the Home Assistant host and stores the resulting identifier in the config entry.
- Production logging intentionally avoids logging credentials, tokens, raw API payloads, watch identifiers and coordinates.

## Troubleshooting

Enable debug logging for `custom_components.kidswatch` using Home Assistant's integration debug logging when investigating a problem. Before opening an issue, reproduce the problem and include the Home Assistant version, KidsWatch integration version, watch model if known, and sanitized logs. Never post passwords, tokens, secrets, phone numbers, IMEI/device identifiers or precise locations.

## Compatibility

This integration talks to the KidsWatch cloud API used by the mobile application. It is based on observed application/API behaviour and can stop working if the provider changes its private API or protocol.

## Support and bugs

Use the repository issue tracker for reproducible integration bugs and feature requests. This project cannot provide support for KidsWatch account recovery, subscriptions, SMS delivery, watch firmware or the official mobile application.

## License

MIT. See [LICENSE](LICENSE).

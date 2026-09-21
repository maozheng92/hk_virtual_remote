# HomeKit 虚拟遥控器 (Pro)

Home Assistant custom integration that exposes a virtual TV / set-top-box remote as a `media_player`, so it can be used from HomeKit and the Home Assistant UI.

Supports:

- **Phicomm** boxes (HTTP on port 8080)
- **ADB** devices (port 5555)
- **Script / action** mode (map every button to Home Assistant scripts)

## HACS install (recommended)

This repository is a HACS custom integration. It is **not** in the HACS default store, so add it as a custom repository first.

1. Open **HACS → Integrations**.
2. Open the three-dot menu → **Custom repositories**.
3. Add `https://github.com/maozheng92/hk_virtual_remote` with category **Integration**.
4. Find **HomeKit 虚拟遥控器 (Pro)** and click **Download**.
5. Restart Home Assistant.
6. Go to **Settings → Devices & Services → Add Integration** and search for **HomeKit 虚拟遥控器**.

Or use this My Home Assistant link after HACS is installed:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maozheng92&repository=hk_virtual_remote&category=integration)

Install a **GitHub Release** (for example `1.1.0` / `v1.1.0`), not a raw git commit. HACS cannot use a commit SHA such as `c745fed` as the integration version.

## Manual install

1. Copy `custom_components/hk_virtual_remote` into `<config>/custom_components/hk_virtual_remote`.
2. Restart Home Assistant.
3. Add the integration from the UI.

## Configuration

After adding the integration, choose a name, optional device IP, and control mode (Phicomm / ADB / scripts). Open the integration options to map power, navigation, volume, and source buttons.

## Releasing (maintainers)

HACS uses **GitHub Releases** as the integration version. Tags alone are not enough.

1. Keep `custom_components/hk_virtual_remote/manifest.json` `version` as the source of truth (semantic version, for example `1.1.0`).
2. After merging to `main`, create and push a matching tag:

   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

3. The [Release workflow](.github/workflows/release.yml) publishes a GitHub Release for that tag. HACS will then show `v1.1.0` instead of a commit hash.

GitHub also needs a short **repository description** and **topics** (`home-assistant`, `hacs`, `integration`, `custom-component`) for HACS default-store validation. Those are GitHub settings, not files in this repo.

## Links

- [Issues](https://github.com/maozheng92/hk_virtual_remote/issues)
- [HACS custom repository docs](https://hacs.xyz/docs/faq/custom_repositories/)

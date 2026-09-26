# HomeKit 虚拟遥控器 (Pro)

Home Assistant custom integration that exposes a virtual TV / set-top-box remote as a `media_player`, so it can be used from HomeKit and the Home Assistant UI.

Supports:

- **Phicomm** boxes (HTTP on port 8080)
- **ADB** devices (port 5555)
- **Xiaomi universal remote** via [ha_xiaomi_home](https://github.com/maozheng92/ha_xiaomi_home) (`chuangmi.ir.v2`)
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

Install a **GitHub Release** (for example `1.3.0` / `v1.3.0`), not a raw git commit. HACS cannot use a commit SHA such as `c745fed` as the integration version.

## Manual install

1. Copy `custom_components/hk_virtual_remote` into `<config>/custom_components/hk_virtual_remote`.
2. Restart Home Assistant.
3. Add the integration from the UI.

## Configuration

After adding the integration, choose a name, optional device IP, and control mode (Phicomm / ADB / Xiaomi / scripts). Open the integration options to map power, navigation, volume, and source buttons.

### Xiaomi universal remote

Requires [Xiaomi Home](https://github.com/maozheng92/ha_xiaomi_home) with the `chuangmi.ir.v2` remote imported. Learn codes first (same as Broadlink):

```yaml
action: remote.learn_command
target:
  entity_id: remote.living_room_ir
data:
  device: television
  command: power
```

Then add this integration in **小米万能遥控器** mode, pick that `remote` entity, and set **红外设备名** to the same `device` (for example `television`). Default command names:

| Button | Command |
| --- | --- |
| Power on / off | `power` |
| Up / Down / Left / Right | `up` / `down` / `left` / `right` |
| Select / Back / Menu | `select` / `back` / `menu` |
| Volume / Mute / Play | `volume_up` / `volume_down` / `mute` / `play_pause` |

Override any name under 电源/导航/音量按键. Home Assistant and the remote must be on the same LAN (UDP 54321); Docker needs host network.

In **基础设置 / Basic settings** you can also link:

- **开机实体**: optional switch / script / scene / `input_boolean` used to turn the device on
- **开关状态反馈（可选）** (`power_binary_sensor`): optional `binary_sensor` whose on/off state is the real device power (smart plug, TV power, current-clamp helper). The virtual TV follows this sensor. Leave empty to keep ping / power-sensor / optimistic state
- **功率传感器**: optional numeric power (watt) sensor as a fallback on/off heuristic
- **小米遥控实体 / 红外设备名**: used only in Xiaomi mode

## Releasing (maintainers)

HACS uses **GitHub Releases** as the integration version. Tags alone are not enough.

1. Keep `custom_components/hk_virtual_remote/manifest.json` `version` as the source of truth (semantic version, for example `1.3.0`).
2. After merging to `main`, create and push a matching tag:

   ```bash
   git tag v1.3.0
   git push origin v1.3.0
   ```

3. The [Release workflow](.github/workflows/release.yml) publishes a GitHub Release for that tag. HACS will then show `v1.3.0` instead of a commit hash.

GitHub also needs a short **repository description** and **topics** (`home-assistant`, `hacs`, `integration`, `custom-component`) for HACS default-store validation. Those are GitHub settings, not files in this repo.

## Links

- [Issues](https://github.com/maozheng92/hk_virtual_remote/issues)
- [HACS custom repository docs](https://hacs.xyz/docs/faq/custom_repositories/)

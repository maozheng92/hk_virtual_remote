import asyncio
import logging
import os
import time

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.script import Script

from .adb_utils import AdbHandler
from .const import *

_LOGGER = logging.getLogger(__name__)

BOOT_GRACE_SECONDS = 120
ACTIVE_KEY_GRACE_SECONDS = 45
ONLINE_WAIT_TIMEOUT_SECONDS = 120
ONLINE_WAIT_INTERVAL_SECONDS = 2

KEY_MAP = {
    CONF_BTN_UP: 19,
    CONF_BTN_DOWN: 20,
    CONF_BTN_LEFT: 21,
    CONF_BTN_RIGHT: 22,
    CONF_BTN_SELECT: 23,
    CONF_BTN_BACK: 4,
    CONF_BTN_INFO: 82,
    CONF_BTN_VOL_UP: 24,
    CONF_BTN_VOL_DOWN: 25,
    CONF_BTN_MUTE: 164,
    CONF_BTN_PLAY_PAUSE: 85,
    CONF_BTN_POWER_ON: 26,
    CONF_BTN_POWER_OFF: 26,
}

HK_KEY_MAP = {
    "arrow_up": CONF_BTN_UP,
    "arrow_down": CONF_BTN_DOWN,
    "arrow_left": CONF_BTN_LEFT,
    "arrow_right": CONF_BTN_RIGHT,
    "select": CONF_BTN_SELECT,
    "back": CONF_BTN_BACK,
    "information": CONF_BTN_INFO,
    "play_pause": CONF_BTN_PLAY_PAUSE,
}


def binary_sensor_means_on(state_value):
    """Return True/False for on/off, or None when unknown/unavailable."""
    if state_value in (None, STATE_UNAVAILABLE, STATE_UNKNOWN):
        return None
    if state_value == STATE_ON:
        return True
    if state_value == STATE_OFF:
        return False
    return None


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HKVirtualRemote(hass, entry)])


class HKVirtualRemote(RestoreEntity, MediaPlayerEntity):
    _attr_device_class = MediaPlayerDeviceClass.TV
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.PAUSE
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )

    def __init__(self, hass, entry):
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_has_entity_name = True
        self._attr_name = None
        self._state = MediaPlayerState.OFF
        self._current_source = None
        self._adb = None
        self._optimistic_until = 0
        self._reload()

    def _reload(self):
        self._config = {**self._entry.data, **self._entry.options}
        self._ip = self._config.get(CONF_DEVICE_IP)
        self._mode = self._config.get(CONF_MODE, MODE_ACTION)
        self._sources = self._config.get(CONF_SOURCES, [])
        self._power_on_entity = self._config.get(CONF_POWER_ON_ENTITY)
        self._power_sensor = self._config.get(CONF_POWER_SENSOR)
        self._power_binary_sensor = self._config.get(CONF_POWER_BINARY_SENSOR)

        if self._mode == MODE_ADB and self._ip:
            self._adb = AdbHandler(self.hass, self._ip)
        else:
            self._adb = None

        self._scripts = {}
        for key in KEY_MAP:
            actions = self._config.get(key, [])
            if actions:
                self._scripts[key] = Script(
                    self.hass, actions, f"{self._attr_unique_id}_{key}", DOMAIN
                )

        for src in self._sources:
            sid = src.get(CONF_SOURCE_ID)
            actions = self._config.get(sid)
            if actions and sid:
                self._scripts[sid] = Script(
                    self.hass, actions, f"{self._attr_unique_id}_{sid}", DOMAIN
                )

    def _script_context(self):
        return getattr(self, "_context", None)

    def _set_boot_grace(self, seconds=BOOT_GRACE_SECONDS):
        self._optimistic_until = max(self._optimistic_until, time.time() + seconds)
        self._state = MediaPlayerState.ON
        self.async_write_ha_state()

    async def async_update(self):
        now = time.time()

        if self._mode == MODE_ADB and self._adb:
            if not getattr(self._adb, "_available", False):
                await self._adb.connect()

        actual_on = await self._is_device_online()
        if now < self._optimistic_until:
            self._state = MediaPlayerState.ON
            return

        self._state = MediaPlayerState.ON if actual_on else MediaPlayerState.OFF

    def _binary_sensor_is_on(self):
        """Return True/False from the feedback sensor, or None if unknown."""
        entity_id = self._power_binary_sensor
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        return binary_sensor_means_on(state.state)

    def _apply_binary_sensor_state(self, is_on):
        """Follow binary_sensor as source of truth; ignore OFF during boot grace."""
        if is_on:
            self._optimistic_until = 0
            self._state = MediaPlayerState.ON
            self.async_write_ha_state()
            return
        if time.time() < self._optimistic_until:
            return
        self._state = MediaPlayerState.OFF
        self.async_write_ha_state()

    async def _is_device_online(self):
        feedback = self._binary_sensor_is_on()
        if feedback is not None:
            return feedback

        if self._power_sensor:
            p_state = self.hass.states.get(self._power_sensor)
            try:
                if p_state and float(p_state.state) > 1.5:
                    return True
            except (TypeError, ValueError):
                pass

        if self._mode == MODE_PHICOMM and self._ip:
            try:
                session = async_get_clientsession(self.hass)
                async with session.get(f"http://{self._ip}:8080/v1/status", timeout=0.5) as r:
                    return r.status == 200
            except Exception as err:
                _LOGGER.debug("斐讯状态检测失败 %s: %s", self._ip, err)

        elif self._mode == MODE_ADB and self._adb:
            return getattr(self._adb, "_available", False)

        elif self._ip:
            res = await self.hass.async_add_executor_job(
                os.system, f"ping -c 1 -W 0.5 {self._ip} > /dev/null 2>&1"
            )
            return res == 0

        return False

    async def _async_wait_until_online(self, timeout=ONLINE_WAIT_TIMEOUT_SECONDS):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if await self._is_device_online():
                return True
            await asyncio.sleep(ONLINE_WAIT_INTERVAL_SECONDS)
        return await self._is_device_online()

    async def _run(self, key):
        if not key:
            return

        if key in self._scripts:
            await self._scripts[key].async_run(context=self._script_context())
            return

        code = KEY_MAP.get(key)
        if not code:
            return

        if key not in {CONF_BTN_POWER_ON, CONF_BTN_POWER_OFF} and self._mode in {
            MODE_PHICOMM,
            MODE_ADB,
        }:
            if not await self._async_wait_until_online():
                _LOGGER.warning("设备未上线，跳过按键发送: %s key=%s", self._entry.title, key)
                return

        if self._mode == MODE_PHICOMM and self._ip:
            try:
                session = async_get_clientsession(self.hass)
                payload = {"keycode": code, "longclick": False}
                await session.post(
                    f"http://{self._ip}:8080/v1/keyevent", json=payload, timeout=2
                )
            except Exception as err:
                _LOGGER.warning("斐讯按键发送失败 %s key=%s err=%s", self._ip, key, err)

        elif self._mode == MODE_ADB and self._adb:
            await self._adb.shell(f"input keyevent {code}")

    async def _async_turn_on_power_entity(self):
        if not self._power_on_entity:
            return False

        state = self.hass.states.get(self._power_on_entity)
        if state is None:
            _LOGGER.warning("开机实体不存在: %s", self._power_on_entity)
            return False

        try:
            await self.hass.services.async_call(
                "homeassistant",
                "turn_on",
                {"entity_id": self._power_on_entity},
                blocking=True,
                context=self._script_context(),
            )
            return True
        except Exception as err:
            _LOGGER.warning("开机实体调用失败 %s: %s", self._power_on_entity, err)
            return False

    async def async_select_source(self, source):
        src = next((s for s in self._sources if s[CONF_SOURCE_NAME] == source), None)
        if not src:
            return

        sid = src.get(CONF_SOURCE_ID)
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)

        if sid in self._scripts:
            _LOGGER.debug("执行自定义源动作: %s", source)
            await self._scripts[sid].async_run(context=self._script_context())
        elif self._ip and sid:
            if self._mode in {MODE_PHICOMM, MODE_ADB} and not await self._async_wait_until_online():
                _LOGGER.warning("设备未上线，跳过输入源切换: %s source=%s", self._entry.title, source)
                return
            if self._mode == MODE_PHICOMM:
                pkg, act = sid.split("/", 1) if "/" in sid else (sid, "")
                try:
                    session = async_get_clientsession(self.hass)
                    payload = {"package": pkg, "activity": act}
                    await session.post(
                        f"http://{self._ip}:8080/v1/application", json=payload, timeout=5
                    )
                except Exception as err:
                    _LOGGER.warning("斐讯启动应用失败 %s sid=%s err=%s", self._ip, sid, err)
            elif self._mode == MODE_ADB and self._adb:
                pkg = sid.split("/")[0]
                await self._adb.shell(
                    f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
                )

        self._current_source = source
        self.async_write_ha_state()

    async def async_turn_on(self):
        actual_on = await self._is_device_online()
        self._set_boot_grace()
        if not actual_on and await self._async_turn_on_power_entity():
            return
        await self._run(CONF_BTN_POWER_ON)

    async def async_turn_off(self):
        self._optimistic_until = 0
        await self._run(CONF_BTN_POWER_OFF)
        self._state = MediaPlayerState.OFF
        self.async_write_ha_state()

    async def async_get_media_image(self):
        if self._state != MediaPlayerState.ON or self._mode != MODE_PHICOMM or not self._ip:
            return None, None
        try:
            session = async_get_clientsession(self.hass)
            async with session.get(f"http://{self._ip}:8080/v1/screenshot", timeout=3) as r:
                if r.status == 200:
                    return await r.read(), "image/jpeg"
        except Exception as err:
            _LOGGER.debug("截图获取失败 %s: %s", self._ip, err)
        return None, None

    async def async_volume_up(self):
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)
        await self._run(CONF_BTN_VOL_UP)

    async def async_volume_down(self):
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)
        await self._run(CONF_BTN_VOL_DOWN)

    async def async_mute_volume(self, mute):
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)
        await self._run(CONF_BTN_MUTE)

    async def async_media_play(self):
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)
        await self._run(CONF_BTN_PLAY_PAUSE)

    async def async_media_pause(self):
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)
        await self._run(CONF_BTN_PLAY_PAUSE)

    @property
    def state(self):
        return self._state

    @property
    def source_list(self):
        return [s[CONF_SOURCE_NAME] for s in self._sources]

    @property
    def source(self):
        return self._current_source

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._entry.title,
        )

    @callback
    def _handle_hk_event(self, event):
        if event.data.get("entity_id") != self.entity_id:
            return
        self.hass.async_create_task(self._async_handle_hk_event(event))

    async def _async_handle_hk_event(self, event):
        key_name = event.data.get("key_name")
        config_key = HK_KEY_MAP.get(key_name)
        if not config_key:
            return
        self._set_boot_grace(ACTIVE_KEY_GRACE_SECONDS)
        await self._run(config_key)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state:
            try:
                self._state = MediaPlayerState(last_state.state)
            except ValueError:
                pass

            restored_source = last_state.attributes.get("source")
            if restored_source in self.source_list:
                self._current_source = restored_source

        self.async_on_remove(
            self.hass.bus.async_listen("homekit_tv_remote_key_pressed", self._handle_hk_event)
        )
        if self._power_binary_sensor:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    [self._power_binary_sensor],
                    self._handle_power_binary_sensor_event,
                )
            )
            feedback = self._binary_sensor_is_on()
            if feedback is not None:
                self._state = MediaPlayerState.ON if feedback else MediaPlayerState.OFF
        self.async_write_ha_state()
        self.hass.async_create_task(self.async_update())

    @callback
    def _handle_power_binary_sensor_event(self, event):
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        is_on = binary_sensor_means_on(new_state.state)
        if is_on is None:
            return
        self._apply_binary_sensor_state(is_on)

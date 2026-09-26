DOMAIN = "hk_virtual_remote"
CONF_DEVICE_IP = "device_ip"
CONF_MODE = "remote_mode"
MODE_ACTION = "mode_action"
MODE_PHICOMM = "mode_phicomm"
MODE_ADB = "mode_adb"
MODE_XIAOMI = "mode_xiaomi"
CONF_POWER_SENSOR = "power_sensor"
CONF_POWER_ON_ENTITY = "power_on_entity"
CONF_POWER_BINARY_SENSOR = "power_binary_sensor"
CONF_POWER_THRESHOLD = "power_threshold"
DEFAULT_POWER_THRESHOLD = 10.0
CONF_XIAOMI_REMOTE = "xiaomi_remote"
CONF_XIAOMI_IR_DEVICE = "xiaomi_ir_device"
DEFAULT_XIAOMI_IR_DEVICE = "television"
CONF_SOURCES = "sources"
CONF_SOURCE_NAME = "name"
CONF_SOURCE_ID = "id"
CONF_SOURCE_ICON = "icon"
CONF_BTN_SELECT_SOURCE = "btn_select_source"
CONF_SOURCE_COMMAND = "command"

# 所有物理按键常量
CONF_BTN_POWER_ON = "btn_power_on"
CONF_BTN_POWER_OFF = "btn_power_off"
CONF_BTN_UP = "arrow_up"
CONF_BTN_DOWN = "arrow_down"
CONF_BTN_LEFT = "arrow_left"
CONF_BTN_RIGHT = "arrow_right"
CONF_BTN_SELECT = "select"
CONF_BTN_BACK = "back"
CONF_BTN_INFO = "information"
CONF_BTN_VOL_UP = "btn_volume_up"
CONF_BTN_VOL_DOWN = "btn_volume_down"
CONF_BTN_MUTE = "btn_mute"
CONF_BTN_PLAY_PAUSE = "btn_play_pause"

# Default command names for Xiaomi/Broadlink-style remote.send_command.
# Learn these via Settings → Infrared (or remote.learn_command) first.
DEFAULT_XIAOMI_COMMANDS = {
    CONF_BTN_POWER_ON: "power",
    CONF_BTN_POWER_OFF: "power",
    CONF_BTN_UP: "up",
    CONF_BTN_DOWN: "down",
    CONF_BTN_LEFT: "left",
    CONF_BTN_RIGHT: "right",
    CONF_BTN_SELECT: "select",
    CONF_BTN_BACK: "back",
    CONF_BTN_INFO: "menu",
    CONF_BTN_VOL_UP: "volume_up",
    CONF_BTN_VOL_DOWN: "volume_down",
    CONF_BTN_MUTE: "mute",
    CONF_BTN_PLAY_PAUSE: "play_pause",
}

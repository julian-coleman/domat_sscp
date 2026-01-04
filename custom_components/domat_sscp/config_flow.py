"""Config flow for the Domat SSCP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.frontend import storage as frontend_store
from homeassistant.config_entries import (
    SOURCE_REAUTH,
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
    #    OptionsFlowWithReload,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.selector import (
    BooleanSelector,
    BooleanSelectorConfig,
    LanguageSelector,
    LanguageSelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_CONNECTION_NAME,
    CONF_INSADY,
    CONF_LANGUAGE,
    CONF_SSCP_ADDRESS,
    DEFAULT_FAST_COUNT,
    DEFAULT_FAST_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SSCP_ADDRESS,
    DEFAULT_SSCP_PORT,
    DEFAULT_WRITE_RETRIES,
    DOMAIN,
    OPT_DEVICE,
    OPT_FAST_COUNT,
    OPT_FAST_INTERVAL,
    OPT_POLLING,
    OPT_SCAN_INTERVAL,
    OPT_UID,
    OPT_WRITE_RETRIES,
)
from .coordinator import DomatSSCPCoordinator
from .insady.insady_options_flow import (
    get_air_configs,
    get_air_schema,
    get_apartment_configs,
    get_apartment_schema,
    get_energy_configs,
    get_energy_schema,
    get_room_configs,
    get_room_schema,
)
from .sscp_connection import sscp_connection
from .sscp_const import SSCP_ERRORS
from .sscp_variable import sscp_variable

_LOGGER = logging.getLogger(__name__)

# Config flow schemas

# Languages matching our translations
_LANGS = ["en", "cs"]
_LANG_SELECTOR = vol.All(
    LanguageSelector(LanguageSelectorConfig(languages=_LANGS))
)

# Config flow
_PORT_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_ADDR_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=1, max=255, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
# Options flows schemas
_SCAN_INTERVAL_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=15, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_FAST_INTERVAL_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=2, max=15, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_FAST_COUNT_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=1, max=10, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)
_WRITE_RETRIES_SELECTOR = vol.All(
    NumberSelector(
        NumberSelectorConfig(min=2, max=10, mode=NumberSelectorMode.BOX),
    ),
    vol.Coerce(int),
)

# Options flow menus
_DEVICE_MENU = []
_INSADY_MENU = ["insady_room", "insady_apartment", "insady_energy", "insady_air",]
_CONFIG_MENU = ["poll", "info"]

class DomatSSCPConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domat SSCP."""

    # Config flow version
    VERSION = 1
    MINOR_VERSION = 3

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors: dict[str, str] = {}
        lang = None

        # Get user language
        try:
            owner = await self.hass.auth.async_get_owner()
            if owner is not None:
                owner_store = await frontend_store.async_user_store(
                    self.hass, owner.id
                )

                if (
                    "language" in owner_store.data
                    and "language" in owner_store.data["language"]
                ):
                        lang = owner_store.data["language"]["language"]
        except Exception:
            pass

        # System language
        if lang is None:
            lang = self.hass.config.language

        # Our translations
        if lang not in _LANGS:
            _LOGGER.error("Unsupported language: %s", lang)
            lang = "en"

        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            coordinator: DomatSSCPCoordinator = entry.coordinator
            input_data = entry.data
            step = "reconfigure"
        elif self.source == SOURCE_REAUTH:
            entry = self._get_reauth_entry()
            input_data = entry.data
            step = "reauth"
        else:  # user
            input_data = None
            step = "user"

        # Ask for input - initial defaults
        if user_input is None:
            return self.async_show_form(
                step_id=step,
                data_schema=_get_user_schema(input_data=input_data, lang=lang),
                errors=errors,
            )

        # Validate the user input and create an entry
        try:
            info = await _validate_config(
                data=user_input,
                variables=None,
            )
        except TimeoutError:
            errors["base"] = "timeout_connect"
        except (ValueError, OSError):
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        else:
            # No exception, so either abort or return
            await self.async_set_unique_id(info["unique_id"])
            if self.source == SOURCE_RECONFIGURE:
                coordinator.set_last_connect()
            if self.source in (SOURCE_RECONFIGURE, SOURCE_REAUTH):
                # Don't abort on unique ID mismatch, in case the PLC has a new serial number
                # self._abort_if_unique_id_mismatch(reason="wrong_plc")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )
            # user
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=info["title"], data=user_input)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=_get_user_schema(input_data=user_input, lang=lang),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        return await self.async_step_user(user_input)

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth."""
        return await self.async_step_user(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Setup an options flow for this handler."""
        return DomatSSCPOptionsFlowHandler(config_entry)


class DomatSSCPOptionsFlowHandler(OptionsFlow):
    """Handles options flow for Domat SSCP."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for Domat SSCP."""

        # Use a additional menu entries for InSady
        if self.config_entry.data[CONF_INSADY] is True:
            menu = _INSADY_MENU + _DEVICE_MENU + _CONFIG_MENU
        else:
            menu = _DEVICE_MENU + _CONFIG_MENU

        # Display a menu with step id's
        return self.async_show_menu(step_id="init", menu_options=menu)

    async def async_step_insady_room(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding a room controls device."""

        step = "insady_room"
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = get_room_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema)

        configs = get_room_configs(lang=lang)
        return await self._step_insady_common(
            step=step,
            user_input=user_input,
            configs=configs,
            schema=schema
        )

    async def async_step_insady_apartment(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding an apartment device."""

        step = "insady_apartment"
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = get_apartment_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema)

        configs = get_apartment_configs(lang=lang)
        return await self._step_insady_common(
            step=step,
            user_input=user_input,
            configs=configs,
            schema=schema
        )

    async def async_step_insady_energy(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding an energy usage device."""

        step = "insady_energy"
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = get_energy_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema)

        configs = get_energy_configs()
        return await self._step_insady_common(
            step=step,
            user_input=user_input,
            configs=configs,
            schema=schema
        )

    async def async_step_insady_air(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options for adding an air recuperation device."""

        step = "insady_air"
        lang=self.config_entry.data.get(CONF_LANGUAGE, "en")
        schema = get_air_schema(lang, user_input)

        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema)

        configs = get_air_configs()
        return await self._step_insady_common(
            step=step,
            user_input=user_input,
            configs=configs,
            schema=schema
        )

    async def _step_insady_common(
        self,
        step: str,
        user_input: dict[str, Any],
        configs: dict[str, Any],
        schema: vol.Schema
    ) -> ConfigFlowResult:
        """Common options flow for InSady flows."""

        coordinator: DomatSSCPCoordinator = self.config_entry.coordinator
        data: dict[str, Any] = self.config_entry.options.copy()
        errors: dict[str, str] = {}
        description_placeholders: dict[str, str] = {}
        variables: list[sscp_variable] = []
        entity_ids: dict[str, str] = {}

        _LOGGER.debug("User input: %s", user_input)
        # Create variables list from user input
        # Our entity ID's are uid-offset-length of the variable
        for section_name, config in configs.items():
            sect = user_input.get(section_name)
            uid = sect.get(OPT_UID)
            if uid != 0:
                variables.append(
                    sscp_variable(uid=uid, offset=config["offset"], length=config["length"], type=config["type"])
                )
                entity_id = str(uid) + "-" + str(config["offset"]) + "-" + str(config["length"])
                if entity_ids.get(entity_id) is not None:
                    errors["base"] = "variable_error"
                    errors[section_name] = "variable_error"
                    err_str = "UID Appears Twice"
                    description_placeholders = {
                        "error": err_str,
                        "variables": uid,
                    }
                    break
                entity_ids.update({entity_id: uid})
                _LOGGER.debug("Added: %s", entity_id)

        if len(errors) == 0 and len(variables) == 0:
            # No user variables
            errors["base"] = "variable_error"
            description_placeholders = {"error": "UID All Zero", "variables": "0"}

        if len(errors) == 0:
            # Check for existing device/entities
            err_info = _check_exists(
                device_name=user_input.get(OPT_DEVICE),
                entity_ids=entity_ids,
                options=self.config_entry.options
            )
            if "device" in err_info:
                errors[OPT_DEVICE] = "variable_error"
                err_str = "Device Already Exists"
                description_placeholders = {
                    "error": err_str,
                    "variables": user_input.get(OPT_DEVICE),
                }
            elif len(err_info["variables"]) > 0:
                errors["base"] = "variable_error"
                var_str = ""
                err_str = "UID Already Exists"
                for section_name in configs:
                    sect = user_input.get(section_name)
                    if sect.get(OPT_UID) in err_info["variables"]:
                        errors[section_name] = "variable_error"
                        var_str += str(sect.get(OPT_UID)) + " "
                description_placeholders = {
                    "error": err_str,
                    "variables": var_str,
                }

        if len(errors) == 0:
            # Validate the user input and create an entry
            coordinator.set_last_connect()
            try:
                info = await _validate_config(
                    data=self.config_entry.data,
                    variables=variables,
                )
            except TimeoutError:
                errors["base"] = "timeout_connect"
            except (ValueError, OSError):
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            else:
                # No exception, so either generate an error or return
                if info["error_code"] != 0:
                    err_str = SSCP_ERRORS.get(info["error_code"], "unknown")
                    var_str = ""
                    for section_name in configs:
                        sect = user_input.get(section_name)
                        if sect.get(OPT_UID) in info["error_variables"]:
                            errors["base"] = "variable_error"
                            errors[section_name] = "variable_error"
                            var_str += str(sect.get(OPT_UID)) + " "
                    description_placeholders = {
                        "error": err_str,
                        "variables": var_str,
                    }
                else:
                    for section_name, config in configs.items():
                        sect = user_input.get(section_name)
                        uid = sect.get(OPT_UID)
                        if uid != 0:
                            entity_id = str(uid) + "-" + str(config["offset"]) + "-" + str(config["length"])
                            config["uid"] = uid
                            config["name"] = sect.get("name")
                            config["device"] = user_input.get("device")
                            data.update({entity_id: config})

                    return self.async_create_entry(data=data)

        # There was some validation problem - previous input as defaults
        return self.async_show_form(
            step_id=step,
            data_schema=schema,
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_poll(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change polling parameters."""

        data: dict[str, Any] = self.config_entry.options.copy()
        step = "poll"

        default_scan_interval = DEFAULT_SCAN_INTERVAL
        default_fast_interval = DEFAULT_FAST_INTERVAL
        default_fast_count = DEFAULT_FAST_COUNT
        default_write_retries = DEFAULT_WRITE_RETRIES
        if OPT_POLLING in data:
            polling = data[OPT_POLLING]
            default_scan_interval = polling.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            default_fast_interval = polling.get(OPT_FAST_INTERVAL, DEFAULT_FAST_INTERVAL)
            default_fast_count = polling.get(OPT_FAST_COUNT, DEFAULT_FAST_COUNT)
            default_write_retries = polling.get(OPT_WRITE_RETRIES, DEFAULT_WRITE_RETRIES)
        if user_input is not None:
            default_scan_interval = user_input.get(OPT_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            default_fast_interval = user_input.get(OPT_FAST_INTERVAL, DEFAULT_FAST_INTERVAL)
            default_fast_count = user_input.get(OPT_FAST_COUNT, DEFAULT_FAST_COUNT)
            default_write_retries = user_input.get(OPT_WRITE_RETRIES, DEFAULT_WRITE_RETRIES)
        schema = vol.Schema(
            {
                vol.Required(OPT_SCAN_INTERVAL, default=default_scan_interval): _SCAN_INTERVAL_SELECTOR,
                vol.Required(OPT_FAST_INTERVAL, default=default_fast_interval): _FAST_INTERVAL_SELECTOR,
                vol.Required(OPT_FAST_COUNT, default=default_fast_count): _FAST_COUNT_SELECTOR,
                vol.Required(OPT_WRITE_RETRIES, default=default_write_retries): _WRITE_RETRIES_SELECTOR,
            }
        )
        if user_input is None:
            return self.async_show_form(step_id=step, data_schema=schema)

        data.update(
            {
                OPT_POLLING: {
                    OPT_SCAN_INTERVAL: user_input.get(OPT_SCAN_INTERVAL),
                    OPT_FAST_INTERVAL: user_input.get(OPT_FAST_INTERVAL),
                    OPT_FAST_COUNT: user_input.get(OPT_FAST_COUNT),
                    OPT_WRITE_RETRIES: user_input.get(OPT_WRITE_RETRIES)
                }
            }
        )
        return self.async_create_entry(data=data)

    async def async_step_info(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Write our configuration and  options to the log."""

        conf_data: dict[str, Any] = self.config_entry.data.copy()
        conf_data["password"] = "********"
        coordinator: DomatSSCPCoordinator = self.config_entry.coordinator
        level = _LOGGER.getEffectiveLevel()

        _LOGGER.setLevel(logging.INFO)
        _LOGGER.info("Co-ordinator name: %s", coordinator.name)
        _LOGGER.info("Configuration data: %s", conf_data)
        _LOGGER.info("Options: %s", self.config_entry.options)
        _LOGGER.setLevel(level)
        return self.async_abort(reason="info_written")


class InvalidAuth(HomeAssistantError):
    """Error to indicate that the authentication is invalid."""


# Helpers
def _check_exists(
    device_name: str | None,
    entity_ids: dict[str, str],
    options: dict[str, Any]
) -> dict[str, Any]:
    """Check if device or entity already exists."""

    variables: list = []
    # Does the device already exist?
    for value in options.values():
        if (
            device_name is not None
            and "device" in value
            and value["device"] == device_name
        ):
            return {"device": device_name}
    # Does the entity already exist?
    for entity_id, entity_uid in entity_ids.items():
        if entity_id in options:
            variables.append(entity_uid)

    return {"variables": variables}


async def _validate_config(
    data: dict[str, Any],
    variables: list[sscp_variable] | None,
) -> dict[str, Any]:
    """Validate that the user input allows us to connect using the values provided by the user.

    Catches some exceptions to raise InvalidAuth.
    Returns either information or errors in info[].
    """

    # Config flow info
    unique_id = ""
    # Options flow info
    error_code = 0
    error_vars = []

    conn = sscp_connection(
        name=data[CONF_CONNECTION_NAME],
        ip_address=data[CONF_IP_ADDRESS],
        port=data[CONF_PORT],
        user_name=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        sscp_address=data[CONF_SSCP_ADDRESS],
        md5_hash=None,
    )

    # Only catch some exceptions specific to authentication
    try:
        await conn.login()
        if conn.socket is None:
            _LOGGER.debug("Login failed")
            raise InvalidAuth from None
    except TimeoutError:
        _LOGGER.debug("Login timeout")
        raise InvalidAuth from None

    if variables is None:
        # Config flow
        # Use user name, SSCP address and PLC serial for unique ID
        await conn.get_info()
        if conn.serial is None:
            _LOGGER.warning("No serial number for %s", data[CONF_CONNECTION_NAME])
            unique_id = (
                data[CONF_USERNAME]
                + "-"
                + str(data[CONF_SSCP_ADDRESS])
                + "-0000000000000000"
            )
        else:
            unique_id = (
                data[CONF_USERNAME]
                + "-"
                + str(data[CONF_SSCP_ADDRESS])
                + "-"
                + conn.serial
            )
        _LOGGER.info("Using unique ID: %s", unique_id)
    else:
        # Options flow
        error_vars, error_codes = await conn.sscp_read_variables(variables)
        if len(error_vars) > 0:
            error_code = error_codes[0]  # We only display the first error

    await conn.logout()

    # Return info about the connection or errors.
    return {
        "title": data[CONF_CONNECTION_NAME],
        "unique_id": unique_id,
        "error_code": error_code,
        "error_variables": error_vars,
    }


def _get_user_schema(
    input_data: dict[str, Any] | None = None,
    lang: str | None = "en"
) -> vol.Schema:
    """Return a config flow schema with defaults based on the step and user input."""

    # Fill in defaults from initial defaults or input
    default_connection_name = ""
    default_ip_address = ""
    default_port = DEFAULT_SSCP_PORT
    default_username = ""
    default_password = ""
    default_sscp_address = DEFAULT_SSCP_ADDRESS
    default_language = lang
    default_insady = True
    if input_data is not None:
        default_connection_name = input_data.get(
            CONF_CONNECTION_NAME, default_connection_name
        )
        default_ip_address = input_data.get(CONF_IP_ADDRESS, default_ip_address)
        default_port = input_data.get(CONF_PORT, default_port)
        default_username = input_data.get(CONF_USERNAME, default_username)
        default_password = input_data.get(CONF_PASSWORD, default_password)
        default_sscp_address = input_data.get(CONF_SSCP_ADDRESS, default_sscp_address)
        default_language = input_data.get(CONF_LANGUAGE, default_language)
        default_insady = input_data.get(CONF_INSADY, default_insady)
    return vol.Schema(
        {
            vol.Required(CONF_CONNECTION_NAME, default=default_connection_name): str,
            vol.Required(CONF_IP_ADDRESS, default=default_ip_address): str,
            vol.Required(CONF_PORT, default=default_port): _PORT_SELECTOR,
            vol.Required(CONF_USERNAME, default=default_username): str,
            vol.Required(CONF_PASSWORD, default=default_password): str,
            vol.Required(
                CONF_SSCP_ADDRESS, default=default_sscp_address
            ): _ADDR_SELECTOR,
            vol.Required(CONF_LANGUAGE, default=default_language): _LANG_SELECTOR,
            vol.Required(CONF_INSADY, default=default_insady): BooleanSelector(BooleanSelectorConfig()),
        }
    )

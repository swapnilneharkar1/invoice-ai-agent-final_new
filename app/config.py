from __future__ import annotations

from dataclasses import dataclass

# ============================================================
# Configuration — edit these values directly, then restart the app
# for changes to take effect.
# ============================================================

FLOW_HTTP_URL = "https://e1355388b33ae9e4887bee3181d0e4.d4.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/26/workflows/a2d0fd625b634b67a4a06ce0ef8d8fcb/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=ZABddUE2a1Ln8jbshwjaDhBXu_QKmdMgtyf8YfkzlQc"

FLOW_TIMEOUT_SECONDS = 666
FLOW_POLL_INTERVAL_SECONDS = 5

# Authorized users
ACCESS_LIST = (
    "swapnil.neharkar1@bajajfinserv.in",
    "divesh.unadkat@bajajfinserv.in",
    "rahul.bansal2@bajajfinserv.in",
     "abhinav.rathi@bajajfinserv.in",
    "rahul.mandaokar@bajajfinserv.in",
    "gaurav.jain3@bajajfinserv.in",
    "omkar.kanade@bajajfinserv.in",
    "nilesh.vinchurkar@bajajfinserv.in",
    "palak.gupta1@bajajfinserv.in",
    "divya.sikchi@bajajfinserv.in",
    "ritesh.karale1@bizsupporta.com",
    "onkar.takalikar@bizsupporta.com",
    "vishnu.rathod3@bizsupporta.com",
    "chaitanaya.bongane@bizsupporta.com",
    "krishnakant.harale@bizsupporta.com",

)


@dataclass(frozen=True)
class Settings:
    flow_http_url: str = FLOW_HTTP_URL
    flow_timeout_seconds: int = FLOW_TIMEOUT_SECONDS
    flow_poll_interval_seconds: int = FLOW_POLL_INTERVAL_SECONDS
    access_list: tuple[str, ...] = ACCESS_LIST


def load_settings() -> Settings:
    return Settings()
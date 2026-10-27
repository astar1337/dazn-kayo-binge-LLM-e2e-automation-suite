
# TEST REGISTRY
#
# Format: ("TEST_ID", "Human Readable Name", function_reference, ["tags"])
#
# Available tags:
#   smoke      - Critical path, run on every build
#   regression - Full coverage, run nightly
#   critical   - Blocks release if these test fail
#   login      - Login-related tests
#   playback   - Playback-related tests
#   navigation - Navigation-related tests
#   search     - Search-related tests


# DAZN Login
from tests.dazn.test_login import (
    run_valid_login as dazn_valid_login,
    run_invalid_password as dazn_invalid_password,
    run_empty_fields as dazn_empty_fields,
    run_logout as dazn_logout,
)

# DAZN Playback
from tests.dazn.test_playback import (
    run_vod_playback as dazn_vod_playback,
    run_live_stream as dazn_live_stream,
    run_play_pause as dazn_play_pause,
    run_seek as dazn_seek,
)

# DAZN Navigation
from tests.dazn.test_navigation import (
    run_bottom_nav_tabs as dazn_nav_tabs,
    run_search as dazn_nav_search,
    run_content_detail as dazn_content_detail,
)

# DAZN Search
from tests.dazn.test_search import (
    run_search_with_results as dazn_search_with_results,
    run_search_no_results as dazn_search_no_results,
)


TEST_REGISTRY = {
    "dazn": {
        "login": [
            ("TC-DAZN-LOGIN-001", "Valid Login", dazn_valid_login, ["smoke", "critical"]),
            ("TC-DAZN-LOGIN-002", "Invalid Password", dazn_invalid_password,["smoke", "critical"]),
            ("TC-DAZN-LOGIN-003", "Empty Fields", dazn_empty_fields,["smoke", "critical"]),
            ("TC-DAZN-LOGIN-004", "Logout", dazn_logout,["smoke", "critical"]),
        ],
        "playback": [
            ("TC-DAZN-PLAY-001", "VOD Playback", dazn_vod_playback,["smoke", "critical"]),
            ("TC-DAZN-PLAY-002", "Live Stream", dazn_live_stream,["smoke", "critical"]),
            ("TC-DAZN-PLAY-003", "Play Pause", dazn_play_pause,["smoke", "critical"]),
            ("TC-DAZN-PLAY-004", "Seek", dazn_seek,["smoke", "critical"]),
        ],
        "navigation": [
            ("TC-DAZN-NAV-001", "Bottom Nav Tabs", dazn_nav_tabs,["smoke", "critical"]),
            ("TC-DAZN-NAV-002", "Search", dazn_nav_search,["smoke", "critical"]),
            ("TC-DAZN-NAV-003", "Content Detail", dazn_content_detail,["smoke", "critical"]),
        ],
        "search": [
            ("TC-DAZN-SEARCH-001", "Search With Results", dazn_search_with_results,["smoke", "critical"]),
            ("TC-DAZN-SEARCH-002", "Search No Results", dazn_search_no_results,["smoke", "critical"]),
        ],
    },
}
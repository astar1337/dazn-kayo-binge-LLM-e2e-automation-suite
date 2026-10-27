from tests.base_test import BaseTest


class DAZNSearch(BaseTest):
    APP_NAME = "dazn"
    APP_PACKAGE = "com.dazn"
    CREDENTIALS_FILE = "credentials/dazn_creds.yaml"


async def run_search_with_results(device_id: str, vpn_region: str, language: str, search_term: str = "boxing"):
    """TC-DAZN-SEARCH-001: Search returns relevant results."""
    test = DAZNSearch(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = f"""
    OBJECTIVE: Verify searching for '{search_term}' returns relevant results.

    EXECUTION STEPS:
    1. Launch DAZN and log in.
    2. Tap the Search icon.
    3. WAIT AND OBSERVE for search bar to appear.
    4. Type '{search_term}' in the search field.
    5. WAIT AND OBSERVE for results (up to 10 seconds).
    6. Count approximate number of results shown.

    ASSERTION:
    - PASS if: At least 1 result is shown and appears relevant to '{search_term}'.
    - FAIL if: Zero results for a common sports term, or results are unrelated.
    """

    return await test.run_test(
        test_id=f"TC-DAZN-SEARCH-001-{search_term.upper()}",
        test_name=f"Search Results - {search_term}",
        task_prompt=prompt,
    )


async def run_search_no_results(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-SEARCH-002: Nonsense search shows empty state."""
    test = DAZNSearch(device_id=device_id, vpn_region=vpn_region, language=language)

    nonsense_term = "xyznonexistentcontent123"

    prompt = f"""
    OBJECTIVE: Verify that searching for '{nonsense_term}' shows a proper empty state.

    EXECUTION STEPS:
    1. Launch DAZN and log in.
    2. Tap the Search icon.
    3. Type '{nonsense_term}' in the search field.
    4. WAIT AND OBSERVE for 10 seconds.
    5. Observe the results area.

    ASSERTION:
    - PASS if: A friendly "no results" message is shown.
    - FAIL if: App crashes, shows an error, or shows unrelated results.
    """

    return await test.run_test()
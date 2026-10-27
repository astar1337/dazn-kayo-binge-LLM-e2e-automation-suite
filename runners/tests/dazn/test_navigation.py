from tests.base_test import BaseTest


class DAZNNavigation(BaseTest):
    APP_NAME = "dazn"
    APP_PACKAGE = "com.dazn"
    CREDENTIALS_FILE = "credentials/dazn_creds.yaml"


async def run_bottom_nav_tabs(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-NAV-001: All bottom navigation tabs are accessible."""
    test = DAZNNavigation(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
    OBJECTIVE: Verify all bottom navigation tabs load their respective screens.

    EXECUTION STEPS:
    1. Launch DAZN and log in.
    2. WAIT AND OBSERVE. Verify you are on the Home tab.
    3. Tap the 'Live' tab. WAIT AND OBSERVE until screen loads.
    4. Verify Live screen loaded (should show live/upcoming events).
    5. Tap the 'Schedule' tab. WAIT AND OBSERVE until screen loads.
    6. Verify Schedule screen loaded.
    7. Tap the 'My DAZN' tab. WAIT AND OBSERVE until screen loads.
    8. Verify My DAZN screen loaded (profile/account info).
    9. Tap the 'Home' tab to return.
    10. Verify Home screen is shown again.

    ASSERTION:
    Compare the final Home screen to the GOLDEN REFERENCE.
    - PASS if: All 4 tabs loaded their correct screens without errors.
    - FAIL if: Any tab fails to load, shows error, or loads wrong screen.
    """

    return await test.run_test(
        test_id="TC-DAZN-NAV-001",
        test_name="Bottom Navigation Tabs",
        task_prompt=prompt,
        reference_image_path=test._build_reference_path("components/bottom_nav_bar.png"),
    )


async def run_search(device_id: str, vpn_region: str, language: str, search_term: str = "boxing"):
    """TC-DAZN-NAV-002: Search returns relevant results."""
    test = DAZNNavigation(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = f"""
    OBJECTIVE: Verify search finds relevant content.

    EXECUTION STEPS:
    1. Launch DAZN and log in.
    2. Find and tap the Search icon (usually top right of home screen).
    3. WAIT AND OBSERVE for search screen/bar to appear.
    4. Type the search term: '{search_term}'.
    5. WAIT AND OBSERVE for search results to load (up to 10 seconds).
    6. Observe the results.

    ASSERTION:
    - PASS if: Search results appear and are relevant to '{search_term}'.
    - FAIL if: No results shown, search bar not found, or app crashes.
    """

    return await test.run_test(
        test_id="TC-DAZN-NAV-002",
        test_name=f"Search - {search_term}",
        task_prompt=prompt,
    )


async def run_content_detail(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-NAV-003: Content detail page loads correctly."""
    test = DAZNNavigation(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
    OBJECTIVE: Verify content detail pages load with expected elements.

    EXECUTION STEPS:
    1. Launch DAZN and log in.
    2. From the home screen, tap on any content card.
    3. WAIT AND OBSERVE for the content detail page to load.
    4. Check for the presence of:
       - Content title
       - Play button or Watch button
       - Content description or metadata
       - Back navigation button
    5. Tap the back button to return to home.

    ASSERTION:
    - PASS if: Detail page loads with at minimum a title and play button.
    - FAIL if: Detail page is blank, missing play button, or crashes.
    """

    return await test.run_test(
        test_id="TC-DAZN-NAV-003",
        test_name="Content Detail Page",
        task_prompt=prompt,
    )
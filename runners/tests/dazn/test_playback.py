from tests.base_test import BaseTest


class DAZNPlayback(BaseTest):
    APP_NAME = "dazn"
    APP_PACKAGE = "com.dazn"
    CREDENTIALS_FILE = "credentials/dazn_creds.yaml"


async def run_vod_playback(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-PLAY-001: VOD content plays successfully."""
    test = DAZNPlayback(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
    OBJECTIVE: Verify that on-demand video content plays successfully.

    EXECUTION STEPS:
    1. Launch DAZN and log in with 'dazn_standard_email' / 'dazn_standard_password'.
    2. WAIT AND OBSERVE until home screen loads.
    3. Browse the home screen content rails.
    4. Find any VOD content card (must NOT have a red LIVE badge).
    5. Tap the content card.
    6. On the content detail page, tap the Play button.
    7. WAIT AND OBSERVE for up to 15 seconds for the video player to load.
    8. Once player loads, observe for at least 5 seconds.

    ASSERTION:
    Compare the Live App screenshot to the GOLDEN REFERENCE image provided.
    - PASS if: Video player is visible and matches the reference layout.
      Progress bar is moving. No error overlay present.
    - FAIL if: Error message appears, buffering never resolves, or black screen persists.
    """

    return await test.run_test(
        test_id="TC-DAZN-PLAY-001",
        test_name="VOD Playback",
        task_prompt=prompt,
        reference_image_path=test._build_reference_path("full_screens/player_playing.png"),
    )


async def run_live_stream(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-PLAY-002: Live stream plays successfully."""
    test = DAZNPlayback(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
    OBJECTIVE: Verify live streaming content plays successfully.

    EXECUTION STEPS:
    1. Launch DAZN and log in.
    2. Tap the 'Live' tab in bottom navigation.
    3. WAIT AND OBSERVE for the live content list to load.
    4. Look for any content with a red 'LIVE' badge.
    5. If no live content exists, report test as SKIPPED.
    6. If live content exists, tap on it.
    7. Tap the Play/Watch Live button.
    8. WAIT AND OBSERVE for up to 20 seconds for live stream to load.
    9. Observe stream for 5 seconds.

    ASSERTION:
    - PASS if: Live stream is playing with LIVE indicator visible in the player.
    - SKIP if: No live events are currently available.
    - FAIL if: Error loading stream, geo-block message, or crash.
    """

    return await test.run_test(
        test_id="TC-DAZN-PLAY-002",
        test_name="Live Stream Playback",
        task_prompt=prompt,
        reference_image_path=test._build_reference_path("full_screens/player_playing.png"),
    )


async def run_play_pause(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-PLAY-003: Play/Pause controls work correctly."""
    test = DAZNPlayback(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
    OBJECTIVE: Verify play and pause controls function correctly.

    EXECUTION STEPS:
    1. Launch DAZN, log in, navigate to any VOD content and start playback.
    2. WAIT AND OBSERVE until video is playing (progress bar moving).
    3. Tap the screen to reveal player controls.
    4. Note the current playback position on the seek bar.
    5. Tap the PAUSE button.
    6. WAIT AND OBSERVE for 3 seconds. Video should be frozen.
    7. Note the playback position again. It should NOT have moved.
    8. Tap the PLAY button.
    9. WAIT AND OBSERVE for 3 seconds. Video should resume.
    10. Note the playback position. It should have advanced.

    ASSERTION:
    Compare the paused state to the GOLDEN REFERENCE (paused player).
    - PASS if: Video pauses when pause is tapped AND resumes when play is tapped.
    - FAIL if: Controls are unresponsive or video continues during pause.
    """

    return await test.run_test(
        test_id="TC-DAZN-PLAY-003",
        test_name="Play Pause Controls",
        task_prompt=prompt,
        reference_image_path=test._build_reference_path("full_screens/player_paused.png"),
    )


async def run_seek(device_id: str, vpn_region: str, language: str):
    """TC-DAZN-PLAY-004: Seek bar allows jumping to different positions."""
    test = DAZNPlayback(device_id=device_id, vpn_region=vpn_region, language=language)

    prompt = """
    OBJECTIVE: Verify the seek bar allows scrubbing to different positions.

    EXECUTION STEPS:
    1. Launch DAZN, log in, start any VOD content.
    2. Let it play for 5 seconds.
    3. Tap screen to show controls.
    4. Note current position on seek bar.
    5. Drag the seek bar thumb forward to approximately 50% of content.
    6. Release and WAIT AND OBSERVE for video to resume from new position.
    7. Verify position changed to approximately where you seeked.

    ASSERTION:
    - PASS if: Video jumps to the new seek position and resumes playing.
    - FAIL if: Seek bar is unresponsive, video doesn't jump, or app crashes.
    """

    return await test.run_test(
        test_id="TC-DAZN-PLAY-004",
        test_name="Seek Functionality",
        task_prompt=prompt,
        reference_image_path=test._build_reference_path("components/player_seek_bar.png"),
    )
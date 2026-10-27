# tests/dazn/criteria/login.py

from models.test_results import ExpectedCriteria, ElementCheck


LOGIN_CRITERIA = ExpectedCriteria(
    required_elements=[
        ElementCheck(
            element="navigation bar",
            aliases=["bottom navigation", "nav bar", "bottom bar", "navigation tabs"],
            critical=True,
        ),
        ElementCheck(
            element="HOME tab",
            aliases=[],
            critical=True,
        ),
        ElementCheck(
            element="SCORES tab",
            aliases=[],
            critical=True,
        ),
        ElementCheck(
            element="SCHEDULE tab",
            aliases=[],
            critical=False,
        ),
        ElementCheck(
            element="SPORTS tab",
            aliases=[],
            critical=False,
        ),
    ],
    forbidden_elements=[
        ElementCheck(
            element="error message",
            aliases=["error dialog", "error popup"],
            critical=True,
        ),
        ElementCheck(
            element="login screen",
            aliases=["sign in screen", "login form"],
            critical=True,
        ),
        ElementCheck(
            element="crash dialog",
            aliases=["app has stopped", "keeps stopping"],
            critical=True,
        ),
        ElementCheck(
            element="invalid credentials",
            aliases=["wrong password", "incorrect password"],
            critical=True,
        ),
    ],
    required_state="Home screen is displayed with content loaded and bottom navigation",
)


# Future: add more criteria for other login scenarios
# INVALID_LOGIN_CRITERIA = ExpectedCriteria(
#     required_elements=[
#         ElementCheck(element="error message", aliases=[...], critical=True),
#         ElementCheck(element="login screen", aliases=[...], critical=True),
#     ],
#     forbidden_elements=[
#         ElementCheck(element="navigation bar", aliases=[...], critical=True),
#     ],
#     required_state="Login screen still displayed with error message",
# )
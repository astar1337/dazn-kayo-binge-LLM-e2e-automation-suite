[
    {
        "app_id": "com.dazn",
        "app_name": "DAZN",
        "description": "DAZN is a sports streaming app available in Germany. Login is required.",
        
        "handling_popups": "CRITICAL INSTRUCTIONS:\n- GDPR Cookie Banner: If you see 'Zustimmen' or 'Alle Akzeptieren', tap it immediately.\n- If a system dialog asks for permissions, tap 'Don't Allow' or 'Nicht erlauben'.\n- If a 'Rate this App' pop-up appears, tap 'Not Now' or the 'X' icon.",

        "permanent_anchors": {
            "splash_screen": {
                "dazn_logo": {
                    "resourceId": "DaznLogo",
                    "description": "DAZN brand logo, always present in header area",
                    "use": "Confirms you are in the DAZN app"
                },
                "login_button": {
                    "resourceId": "LpButton",
                    "text_contains": "Log in",
                    "description": "Primary login button in top-right header area",
                    "use": "ALWAYS use this to navigate to login. Prefer this over visual matching."
                },
                "explore_button": {
                    "resourceId": "LpButton",
                    "text_contains": "Explore",
                    "description": "Browse content without logging in",
                    "use": "Do NOT tap this during login tests"
                },
                "get_started_button": {
                    "className": "Button",
                    "text_contains": "Get started",
                    "description": "Primary CTA button, center-bottom of splash screen",
                    "use": "Tap this after entering email to proceed to password step"
                }
            },
            "login_screen": {
                "email_field": {
                    "className": "EditText",
                    "description": "Email input field, always the first input on login screen",
                    "use": "Tap this and use type_secret with credential key to enter email"
                },
                "password_field": {
                    "className": "EditText",
                    "description": "Password input field, appears after email is submitted",
                    "use": "Tap this and use type_secret with credential key to enter password"
                }
            },
            "home_screen": {
                "bottom_nav_home": {
                    "text_contains": "Home",
                    "description": "Home tab in bottom navigation bar",
                    "use": "If visible, confirms user is successfully logged in"
                },
                "bottom_nav_live": {
                    "text_contains": "Live",
                    "description": "Live tab in bottom navigation bar",
                    "use": "If visible, confirms user is on home screen"
                },
                "bottom_nav_schedule": {
                    "text_contains": "Schedule",
                    "description": "Schedule tab in bottom navigation bar. May show as 'Zeitplan' in German.",
                    "use": "If visible, confirms user is on home screen"
                },
                "bottom_nav_my_dazn": {
                    "text_contains": "My DAZN",
                    "description": "My DAZN tab in bottom navigation bar. May show as 'Mein DAZN' in German.",
                    "use": "Tap this to access account settings and logout"
                }
            }
        },

        "key_screens": {
            "splash_screen": "Background: Dark/Black with DAZN logo (resourceId: DaznLogo). Login Button: Look for resourceId 'LpButton' with text 'Log in' in the top-right area. Do NOT tap 'Explore' or 'Get started' unless instructed.",
            "login_screen_email": "IMPORTANT: DAZN login is a TWO-STEP process. First screen shows ONLY an Email field (className: EditText). Enter the email and tap 'Get started' button to proceed to the password screen.",
            "login_screen_password": "Second screen shows the Password field (className: EditText). Enter the password and tap 'Sign in' or 'LOG IN' button.",
            "home_screen": "Bottom Navigation bar contains: 'Home', 'Live', 'Schedule' (or 'Zeitplan'), 'My DAZN' (or 'Mein DAZN'). If you see these tabs, the user is successfully logged in."
        }
    }
]
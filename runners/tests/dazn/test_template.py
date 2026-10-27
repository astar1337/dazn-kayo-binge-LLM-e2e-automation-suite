
# async def run_test_case(device_id: str, vpn_region: str, language: str, agent_mode: str = "default",no_trajectory: bool = False):
#     test = DAZNLogin(device_id=device_id, vpn_region=vpn_region, language=language)

#     prompt = f"""
#     OBJECTIVE: X Y Z

#     EXECUTION STEPS:
#     """ X Y Z """

#     assertions = {
#         "must_contain": [""],
#         "must_not_contain": [""],
#     }

#     return await test.run_test(
#         test_id="TC-",
#         test_name="",
#         task_prompt=prompt,
#         # reference_image_path=test._build_reference_path("full_screens/home_screen_loaded.png"),
#         agent_mode=agent_mode,
#         no_trajectory=no_trajectory,
        
#     )
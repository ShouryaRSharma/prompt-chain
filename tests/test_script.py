# import requests

# API_BASE = "http://localhost:8000"


# def create_model(model_config):
#     response = requests.post(f"{API_BASE}/create_model", json=model_config)
#     print(f"Model {model_config['name']} created: {response.json()}")


# def create_chain(chain_config):
#     response = requests.post(f"{API_BASE}/create_chain", json=chain_config)
#     print(f"Chain created: {response.json()}")


# def execute_chain(chain_name, initial_input):
#     request = {"chain_name": chain_name, "initial_input": initial_input}
#     response = requests.post(f"{API_BASE}/execute_chain", json=request)
#     return response.json()


# crime_detector_model = {
#     "name": "crime_detector",
#     "system_prompt": """You are an AI assistant specialized in detecting crimes in web articles. Your task is to determine if a crime has been committed based on the given article text.

# Input Schema:
# {
#     "article_text": "str"
# }

# Output Schema:
# {
#     "crime_detected": "bool",
#     "explanation": "str"
# }

# Ensure your response is a valid JSON object matching the output schema.""",
#     "user_prompt_schema": {"article_text": "str"},
#     "response_schema": {"crime_detected": "bool", "explanation": "str"},
# }

# crime_classifier_model = {
#     "name": "crime_classifier",
#     "system_prompt": """You are an AI assistant specialized in classifying crimes. Your task is to categorize the crime mentioned in the article into one of four types: Theft, Assault, Fraud, or Cybercrime. Only classify if a crime has been detected.

# Input Schema:
# {
#     "article_text": "str",
#     "crime_detected": "bool"
# }

# Output Schema:
# {
#     "crime_type": "str",
#     "confidence": "float"
# }

# Ensure your response is a valid JSON object matching the output schema. If no crime was detected, set crime_type to "None" and confidence to 0.0.""",
#     "user_prompt_schema": {"article_text": "str", "crime_detected": "bool"},
#     "response_schema": {"crime_type": "str", "confidence": "float"},
# }

# crime_summarizer_model = {
#     "name": "crime_summarizer",
#     "system_prompt": """You are an AI assistant that summarizes crime reports. Your task is to create a concise summary of the crime committed and where it was spotted, based on the article text and the classified crime type.

# Input Schema:
# {
#     "article_text": "str",
#     "crime_type": "str"
# }

# Output Schema:
# {
#     "summary": "str"
# }

# Ensure your response is a valid JSON object matching the output schema. If the crime_type is "None", provide a summary stating that no crime was detected in the article.""",
#     "user_prompt_schema": {"article_text": "str", "crime_type": "str"},
#     "response_schema": {"summary": "str"},
# }

# # Define chain configuration
# chain_config = {
#     "name": "crime_detection_chain",
#     "steps": [
#         {"name": "crime_detector", "input_mapping": {"article_text": "initial_input.article_text"}},
#         {
#             "name": "crime_classifier",
#             "input_mapping": {
#                 "article_text": "initial_input.article_text",
#                 "crime_detected": "previous_step.crime_detected",
#             },
#         },
#         {
#             "name": "crime_summarizer",
#             "input_mapping": {
#                 "article_text": "initial_input.article_text",
#                 "crime_type": "previous_step.crime_type",
#             },
#         },
#     ],
#     "final_output_mapping": {
#         "crime_detected": "step_0.crime_detected",
#         "crime_type": "step_1.crime_type",
#         "summary": "step_2.summary",
#     },
# }

# # Create models
# create_model(crime_detector_model)
# create_model(crime_classifier_model)
# create_model(crime_summarizer_model)

# # Create chain
# create_chain(chain_config)

# # Test article
# test_article = """
# Local police reported a break-in at the downtown jewelry store last night.
# The perpetrators smashed a display window and made off with several high-value
# items. Authorities are reviewing security camera footage and asking for any
# witnesses to come forward.
# """

# # Execute chain
# result = execute_chain("crime_detection_chain", {"article_text": test_article})

# # Print results
# print("\nChain Execution Result:")
# print(f"Crime Detected: {result['result']['crime_detected']}")
# print(f"Crime Type: {result['result']['crime_type']}")
# print(f"Summary: {result['result']['summary']}")

# # Test with a non-crime article
# non_crime_article = """
# The city council announced today that the annual summer festival will be held
# next month in Central Park. The event will feature live music, food vendors,
# and activities for children. Local businesses are encouraged to participate
# by setting up booths to showcase their products and services.
# """

# # Execute chain with non-crime article
# non_crime_result = execute_chain("crime_detection_chain", {"article_text": non_crime_article})

# # Print results for non-crime article
# print("\nNon-Crime Article Chain Execution Result:")
# print(f"Crime Detected: {non_crime_result['result']['crime_detected']}")
# print(f"Crime Type: {non_crime_result['result'].get('crime_type', 'N/A')}")
# print(f"Summary: {non_crime_result['result'].get('summary', 'N/A')}")

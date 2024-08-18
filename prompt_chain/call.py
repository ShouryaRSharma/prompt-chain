# import os
# from typing import Type

# from prompt_chain.prompt_lib.models import (
#     PromptModel,
#     ResponseModel,
#     SentenceExtractionPrompt,
#     SentenceExtractionResponse,
# )
# from prompt_chain.prompt_lib.web_client import WebClient


# def call_openai(
#     prompt: PromptModel[SentenceExtractionPrompt], response_model: Type[ResponseModel[list[str]]]
# ) -> list[str]:
#     OPEN_AI_KEY = os.getenv("OPENAI_API_KEY")

#     headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPEN_AI_KEY}"}

#     data = {
#         "model": "gpt-3.5-turbo",
#         "messages": [
#             {"role": "system", "content": prompt.system_prompt},
#             {"role": "user", "content": prompt.user_prompt.model_dump_json()},
#         ],
#     }

#     with WebClient() as web_client:
#         res = web_client.post(
#             "https://api.openai.com/v1/chat/completions", headers=headers, json=data
#         )
#         shaped_response = res["choices"][0]["message"]["content"]
#         validated_response = response_model.model_validate_json(shaped_response)
#         return validated_response.result


# def extract_sentences(content: str) -> list[str]:
#     prompt: PromptModel[SentenceExtractionPrompt] = PromptModel(
#         system_prompt="""
#         Extract sentences from the content where John Doe is mentioned.
#         Your input schema will be like so:
#         {
#             "content": "The content from which you want to extract sentences."
#         }
#         Your response schema should always be a json in the following format:
#         {
#             "result": [list of sentences]
#         }
#         """,
#         user_prompt=SentenceExtractionPrompt(content=content),
#     )

#     return call_openai(prompt, SentenceExtractionResponse)


# if __name__ == "__main__":
#     content = (
#         "John Doe went to the store. He bought some apples. Later, John Doe called his friend."
#     )
#     sentences = extract_sentences(content)
#     print("Extracted sentences:", sentences)

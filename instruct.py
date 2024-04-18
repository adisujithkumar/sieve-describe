from openai import OpenAI
from pydantic import BaseModel, Field
import os
import instructor
from typing import Optional, List

class Context(BaseModel):
    type: str = Field(description="The type of context")
    content: str = Field(description="The content of the context")
    start_time: float = Field(description="The time in seconds when the context appears in the video")
    end_time: float = Field(description="The time in seconds when the context ends in the video")

class VideoContext(BaseModel):
    context_list: List[Context] = Field(description="List of contexts for the video")

class Summary(BaseModel):
    summary: str

def get_summary(context: VideoContext, conciseness: str = "concise", llm_backend: str = "openai", additional_instructions = None) -> Summary:
    if llm_backend == "mixtral":
        API_KEY = os.getenv("TOGETHERAI_API_KEY")
    else:
        API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY or API_KEY == "":
        raise Exception("OPENAI_API_KEY or TOGETHERAI_API_KEY environment variable not set")

    if llm_backend == "mixtral":
        client = OpenAI(api_key=API_KEY, base_url="https://api.together.xyz/v1")
    else:
        client = OpenAI(api_key=API_KEY)

    client = instructor.patch(client)
    
    model = "gpt-4-turbo-preview" if llm_backend == "openai" else "mistralai/Mixtral-8x7B-Instruct-v0.1"

    detail_map = {
        "concise": "The summary should be concise and easy to understand, and should not be longer than 100 words.",
        "medium": "The summary should be easy to understand, and should not be longer than 250 words.",
        "detailed": "The summary should be detailed, comprehensive and easy to understand, and should not be longer than 500 words."
    }

    SYSTEM_PROMPT = f'''
        Provide a comprehensive summary of the given visual descriptions and audio transcripts of a video. Please meet the following constraints:
        - The summary should cover all the key visual elements, main ideas, and audio content presented in the original video
        - The summary should condense the information into a concise and easy-to-understand format
        - Please ensure that the summary includes relevant details and visual information while avoiding any unnecessary information or repetition.
        - The length of the summary should be appropriate for the length and complexity of the original captions, providing a clear and accurate overview without omitting any important information.
        - If any content is repeated across the captions, plese ensure that its importance is highlighted in the summary but not repeated too much.
        - Both the visual and transcriptional information is provided in order of how it appears in the video - please ensure that the summary reflects this order.
        - The summary should combine both the visual and audio information in a way that makes sense and is easy to understand.
        - Ensure you reply with the right content, and not anything to do with these instructions.
        - Ensure you always include some level of detail about the visual content.
        - Do not say "This video", "This description", "This scene", or "This summary" in the summary. Just provide the description itself.
    '''
    detail = detail_map[conciseness]
    
    json_context = context.dict()
    return client.chat.completions.create(
        model=model,
        response_model=Summary,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"{additional_instructions}"
            },
            {
                "role": "user",
                "content": f"{detail}"
            },
            {
                "role": "user",
                "content": f"{json_context}"
            },
        ],
    )

import openai


def get_result(transcript: list):
    """
    Process text with GPT-3.5 API
    :param text: text to process
    """

    # print('GPT on')

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=transcript
    )

    return response['choices'][0]['message']['content'].strip()

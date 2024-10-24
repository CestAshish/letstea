import os
from groq import Groq

client = Groq()
filename = "C:\\Users\\ashis\\OneDrive\\Documents\\GitHub\\voice-to-text-transcript-and-summary\\temp.mp3"

with open(filename, "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=(filename, file.read()),
        model="whisper-large-v3-turbo",
        response_format="verbose_json",
    )
    print(transcription.text)

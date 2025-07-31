from gtts import gTTS

# Load your markdown file and read the text
with open("almatsurat.md", "r", encoding="utf-8") as file:
    text = file.read()

# Convert the text to speech in Indonesian (language code 'id')
tts = gTTS(text, lang="id")

# Save the audio as an MP3 file
tts.save("output.mp3")

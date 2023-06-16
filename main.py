from google.cloud import speech
from http.client import HTTPException
import requests

from tkinter import Tk, Text, BOTH, END, Button, StringVar
import threading
import queue

from stt.stt import MicrophoneStream, listen_print_loop
import os
import simpleaudio
import wave
from pydub import AudioSegment
from gtts import gTTS
import asyncio
from gpt.api import get_result
from dotenv import load_dotenv

load_dotenv()
preset = requests.get('http://3.144.110.171:8000/prompt').text


class GPTalk:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.gui_queue = queue.Queue()  # Queue for communication with GUI
        self.input_task = None
        self.play_task = None
        self.stop_audio = None
        self.root = None  # Reference to tkinter root
        self.text = None  # Reference to tkinter text widget
        self.default_lang = None
        self.transcript = [
            {"role": "system", "content": preset},
        ]

    def _recognize(self):
        language_code = "ko-KR"  # a BCP-47 language tag
        first_lang = "en-US"
        second_lang = "ko-KR"
        RATE = 16000
        CHUNK = int(RATE / 10)  # 100ms

        client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=self.default_lang.get(),
            # alternative_language_codes=[second_lang],
            speech_contexts=[
                speech.SpeechContext(
                    phrases=["gp talk"],
                    boost=20.0
                ),
                speech.SpeechContext(
                    phrases=["daeyang"],
                    boost=20.0
                ),
            ],
        )

        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        with MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()
            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = client.streaming_recognize(streaming_config, requests)

            # Now, put the transcription responses to use.
            instruction = listen_print_loop(responses)
            # Add instruction to GUI queue
            self.gui_queue.put('User: ' + instruction)
            return instruction

    async def _input(self):
        """
        Get microphone input from user and put it into the queue
        """
        while True:
            t = await asyncio.get_event_loop().run_in_executor(None, self._recognize)
            if not t:
                await self.queue.put(t)
                self.play_task.cancel()
                return
            if t == 'q':
                self.stop_audio.set()
                continue
            await self.queue.put(t)

    async def _play(self):
        """
        Get text from the queue and playback the audio
        """
        while True:
            t = await self.queue.get()

            if not t:
                self.queue.task_done()
                return
            else:
                self.transcript.append({"role": "user", "content": t})
                try:
                    answer = requests.get(
                        'http://3.144.110.171:8000/instruction/search', params={"input_inst": t})
                    if answer.status_code == 404:
                        raise HTTPException
                    else:
                        answer = answer.json()
                except HTTPException:
                    answer = get_result(self.transcript)

                    data = {"input_inst": t, "input_answer": answer}
                    requests.post(
                        'http://3.144.110.171:8000/instruction/add', json=data)

                self.transcript.append(
                    {"role": "system", "content": answer})
                self.gui_queue.put('GPTalk: ' + answer)
                tts = gTTS(
                    text=answer, lang=self.default_lang.get().split('-')[0])

                tts.save("output.mp3")  # TODO 파일을 저장하지 않고 바로 재생하도록 수정

                w = AudioSegment.from_mp3('output.mp3')
                w.export('output.wav', format='wav')

                with wave.open('output.wav', 'rb') as wav_file:
                    audio_data = wav_file.readframes(wav_file.getnframes())
                    playback = simpleaudio.play_buffer(audio_data, wav_file.getnchannels(
                    ), wav_file.getsampwidth(), wav_file.getframerate())

                os.remove("output.mp3")
                os.remove("output.wav")

                while playback.is_playing():
                    await asyncio.sleep(0.1)
                    if self.stop_audio.is_set():
                        playback.stop()
                        self.stop_audio.clear()
                        break

    def main(self):
        self.root = Tk()
        self.clear_button = Button(
            self.root, text="Clear Transcript", command=self.clear_text)
        self.clear_button.pack()

        self.default_lang = StringVar(value='en-US')

        # Create radio buttons for 'English' and 'Korean'
        # self.radio_english = Radiobutton(
        #     self.root, text="English", variable=self.default_lang, value='en-US')
        # self.radio_korean = Radiobutton(
        #     self.root, text="Korean", variable=self.default_lang, value='ko-KR')

        # self.radio_english.pack()
        # self.radio_korean.pack()

        self.text = Text(self.root)
        self.text.pack(expand=True, fill=BOTH)

        self.root.title("GPTalk")
        self.root.geometry("720x480")

        threading.Thread(target=self.start_asyncio_loop).start()

        self.update_gui()
        self.root.mainloop()

    def clear_text(self):
        self.text.delete('1.0', END)
        self.transcript = [
            {"role": "system", "content": preset},
        ]

    def update_gui(self):
        while not self.gui_queue.empty():
            instruction = self.gui_queue.get()
            self.text.insert(END, instruction + '\n')
        # Check for new instructions every 100ms
        self.root.after(100, self.update_gui)

    def start_asyncio_loop(self):
        self.stop_audio = asyncio.Event()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                asyncio.gather(self._input(), self._play()))
        except Exception as e:
            # Handle your exception here
            print(e)
        finally:
            loop.close()


if __name__ == "__main__":
    gptalk = GPTalk()
    asyncio.run(gptalk.main())

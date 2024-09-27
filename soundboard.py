import pyaudio
import wave
import numpy as np
import os
import keyboard
import sounddevice as sd
from scipy.signal import resample
import threading

# List all audio devices and their properties
def list_audio_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    devices = []
    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        device_name = device_info.get('name')
        max_input_channels = device_info.get('maxInputChannels')
        max_output_channels = device_info.get('maxOutputChannels')
        default_sample_rate = device_info.get('defaultSampleRate')

        # Use sounddevice to get the current sample rate
        try:
            current_sample_rate = sd.query_devices(i)['default_samplerate']
        except Exception as e:
            current_sample_rate = default_sample_rate

        devices.append((i, device_name, max_input_channels, max_output_channels, current_sample_rate))

    p.terminate()
    return devices

# Prompt the user to select an audio device
def select_device(devices, device_type):
    print(f"Select {device_type} device:")
    for i, (index, name, max_input, max_output, sample_rate) in enumerate(devices):
        if (device_type == "microphone" and max_input > 0) or (device_type == "playback" and max_output > 0):
            print(f"{i}: {name} (Sample Rate: {sample_rate})")
    selected_index = int(input(f"Enter the number of the {device_type} device: "))
    return devices[selected_index]

# Load a WAV file and return its data and sample rate
def load_wave_file(filename):
    wf = wave.open(filename, 'rb')
    sample_rate = wf.getframerate()
    data = wf.readframes(wf.getnframes())
    wf.close()
    print(f"Loaded {filename} with sample rate {sample_rate}")
    return np.frombuffer(data, dtype=np.int16), sample_rate

# Resample audio data to match the target sample rate
def resample_audio(audio_data, original_rate, target_rate):
    if original_rate != target_rate:
        num_samples = int(len(audio_data) * float(target_rate) / original_rate)
        audio_data = resample(audio_data, num_samples)
    return audio_data

# Mix two audio streams
def mix_audio(input_audio, extra_audio):
    min_len = min(len(input_audio), len(extra_audio))
    mixed_audio = input_audio[:min_len] + extra_audio[:min_len]
    return mixed_audio

# Scan a folder for WAV files, load them into memory, and assign keyboard shortcuts to them
def scan_and_load_sound_effects(folder, target_sample_rate):
    sound_effects = {}
    for file in os.listdir(folder):
        if file.endswith(".wav"):
            key = input(f"Press a key to assign to {file}: ")
            filepath = os.path.join(folder, file)
            sound_data, sample_rate = load_wave_file(filepath)
            if sample_rate != target_sample_rate:
                sound_data = resample_audio(sound_data, sample_rate, target_sample_rate)
            sound_effects[key] = sound_data
    return sound_effects

# Function to play a sound effect in a separate thread
def play_sound_effect(sound_data, output_stream):
    output_stream.write(sound_data.tobytes())

def main():
    # List all audio devices
    devices = list_audio_devices()

    # Select microphone device
    mic_device = select_device(devices, "microphone")
    print("The first playback device you select should be your personal headphones.")
    # Select playback device for sound effects
    sound_effects_playback_device = select_device(devices, "playback")
    print("The second playback device you select should be the virtual audio cable.")
    # Select playback device for mixed audio (microphone + sound effects)
    mixed_playback_device = select_device(devices, "playback")

    # Print selected device sample rates
    print(f"Selected microphone device sample rate: {mic_device[4]}")
    print(f"Selected sound effects playback device sample rate: {sound_effects_playback_device[4]}")
    print(f"Selected mixed playback device sample rate: {mixed_playback_device[4]}")

    # Determine the folder to scan for sound effects based on the sample rate
    sample_rate_folder = f"soundeffects/{int(mic_device[4])}"
    if not os.path.exists(sample_rate_folder):
        print(f"Error: Folder {sample_rate_folder} does not exist.")
        return

    # Scan the folder for sound effects, load them into memory, and assign keyboard shortcuts
    sound_effects = scan_and_load_sound_effects(sample_rate_folder, int(mic_device[4]))

    p = pyaudio.PyAudio()

    # Open input stream for the microphone
    input_stream = p.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=int(mic_device[4]),
                          input=True,
                          input_device_index=mic_device[0],
                          frames_per_buffer=1024)

    # Open output stream for sound effects
    sound_effects_output_stream = p.open(format=pyaudio.paInt16,
                                         channels=1,
                                         rate=int(sound_effects_playback_device[4]),
                                         output=True,
                                         output_device_index=sound_effects_playback_device[0],
                                         frames_per_buffer=1024)

    # Open output stream for mixed audio (microphone + sound effects)
    mixed_output_stream = p.open(format=pyaudio.paInt16,
                                 channels=1,
                                 rate=int(mixed_playback_device[4]),
                                 output=True,
                                 output_device_index=mixed_playback_device[0],
                                 frames_per_buffer=1024)

    print("Recording and mixing audio...")

    # Dictionary to keep track of key states
    key_states = {key: False for key in sound_effects.keys()}

    def mixer():
        try:
            while True:
                # Read audio data from the microphone
                input_audio = input_stream.read(1024)
                input_audio_np = np.frombuffer(input_audio, dtype=np.int16)

                # Copy the input audio to mix with sound effects
                mixed_audio_np = input_audio_np.copy()

                # Check if any sound effect keys are pressed
                for key, sound_data in sound_effects.items():
                    if keyboard.is_pressed(key):
                        if not key_states[key]:
                            key_states[key] = True
                            # Start a new daemon thread to play the sound effect
                            threading.Thread(target=play_sound_effect, args=(sound_data, sound_effects_output_stream), daemon=True).start()
                            # Mix the sound effect with the input audio
                            mixed_audio_np = mix_audio(mixed_audio_np, sound_data)
                    else:
                        key_states[key] = False

                # Play the mixed audio on the mixed output stream
                mixed_output_stream.write(mixed_audio_np.tobytes())

        except KeyboardInterrupt:
            print("Stopping...")

        # Close all streams and terminate PyAudio
        input_stream.stop_stream()
        input_stream.close()
        sound_effects_output_stream.stop_stream()
        sound_effects_output_stream.close()
        mixed_output_stream.stop_stream()
        mixed_output_stream.close()
        p.terminate()

    # Start the mixer thread
    mixer_thread = threading.Thread(target=mixer)
    mixer_thread.start()

if __name__ == "__main__":
    main()
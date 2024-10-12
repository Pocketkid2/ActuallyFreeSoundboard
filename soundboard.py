import sounddevice as sd
import soundfile as sf
import os
import time
import queue
import keyboard

exit_condition = False

# List all audio devices
def list_audio_devices():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} (Channels: {device['max_input_channels']} in, {device['max_output_channels']} out, Sample Rate: {device['default_samplerate']})")

# Select an audio device
def select_device(device_type):
    list_audio_devices()
    device_index = int(input(f"Enter the number of the {device_type} device: "))
    return device_index

# Read and assign keys to sound files
def assign_keys_to_sounds(directory):
    sound_files = [f for f in os.listdir(directory) if f.endswith('.wav')]
    key_sound_map = {}
    for sound_file in sound_files:
        print(f"Press a key to assign to {sound_file}")
        event = None
        while True:
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_UP:
                print(f"{sound_file} assigned to {event.name}")
                key = event.scan_code
                key_sound_map[key] = os.path.join(directory, sound_file)
                break
    return key_sound_map

# Add to queue when key is pressed
def on_key_press(event, key_queue):
    print(f"{event.name} pressed")
    key_queue.put(event.scan_code)

def main():
    # Select microphone device
    print("\n\nThe first playback device you select should be your personal headphones.")
    mic_device = select_device("microphone")

    # Select playback device
    print("\n\nThe second playback device you select should be the virtual audio cable output/playback device.")
    playback_device = select_device("playback")

    # Pause so that the selection keys don't get mixed up with the soundboard keys
    time.sleep(1)

    # Assign keys to sound files
    sound_dir = 'soundeffects/44100'
    key_sound_map = assign_keys_to_sounds(sound_dir)

    # Queue to handle key presses
    key_queue = queue.Queue()
    keyboard.on_press(lambda event: on_key_press(event, key_queue))

    # Load sound files
    sound_data = {}
    for key, file_path in key_sound_map.items():
        data, samplerate = sf.read(file_path)
        sound_data[key] = (data, samplerate)

    # Buffer and playback position tracker
    playback_buffer = None
    playback_position = 0

    def play_sound_normally(sound_data, sample_rate):
        sd.play(sound_data, sample_rate)

    # Define a callback function to pass audio from the microphone to the playback device
    def callback(indata, outdata, frames, time, status):
        nonlocal playback_buffer, playback_position
        global exit_condition
        if status:
            print(status)
        outdata[:] = indata
        # Check for an unhandled key press
        if not key_queue.empty():
            key = key_queue.get()
            if key in sound_data:
                playback_buffer, sr = sound_data[key]
                play_sound_normally(playback_buffer, sr)
                playback_position = 0
                if sr != 44100:
                    print(f"Sample rate mismatch for {key}: expected 44100, got {sr}")
            if key == 'x':
                exit_condition = True
        # Check for currently playing sound in buffer
        if playback_buffer is not None:
            end_position = playback_position + frames
            if end_position < len(playback_buffer):
                outdata[:frames] += playback_buffer[playback_position:end_position]
                playback_position = end_position
            else:
                outdata[:len(playback_buffer) - playback_position] += playback_buffer[playback_position:]
                playback_buffer = None  # Stop playback

    # Open the input and output streams and pass audio from the microphone to the playback device
    with sd.Stream(device=(mic_device, playback_device), samplerate=44100, channels=2, callback=callback):
        print("Press Ctrl+C to stop.")
        try:
            # Repeat until exit condition is met
            while True:
                # Run audio for one second
                sd.sleep(1)
                # Check if exit condition is met
                if exit_condition:
                    break
        except KeyboardInterrupt:
            print("Exiting...")

    # Stop listening for key presses
    keyboard.unhook_all()

if __name__ == "__main__":
    main()
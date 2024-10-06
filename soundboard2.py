import sounddevice as sd

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

def main():
    # Select microphone device
    mic_device = select_device("microphone")
    print("The first playback device you select should be your personal headphones.")
    # Select playback device
    playback_device = select_device("playback")

    # Print selected devices
    print(f"Selected microphone device: {mic_device}")
    print(f"Selected playback device: {playback_device}")

    # Define a callback function to pass audio from the microphone to the playback device
    def callback(indata, outdata, frames, time, status):
        if status:
            print(status)
        outdata[:] = indata

    # Open the input and output streams and pass audio from the microphone to the playback device
    with sd.Stream(device=(mic_device, playback_device), samplerate=44100, channels=2, callback=callback):
        print("Press Ctrl+C to stop.")
        try:
            sd.sleep(int(1e6))  # Keep the stream open
        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == "__main__":
    main()
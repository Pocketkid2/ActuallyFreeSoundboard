# Not Malware Sound Mixer

A versatile tool that allows you to mix various sound snippets into your microphone's audio stream. Perfect for adding fun and creativity to video games and Discord calls!

The goals of this project are as follows:
- Free
- Open source
- Runs on windows
- No ads
- No spyware
- No viruses
- Passes through your primary mic with no issues or quality loss
- Allows you to add any kind of soundbite to the audio mix using any key or combination of keys
- Works in the background so you can run this while gaming or in a discord call or both
- Interface so simple and user-friendly, your grandma could figure it out

### Requirements
Python 3

### Installation
Run `./install_requirements.sh` in git bash

### Usage
Run `./start.sh` in git bash, the script will walk you through the rest

### Configuration
All sound files are loaded from the `soundeffects/<samplerate>` folder. Some samples are provided for you.

### How to create sounds
I followed this simple procedure to create the sample sound effects:
1. Use `youtube-dl` (or its fork `yt-dlp`) to download the youtube video containing the sound (tip: `-f140` grabs the 44.1khz audio, `-f251` grabs the 48khz audio)
2. Use Audacity to edit the clip down to the minimum size of just the soundbite
3. Export as signed 16-bit stereo (2ch) WAV into the soundeffects/`<samplerate>` folder

### Known bugs/issues
- Sounds don't play correctly. This is probably an issue to do with the mixing code, it all came from GitHub copilot so it's not that great.

### Future plans
None so far
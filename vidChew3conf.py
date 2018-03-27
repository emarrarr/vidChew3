### Do everything except encode
dryRun = True
### Print out some extra debug text
### Really only useful for seeing the audio track selection logic
debug = False

### Log all vidChew3 output (not including ffmpeg output)
doLogFile = True
### Generate a log for each ffmpeg invocation
ffmpegLogs = True

### Exit the script if ffmpeg fails
exitOnFail = False

### Output directory for encodes
destDir = ""

### fileTag will be appended to the end of output filenames
fileTag = "-myTag"

### Filenames containing a string in filenameSkipArray will be skipped
filenameSkipArray = [fileTag, 'vidChew']

### Desired language for audio/subtitle track in ISO 639-2 format
### https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes
targLang = "eng"

### ffmpeg video encoding settings
videoTargCodec = "libx265"
videoTargCodecPreset = "medium"
videoTargCrf = "22"

### Video downscaling options
videoDownscale = True
maxVidWidth = 1920
maxVidHeight = 1080
force16 = True

### Preferred audio formats during deep search, prioritized from left to right.
### Leave a blank string at the end to include a pass for formats not in your list.
prefAudioFormats = ['ac3', 'eac3', 'dts', 'aac', '']

### Audio reencoding options
audioReenc = True
### Force reencode of audio, even if input bitrate is lower than target bitrate
audioReencForce = False
audioReencCodec = "ac3"
audioReencBitRateStereo = 256
audioReencBitRateSurround = 640
audioReencChannelsSurround = 6

### Audio downmixing options
audioDownmix = False
audioDownmixCodec = "libfdk_aac"
audioDownmixChannels = 2
audioDownmixBitRate = 256

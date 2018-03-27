vidChew3
Copyright (C) 2018 \m/rr emarrarr@tuta.io

Usage: vidChew3

Dependencies: python3, ffmpeg, ffprobe, gzip, baseutils

Recursive batch video reencode script with optional video downscaling and audio downmixing via ffmpeg, written in Python, intended for Linux.

+ vidChew3 works within the current directory and will recurse through subfolders.

+ If a vidChew3conf.py file is placed in the current working directory, config variables will be read from it.  If not, config variables will be read from the Default Config section within the script below.

+ By default, vidChew3 outputs to the same folder the input resides in.  Output folder can be modified via the destDir config variable.
  
+ If an input filename contains a string in the filenameSkipArray, the input will be skipped. Inputs that can't be read by ffprobe will always be skipped.

+ If downscaling is disabled, video is reeconded at its original size.  If downscaling is enabled and input height or width is greater than maxVidWidth or maxVidHeight, then input is scaled to maxVidWidth and maxVidHeight.  Otherwise, input is not scaled (input is never upscaled).

+ If force16 is enabled, inputs that are being downscaled will be forced to 16:9 aspect ratio.  If input is not being downscaled, aspect ratio never changes.

+ If there is a single audio track, it is automatically selected.  If there are multiple audio tracks in the input, vidChew3 attempts to select the one with a codec highest in your prefAudioFormats array, in your targLang, and with the highest number of channels.  If these critera can't be met, the audio track in your targLang with the highest number of channels will be selected.  If language metadata is not available, the track with the highest number of channels is selected. 

+ If audioDownmix & audioReenc are both disabled, audio is copied from input.

+ If audioDownmix is enabled, audio is reencoded with audioDownmixChannels using audioDownmixCodec @ audioDownmixBitrate unless the input is already <= audioDownmixChannels channels, in which case it will be copied.

+ If audioReenc is enabled, audio is reencoded with audioReencChannelsSurround channels (if input channels > 2), 2 channels (if input is 2 channels), or 1 channel (if input is 1 channel) using audioReencCodec @ audioReencBitRateSurround or audioReencBitRateStereo, respectively.  If audioReencForce is enabled, audio will always be reencoded.  If not, audio will be copied if input audio bitrate is <= audioReencBitRateSurround / audioReencBitRateStereo. TrueHD (Dolby Atmos) audio is always reencoded with audioReencChannelsSurround using audioReencCodec @ audioReencBitRateSurround.

+ If audioDownmix & audioReenc are both enabled, vidChew3 will not run.

+ The first targLang subtitle track (if exist) is selected for the output mux.  If a targLang subtitle track isn't found, no subtitle track is included in the output mux.

+ The input subtitle track is copied if hdmv_pgs_subtitle or dvd_subtitle.  Otherwise, it is converted to ASS.
    
+ Video & audio tracks are set as default.  Subtitle track is set non-default.

+ No metadata (except audio/subtitle language) are copied.  Chapters are preserved.

+ Only alphanumeric characters, periods, dashes, and underscores are maintained in the destination filename.

vidChew3 was born out of a desire to translate vidChew2 to Python.  This was primarily an academic effort to teach myself a little Python, but I also wished to design a more reliable audio selection algorithm (for lack of a better word).  As it turns out, Python is quite a bit faster than bash, too ;P.  This is my first significant effort in Python and I am MORE than positive that I've broken many conventions / best practices and that MUCH of the code can be written in far superior ways.  That said, I hope you find it useful, in one capacity or another.

As with vidChew2, vidChew3 only supports a single audio/subtitle track.  I started working on this in an effort to migrate my AVC/h264 TV & movie collections to HEVC/h265 without the use of Handbrake.  It was obviously written specifically with 1080p/720p AVC (h264) and HEVC (h265) in mind and likely needs some changes to adequately support other codecs.  The config options are based on ffmpeg/ffprobe codec syntax, so it's important to respect it or else the script will likely just break.

I strongly recommend testing on short clips before committing to hours (or years) of encoding before realizing you weren't happy with your settings ;P

https://trac.ffmpeg.org/wiki/Seeking#Cuttingsmallsections

ffmpeg -ss 00:15:00.0 -i "<in>" -map 0 -c copy -t 00:00:10.0 "<out>"

As stated, this script could no doubt be signficantly improved.  If such things are up your alley, you have my love and feel free.  I'd be quite thrilled if you reached out and shared your work. ;]

Taste the rainbow...

<3

\m/

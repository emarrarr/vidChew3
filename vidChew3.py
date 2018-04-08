#!/usr/bin/env python3

ver = "0408182041"

################################################################################################################
###
### GNU General Public License v3 (GPLv3)
###
### This program is free software: you can redistribute it and/or modify
### it under the terms of the GNU General Public License as published by
### the Free Software Foundation, either version 3 of the License, or
### (at your option) any later version.
### 
### This program is distributed in the hope that it will be useful,
### but WITHOUT ANY WARRANTY; without even the implied warranty of
### MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
### GNU General Public License for more details.
### You should have received a copy of the GNU General Public License
### along with this program.  If not, see <http://www.gnu.org/licenses/>.
###
################################################################################################################
###
### vidChew3
### Copyright (C) 2018 \m/rr - emarrarr@tuta.io
###
### Usage: vidChew3
### Dependencies: python3, ffmpeg, ffprobe, gzip, coreutils
###
### Recursive batch video reencode script with optional video downscaling and audio downmixing via ffmpeg,
### written in Python, intended for Linux.
###
### - vidChew3 works within the current directory and will recurse through subfolders.
###
### - If a vidChew3conf.py file is placed in the current working directory, config variables will be read
###   from it.  If not, config variables will be read from the Default Config section within the script below.
###
### - By default, vidChew3 outputs to the same folder the input resides in.  Output folder can be modified via
###   the destDir config variable.
###   
### - If an input filename contains a string in the filenameSkipArray, the input will be skipped. Inputs that
###   can't be read by ffprobe will always be skipped.
###
### - If downscaling is disabled, video is reeconded at its original size.
###   	 + If downscaling is enabled and input height or width is greater than maxVidWidth
###	  	   or maxVidHeight, then input is scaled to maxVidWidth and maxVidHeight.  Otherwise,
###   	   input is not scaled (input is never upscaled).
###
### - If force16 is enabled, inputs that are being downscaled will be forced to 16:9 aspect ratio.
###      + If input is not being downscaled, aspect ratio never changes.
###
### - If there is a single audio track, it is automatically selected.  If there are multiple audio tracks
###   in the input, vidChew3 attempts to select the one with a codec highest in your prefAudioFormats array,
###   in your targLang, and with the highest number of channels.  If these critera can't be met, the audio
###   track in your targLang with the highest number of channels will be selected.  If language metadata is
###   not available, the track with the highest number of channels is selected. 
###
### - If audioDownmix & audioReenc are both disabled, audio is copied from input.
###
### - If audioDownmix is enabled, audio is reencoded with audioDownmixChannels using audioDownmixCodec @
###   audioDownmixBitrate unless the input is already <= audioDownmixChannels channels, in which case it
###   will be copied.
###
### - If audioReenc is enabled, audio is reencoded with audioReencChannelsSurround channels (if input
###   channels > 2), 2 channels (if input is 2 channels), or 1 channel (if input is 1 channel) using
###   audioReencCodec @ audioReencBitRateSurround or audioReencBitRateStereo, respectively.  If
###   audioReencForce is enabled, audio will always be reencoded.  If not, audio will be copied if input 
###   audio bitrate is <= audioReencBitRateSurround / audioReencBitRateStereo. TrueHD (Dolby Atmos) audio 
###   is always reencoded with audioReencChannelsSurround using audioReencCodec @ audioReencBitRateSurround.
###
###	- If audioDownmix & audioReenc are both enabled, vidChew3 will not run.
###
### - The first targLang subtitle track (if exist) is selected for the output mux.  If a targLang subtitle
###   track isn't found, no subtitle track is included in the output mux.
### 
### - The input subtitle track is copied if hdmv_pgs_subtitle or dvd_subtitle.  Otherwise, it is converted
###   to ASS.
###     
### - Video & audio tracks are set as default.  Subtitle track is set non-default.
###
### - No metadata (except audio/subtitle language) are copied.  Chapters are preserved.
###
### - Only alphanumeric characters, periods, dashes, and underscores are maintained in the destination
###   filename.
###
### vidChew3 was born out of a desire to translate vidChew2 to Python.  This was primarily an academic effort
### to teach myself a little Python, but I also wished to design a more reliable audio selection algorithm
### (for lack of a better word).  As it turns out, Python is quite a bit faster than bash, too ;P.  This is
### my first significant effort in Python and I am MORE than positive that I've broken many conventions
### / best practices and that MUCH of the code can be written in far superior ways.  That said, I hope
### you find it useful, in one capacity or another.
###
### As with vidChew2, vidChew3 only supports a single audio/subtitle track.  I started working on this in
### an effort to migrate my AVC/h264 TV & movie collections to HEVC/h265 without the use of Handbrake.  It
### was obviously written specifically with 1080p/720p AVC (h264) and HEVC (h265) in mind and likely needs
### some changes to adequately support other codecs.  The config options are based on ffmpeg/ffprobe codec
### syntax, so it's important to respect it or else the script will likely just break.
###
### I strongly recommend testing on short clips before committing to hours (or years) of
### encoding before realizing you weren't happy with your settings ;P
### https://trac.ffmpeg.org/wiki/Seeking#Cuttingsmallsections
### ffmpeg -ss 00:15:00.0 -i "<in>" -map 0 -c copy -t 00:00:10.0 "<out>"
###
### As stated, this script could no doubt be signficantly improved.  If such things are up your alley,
### you have my love and feel free.  I'd be quite thrilled if you reached out and shared your work. ;]
### 
### Taste the rainbow...
###
###		<3
###		\m/
###
################################################################################################################
###
### Version History (date +"%m%d%y%0k%M" -u)
###
### + 0408182041 - \m/rr
###      Initial release
###
################################################################################################################

import os, sys, json, string, re, subprocess, logging, time, datetime, types

### Get current working directory, add it to path (for config file), and start timers

runFrom = os.getcwd()
sys.path.insert(0, runFrom)

startTime = datetime.datetime.now().strftime("%m/%d/%y %H:%M:%S")
startTimer = time.time()

### Determine whether config file exists

configPath = runFrom + "/" + "vidChew3conf.py"

if os.path.isfile(configPath):
	
	usingConfig = True
	from vidChew3conf import *	
	
else:
	
	usingConfig = False
	
##### Default Config #####

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

##### Default Config End #####

##### Functions #####

### Define a function that changes log handlers to produce blank lines without a prefix

def log_newline(self, how_many_lines=1):
	
	self.removeHandler(self.console_handler)
	if doLogFile: self.removeHandler(self.file_handler)
	self.addHandler(self.blank_handler)
	if doLogFile: self.addHandler(self.file_handler_blank)
	for i in range(how_many_lines):
		self.info('')

	self.removeHandler(self.blank_handler)
	if doLogFile: self.removeHandler(self.file_handler_blank)
	self.addHandler(self.console_handler)
	if doLogFile: self.addHandler(self.file_handler)
	
### Create a logger object to handle text output and optionally write a logfile

def create_logger(loggingType=0, loggingPath=""):
	
	logFormatter = logging.Formatter("[vidChew3] : %(asctime)s %(message)s",  "%m%d%y%H%M%S")

	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setLevel(logging.INFO)
	console_handler.setFormatter(logFormatter)

	blank_handler = logging.StreamHandler()
	blank_handler.setLevel(logging.INFO)
	blank_handler.setFormatter(logging.Formatter(fmt=''))
	
	if loggingType == 1:
		
		logDate = '{0:%m%d%y%H%M%S}'.format(datetime.datetime.now())
		logFilename = "vidChew3-" + logDate
		file_handler = logging.FileHandler("{0}/{1}.log".format(loggingPath,logFilename))
		file_handler.setLevel(logging.INFO)
		file_handler.setFormatter(logFormatter)
		
		logDate = '{0:%m%d%y%H%M%S}'.format(datetime.datetime.now())
		logFilename = "vidChew3-" + logDate
		file_handler_blank = logging.FileHandler("{0}/{1}.log".format(loggingPath,logFilename))
		file_handler_blank.setLevel(logging.INFO)
		file_handler_blank.setFormatter(logging.Formatter(fmt=''))

	logger = logging.getLogger('logging_test')
	logger.setLevel(logging.INFO)
	logger.addHandler(console_handler)
	if loggingType == 1: logger.addHandler(file_handler)

	logger.console_handler = console_handler
	logger.blank_handler = blank_handler
	if loggingType == 1: logger.file_handler = file_handler
	if loggingType == 1: logger.file_handler_blank = file_handler_blank
	logger.newline = types.MethodType(log_newline, logger)

	return logger
	
##### Functions End #####

### Check for an argument

if len(sys.argv) > 1:
	print("!! This script doesn't accept any arguments!")
	print("!! It's intended to run recursively on the current directory")
	quit()
else:
	specifiedInputFolder = "."
	
### Check to see if destDir exists

if destDir != "":
	if os.path.isdir(destDir) == False:
		print("!! destDir (%s) does not exist!" % destDir)
		quit()
	
### Create logger for status output / log writing

if doLogFile:
	logFolder = os.path.abspath(specifiedInputFolder)
	logger = create_logger(1, logFolder)
else:
	logger = create_logger()
	
### Say hello!

inputFolder = os.path.abspath(specifiedInputFolder)
	
logger.newline()
logger.info("!! vidChew3 by \m/rr :: %s" % ver)
logger.info("!! startTime: %s" % str(startTime))
logger.info("!! inputFolder: %s" % inputFolder)
if usingConfig: logger.info("++ Using config: %s" % configPath)
if not usingConfig: logger.info("-- Using internal config")
if dryRun: logger.info("-- Dry run enabled!")
if debug: logger.info("** Debugging output enabled!")

if audioReenc and audioDownmix:
	logger.newline()
	logger.info("!! Audio reencoding and downmixing cannot both be enabled!")
	logger.newline()
	quit()
	
### Walk input folder and process

for root, subdirs, files in os.walk(inputFolder):
	for filename in sorted(files):
		
		fullInputFile = os.path.join(root, filename)
		inputAbsPath = os.path.abspath(fullInputFile)
		inputPath, inputFile = os.path.split(inputAbsPath)
		inputBaseFile = os.path.splitext(inputFile)[0]
		logger.newline()
		logger.info("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
		logger.info('! Input: %s' % (inputFile))
		logger.info('! Folder: %s' % (root))
		logger.info("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
		logger.newline()
		
		### Determine whether or not to skip based on filenameSkipArray
		
		doSkip = False
			
		for skip in filenameSkipArray:
			if skip in inputFile:
				logger.info("!! Filename contains \"%s\"!  Skipping..." % (skip))
				doSkip = True
		if doSkip: continue
		
		### Obtain input filesize, convert to MB
		
		inputSize = os.stat(inputAbsPath)
		inputSize = int(inputSize.st_size) / 1000000
		inputSize = str(round(inputSize, 2))

		### Obtain ffprobe output in json format, decode, and parse

		try:
			jsonBytes = subprocess.check_output(["ffprobe", "-v", "quiet", inputAbsPath, "-print_format", "json", "-show_format", "-show_streams"])
		except subprocess.CalledProcessError as ffprobeexc:
			logger.info("!! Could not retrieve input video info via ffprobe!")
			logger.newline()
			continue
		
		jsonText = jsonBytes.decode('utf-8')

		data = json.loads(jsonText)
		
		### Determine overall bitrate of input
		
		if "bit_rate" in data["format"]:
			overallBitrate = data["format"]["bit_rate"]
			overallBitrate = int(overallBitrate) / 1000
			overallBitrate = str(round(overallBitrate, 2))
		else:
			overallBitrate = "unknown"
		
		### Count streams

		logger.info("-+- Track Selection -+-")
		logger.newline()
		logger.info("++ Number of streams: %s (%s MB | %s kb/s)" % (len(data["streams"]), inputSize, overallBitrate))
		logger.newline()
		
		### Choose first video track
		
		logger.info(":: Video")
		
		videoFound = False
		bfVideoIndex = 0
		bfVideoCodecName =""
		bfVideoBitrate = 0
		bfVideoBitrateDisplay = ""
		bfVideoWidth = ""
		bfVideoHeight = ""
		bfVideoDisplayAr = ""
		targVidTrack = ""
		targVidTrack = ""
					
		for i in data["streams"]:
			if i["codec_type"] == "video":
				if 'index' in i:
					index = i["index"]
				else:
					index = "unknown"
				if 'codec_name' in i:
					codecName = i["codec_name"]
				else:
					codecName = "unknown"
				if 'bit_rate' in i:
					bitRate = i["bit_rate"]
					bitRate = int(bitRate) / 1000
					bitRate = int(bitRate)
					bitRateDisplay = bitRate
				else:
					bitRate = 0
					bitRateDisplay = "unknown"
				if 'width' in i:
					width = i["width"]
				else:
					width = "unknown"
				if 'height' in i:
					height = i["height"]
				else:
					height = "unknown"
				if 'display_aspect_ratio' in i:
					ar = i["display_aspect_ratio"]
				else:
					ar = "unknown"
				
				bfVideoIndex = index
				bfVideoCodecName = codecName
				bfVideoBitrate = bitRate
				bfVideoBitrateDisplay = bitRateDisplay
				bfVideoWidth = width
				bfVideoHeight = height
				bfVideoDisplayAr = ar
				videoFound = True
				break		
						
		if videoFound:
			logger.info("!! Chose first video track!")
			logger.info("\t index: %s | codecName: %s | Resolution: %sx%s (%s)" % (bfVideoIndex, bfVideoCodecName, bfVideoWidth, bfVideoHeight, bfVideoDisplayAr))
			targVidTrack = str(bfVideoIndex)
			targVidTrackMap = "-map 0:" + targVidTrack
		else:
			logger.info("!! No video track found!")
			

		### Count & display all audio streams
		
		logger.newline()
		logger.info(":: Audio")

		audioStreamCount = 0
		for i in data["streams"]:
			if i["codec_type"] == 'audio':
				audioStreamCount += 1
		logger.info("++ Number of audio streams: %s" % (audioStreamCount))
		
		for i in data["streams"]:
				if i["codec_type"] == "audio":
					if 'index' in i:
						index = i["index"]
					else:
						index = "unknown"
					if "tags" in i:
						if 'language' in i["tags"]:
							language = i["tags"]["language"]
						else:
							language = "unknown"
					else:
						language = "unknown"
					if 'codec_name' in i:
						codecName = i["codec_name"]
					else:
						codecName = "unknown"
					if 'channels' in i:
						channels = i["channels"]
						channels = int(channels)
						channelsDisplay = channels
					else:
						channels = 0
						channelsDisplay = "unknown"
					if 'bit_rate' in i:
						bitRate = i["bit_rate"]
						bitRate = int(bitRate) / 1000
						bitRate = int(bitRate)
						bitRateDisplay = bitRate
					elif codecName == "dts":
						if 'profile' in i:
							if i['profile'] == "DTS-HD MA":
								codecName = "dts-hd ma"
								bitRate = 1536
								bitRateDisplay = str(bitRate)
							else:
								bitRate = 0
								bitRateDisplay = "unknown"	
						else:
							bitRate = 0
							bitRateDisplay = "unknown"
					elif codecName == "truehd":
						bitRate = 18000
						bitRateDisplay = str(bitRate) + " (max)"
					else:
						bitRate = 0
						bitRateDisplay = "unknown"
					
					logger.info("\t index: %s | language: %s | codecName: %s | channels: %s | bitRate: %s kb/s" % (index, language, codecName, channelsDisplay, bitRateDisplay))

		### Determine audio stream

		audioFound = False
		bfAudioIndex = ""
		bfAudioLanguage = ""
		bfAudioCodecName = ""
		bfAudioChannels = 0
		bfAudioChannelsDisplay = ""
		bfAudioBitrate = 0
		bfAudioBitrateDisplay = ""
		targAudioTrack = ""
		targAudioTrackMap = ""
		targAudioTrackTag = ""

		if audioStreamCount == 1:
			logger.info("++ Only one audio track found, choosing...")
			for i in data["streams"]:
				if i["codec_type"] == "audio":
					if 'index' in i:
						index = i["index"]
					else:
						index = "unknown"
					if "tags" in i:
						if 'language' in i["tags"]:
							language = i["tags"]["language"]
						else:
							language = "unknown"
					else:
						language = "unknown"
					if 'codec_name' in i:
						codecName = i["codec_name"]
					else:
						codecName = "unknown"
					if 'channels' in i:
						channels = i["channels"]
						channels = int(channels)
						channelsDisplay = channels
					else:
						channels = 0
						channelsDisplay = "unknown"
					if 'bit_rate' in i:
						bitRate = i["bit_rate"]
						bitRate = int(bitRate) / 1000
						bitRate = int(bitRate)
						bitRateDisplay = bitRate
					elif codecName == "dts":
						if 'profile' in i:
							if i['profile'] == "DTS-HD MA":
								codecName = "dts-hd ma"
								bitRate = 1536
								bitRateDisplay = str(bitRate)
							else:
								bitRate = 0
								bitRateDisplay = "unknown"	
						else:
							bitRate = 0
							bitRateDisplay = "unknown"
					elif codecName == "truehd":
						bitRate = 18000
						bitRateDisplay = str(bitRate) + " max"
					else:
						bitRate = 0
						bitRateDisplay = "unknown"
					
					if debug:
						logger.info("** index: %s" % index)
						logger.info("** language: %s" % language)
						logger.info("** codecName: %s" % codecName)
						logger.info("** channels: %s" % channelsDisplay)
						logger.info("** bitRate (kbps): %s" % bitRateDisplay)
						logger.newline()
					
					bfAudioIndex = index
					bfAudioLanguage = language
					bfAudioCodecName = codecName
					bfAudioChannels = channels
					bfAudioChannelsDisplay = channelsDisplay
					bfAudioBitrate = bitRate
					bfAudioBitrateDisplay = bitRateDisplay
					audioFound = True
					break

		elif audioStreamCount > 1:
			logger.info("++ Multiple audio tracks found, deep searching...")
			for f in prefAudioFormats:
				for i in data["streams"]:
					if i["codec_type"] == "audio":
						if 'index' in i:
							index = i["index"]
						else:
							index = "unknown"
						if "tags" in i:
							if 'language' in i["tags"]:
								language = i["tags"]["language"]
							else:
								language = "unknown"
						else:
							language = "unknown"
						if 'codec_name' in i:
							codecName = i["codec_name"]
						else:
							codecName = "unknown"
						if 'channels' in i:
							channels = i["channels"]
							channels = int(channels)
							channelsDisplay = channels
						else:
							channels = 0
							channelsDisplay = "unknown"
						if 'bit_rate' in i:
							bitRate = i["bit_rate"]
							bitRate = int(bitRate) / 1000
							bitRate = int(bitRate)
							bitRateDisplay = bitRate
						elif codecName == "dts":
							if 'profile' in i:
								if i['profile'] == "DTS-HD MA":
									codecName = "dts-hd ma"
									bitRate = 1536
									bitRateDisplay = str(bitRate)
								else:
									bitRate = 0
									bitRateDisplay = "unknown"	
							else:
								bitRate = 0
								bitRateDisplay = "unknown"
						elif codecName == "truehd":
							bitRate = 18000
							bitRateDisplay = str(bitRate) + " max"
						else:
							bitRate = 0
							bitRateDisplay = "unknown"
						
						if debug:
							logger.info("** f: %s", f)
							logger.info("** index: %s" % index)
							logger.info("** language: %s" % language)
							logger.info("** codecName: %s" % codecName)
							logger.info("** channels: %s" % channelsDisplay)
							logger.info("** bitRate (kbps): %s" % bitRateDisplay)
							logger.newline()
						
						if f != "":
							if (language == targLang and codecName == f and channels > bfAudioChannels):
								if debug == 1:
									logger.info("** This is the best found audio track!")
									logger.newline()
								bfAudioIndex = index
								bfAudioLanguage = language
								bfAudioCodecName = codecName
								bfAudioChannels = channels
								bfAudioChannelsDisplay = channelsDisplay
								bfAudioBitrate = bitRate
								bfAudioBitrateDisplay = bitRateDisplay
								audioFound = True
						else:
							if (language == targLang and channels > bfAudioChannels):
								if debug == 1:
									logger.info("** This is the best found audio track!")
									logger.newline()
								bfAudioIndex = index
								bfAudioLanguage = language
								bfAudioCodecName = codecName
								bfAudioChannels = channels
								bfAudioChannelsDisplay = channelsDisplay
								bfAudioBitrate = bitRate
								bfAudioBitrateDisplay = bitRateDisplay
								audioFound = True
							elif (channels > bfAudioChannels):
								if debug == 1:
									logger.info("** This is the best found audio track!")
									logger.newline()
								bfAudioIndex = index
								bfAudioLanguage = language
								bfAudioCodecName = codecName
								bfAudioChannels = channels
								bfAudioChannelsDisplay = channelsDisplay
								bfAudioBitrate = bitRate
								bfAudioBitrateDisplay = bitRateDisplay
								audioFound = True											

		else:
			logger.info("!! No audio tracks found!")
			logger.newline()
			audioFound = False

		if audioFound:
			logger.newline()
			logger.info("!! Audio Track Chosen!")
			logger.info("\t index: %s | language: %s | codecName: %s | channels: %s | bitRate: %s kb/s" % (bfAudioIndex, bfAudioLanguage, bfAudioCodecName, bfAudioChannelsDisplay, bfAudioBitrateDisplay))
			logger.newline()
			targAudioTrack = str(bfAudioIndex)
			targAudioTrackMap = "-map 0:" + targAudioTrack
			if bfAudioLanguage != "unknown":
				targAudioTrackTag = "-metadata:s:1 language=" + bfAudioLanguage
			else:
				targAudioTrackTag = ""
		else:
			logger.info("!! No audio track found!")
			logger.newline()
			
		### Count & display all subtitle streams
		
		logger.info(":: Subtitle")
				
		subStreamCount = 0
		for i in data["streams"]:
			if i["codec_type"] == 'subtitle':
				subStreamCount += 1
		logger.info("++ Number of subtitle streams: %s" % subStreamCount)

		for i in data["streams"]:
			if i["codec_type"] == "subtitle":
				if 'index' in i:
					index = i["index"]
				else:
					index = "unknown"
				if "tags" in i:
					if 'language' in i["tags"]:
						language = i["tags"]["language"]
					else:
						language = "unknown"
				else:
					language = "unknown"
				if 'codec_name' in i:
					codecName = i["codec_name"]
				else:
					codecName = "unknown"
				
				logger.info("\t index: %s | language: %s | codecName: %s" % (index, language, codecName))
				
		### Determine targLang subtitle stream, if exist
		
		subtitleFound = False
		bfSubtitleIndex = 0
		bfSubtitleLanguage = ""
		bfSubtitleCodecLang =""
		targSubTrack = ""
		targSubTrackMap = ""
		targSubTrackTag = ""
		subOpt = ""

		for i in data["streams"]:
			if i["codec_type"] == "subtitle":
				if 'index' in i:
					index = i["index"]
				else:
					index = "unknown"
				if "tags" in i:
					if 'language' in i["tags"]:
						language = i["tags"]["language"]
					else:
						language = "unknown"
				else:
					language = "unknown"
				if 'codec_name' in i:
					codecName = i["codec_name"]
				else:
					codecName = "unknown"
				
				if (language == targLang):
					if debug == 1:
						logger.info("** This is the best found subtitle track!")
						logger.newline()
					bfSubtitleIndex = index
					bfSubtitleLanguage = language
					bfSubtitleCodecName = codecName
					subtitleFound = True
					break
					
		if subtitleFound:
			logger.newline()
			logger.info("!! Subtitle Track Chosen!")
			logger.info("\t index: %s | language: %s | codecName: %s" % (bfSubtitleIndex, bfSubtitleLanguage, bfSubtitleCodecName))
			targSubTrack = str(bfSubtitleIndex)
			targSubTrackMap = "-map 0:" + targSubTrack
			targSubTrackTag = "-metadata:s:2 language=" + bfSubtitleLanguage
			if bfSubtitleCodecName == "hdmv_pgs_subtitle" or bfSubtitleCodecName == "dvd_subtitle":
				subOpt = "-c:s copy"
			else:
				subOpt = ""
		else:
			logger.info("!! No %s subtitle track found!" %(targLang))
			targSubTrack = ""
			targSubTrackMap = ""
			targSubTrackTag = ""	
			
		### Video downscaling
		
		doDownscale = False
		doForce16 = False
		
		if videoDownscale:
			if bfVideoWidth > maxVidWidth or bfVideoHeight > maxVidHeight:
				doDownscale = True
				scaleOpt = "-vf scale=" + str(maxVidWidth) + ":" + str(maxVidHeight)
				targVidWidth = maxVidWidth
				targVidHeight = maxVidHeight
				if force16:
					if bfVideoDisplayAr != "16:9":
						doForce16 = True
						scaleOpt = scaleOpt + ",setdar=dar=16/9"
			else:
				scaleOpt = ""
				targVidWidth = bfVideoWidth
				targVidHeight = bfVideoHeight
		else:
			scaleOpt = ""
			targVidWidth = bfVideoWidth
			targVidHeight = bfVideoHeight
			
		### Audio wasn't found
		
		if not audioFound:
			audioOpt = "-an"
			
		### Fallback audio options
		
		if audioFound and not audioReenc and not audioDownmix:
			audioOpt = "-c:a" + " " + "copy"
			tagAudio = bfAudioCodecName
			tagChannels = str(bfAudioChannels)
			
		### Audio reencoding
		
		doReencAudio = False
		
		if audioFound:
			if audioReenc:
				if debug : logger.info("** Reencoding audio!")
				if bfAudioBitrate != 0:
					if debug : logger.info("** Audio bitrate is non-zero")
					if bfAudioChannels > 2:
						if debug : logger.info("** There are more than 2 audio channels")
						if not audioReencForce:
							if debug : logger.info("** audioReencForce is NOT enabled")
							if bfAudioBitrate <= audioReencBitRateSurround:
								if debug : logger.info("** The input bitrate (%s) is <= the desired bitrate (%s) (surround)" % (bfAudioBitrate, audioReencBitRateSurround))
								doReencAudio = False
								audioOpt = "-c:a copy"
								tagAudio = bfAudioCodecName
								tagChannels = str(bfAudioChannels)
							else:
								if debug : logger.info("** The input bitrate (%s) > than the desired bitrate (%s) (surround)" % (bfAudioBitrate, audioReencBitRateSurround))
								doReencAudio = True
								audioOpt = "-c:a" + " " + audioReencCodec + " " + "-b:a" + " " + str(audioReencBitRateSurround) + "k" + " " + "-ac" + " " + str(audioReencChannelsSurround)
								tagAudio = audioReencCodec
								tagChannels = str(audioReencChannelsSurround)
						else:
							if debug : logger.info("** audioReencForce IS enabled")
							doReencAudio = True
							audioOpt = "-c:a" + " " + audioReencCodec + " " + "-b:a" + " " + str(audioReencBitRateSurround) + "k" + " " + "-ac" + " " + str(audioReencChannelsSurround)
							tagAudio = audioReencCodec
							tagChannels = str(audioReencChannelsSurround)							
					else:
						if debug : logger.info("** There are 2 or less audio channels")
						if not audioReencForce:
							if debug : logger.info("** audioReencForce is NOT enabled")
							if bfAudioBitrate <= audioReencBitRateStereo:
								if debug : logger.info("** The input bitrate (%s) <= than the desired bitrate (%s) (stereo)" % (bfAudioBitrate, audioReencBitRateStereo))
								doReencAudio = False
								audioOpt = "-c:a" + " " + "copy"
								tagAudio = bfAudioCodecName
								tagChannels = str(bfAudioChannels)
							else:
								if debug : logger.info("** The input bitrate (%s) is > the desired bitrate (%s) (stereo)" % (bfAudioBitrate, audioReencBitRateStereo))
								doReencAudio = True
								audioOpt = "-c:a" + " " + audioReencCodec + " " + "-b:a" + " " + str(audioReencBitRateStereo) + "k"
								tagAudio = audioReencCodec
								tagChannels = str(bfAudioChannels)
						else:
							if debug : logger.info("** audioReencForce IS enabled")
							doReencAudio = True
							audioOpt = "-c:a" + " " + audioReencCodec + " " + "-b:a" + " " + str(audioReencBitRateStereo) + "k"
							tagAudio = audioReencCodec
							tagChannels = str(bfAudioChannels)
				else:
					if debug : logger.info("** The input bitrate is 0/unknown")
					doReencAudio = False
					audioOpt = "-c:a" + " " + "copy"
					tagAudio = bfAudioCodecName
					tagChannels = str(bfAudioChannels)
			
		### Force reencode of TrueHD audio (if reencoding is enabled)
			
		if audioFound:
			if audioReenc:
				if bfAudioCodecName == "truehd":
					doReencAudio = True
					audioOpt = "-c:a" + " " + audioReencCodec + " " + "-b:a" + " " + str(audioReencBitRateSurround) + "k" + " " + "-ac" + " " + str(audioReencChannelsSurround)
					tagAudio = audioReencCodec
					tagChannels = audioReencChannelsSurround
				
		### Audio downmixing
		
		doDownmix = False
			
		if audioDownmix:
			if bfAudioChannels <= audioDownmixChannels:
				doDownmix = False
				audioOpt = "-c:a" + " " + "copy"
				tagAudio = bfAudioCodecName
				tagChannels = str(bfAudioChannels)
			else:
				doDownmix = True
				audioOpt = "-c:a" + " " + audioDownmixCodec + " " + "-b:a" + " " + str(audioDownmixBitRate) + "k" + " " + "-ac" + " " + str(audioDownmixChannels)
				tagAudio = audioDownmixCodec
				tagChannels = str(audioDownmixChannels)
		
		### Construct destination filename/path
			
		if targVidWidth == 1920:
			tagRes = "1080p"
		elif targVidHeight == 1280:
			tagRes = "720p"
		else:
			tagRes = str(bfVideoHeight) + "p"
			
		if videoTargCodec == "libx265":
			tagCodec = "HEVC"
			tagEncoder = "x265"
		elif videoTargCodec == "libx264":
			tagCodec = "AVC"
			tagEncoder = "x264"
		else:
			tagCodec = "tagCodec"
			tagEncoder = "tagEncoder"
		
		tagChannels = str(tagChannels) + "ch"
		
		if tagAudio == "libopus": tagAudio = "OPUS"
		if tagAudio == "libvorbis": tagAudio = "OGG"
		if tagAudio == "vorbis": tagAudio = "OGG"
		if tagAudio == "libfdk_aac": tagAudio = "AAC"
		if tagAudio == "libmp3lame": tagAudio = "MP3"
		if tagAudio == "libtwolame": tagAudio = "MP2"
		if tagAudio == "mp2": tagAudio = "MP2"
		if tagAudio == "wmav2": tagAudio = "WMA"
		if tagAudio == "wmav1": tagAudio = "WMA"
		
		tagAudio = tagAudio.upper()
		
		newName = inputBaseFile + "." + tagRes + "." + tagCodec + "." + tagEncoder + "." + tagChannels + "." + tagAudio + fileTag + ".mkv"
		
		anPattern = re.compile('[^a-zA-Z0-9_.-]')
		newName = anPattern.sub('', newName)
		
		if destDir == "":
			finalDest = os.path.join(root, newName)
		else:
			finalDest = os.path.join(destDir, newName)
			
		if debug:
			logger.newline()
			logger.info('** Filename Construction')
			logger.info(inputAbsPath)
			logger.info(inputPath)
			logger.info(inputFile)
			logger.info(inputBaseFile)
			logger.info(finalDest)
			
			
		### Pre-encode data summary
		
		if tagCodec != "tagCodec" and tagEncoder != "tagEncoder":
			outputVidFormat = tagCodec + " / " + tagEncoder
		else:
			outputVidFormat = videoTargCodec
			
		if doDownscale:
			outputVidWidth = maxVidWidth
			outputVidHeight = maxVidHeight
		else:
			outputVidWidth = bfVideoWidth
			outputVidHeight = bfVideoHeight
			
		if doForce16:
			outputVidAr = "16:9"
		else:
			outputVidAr = bfVideoDisplayAr
			
		if audioOpt == "-c:a copy":
			outputAudCodec = bfAudioCodecName
			outputAudBit = bfAudioBitrateDisplay
			outputAudChannels = bfAudioChannelsDisplay
		else:
			if doReencAudio:
				if bfAudioChannels > 2:
					outputAudCodec = audioReencCodec
					outputAudBit = str(audioReencBitRateSurround)
					outputAudChannels = str(audioReencChannelsSurround)
				else:
					outputAudCodec = audioReencCodec
					outputAudBit = str(audioReencBitRateStereo)
					outputAudChannels = bfAudioChannelsDisplay
			if doDownmix:
				outputAudCodec = audioDownmixCodec
				outputAudBit = str(audioDownmixBitRate)
				outputAudChannels = str(audioDownmixChannels)
		
		prefAudioFormatsList = ' '.join(prefAudioFormats)
		
		if subOpt == "":
			outputSubtitleCodec = "ass"
		else:
			outputSubtitleCodec = bfSubtitleCodecName
		
		logger.newline()
		logger.info("-+- Input -+-")
		logger.newline()
		logger.info("++ %s (%s MB | %s kb/s)" % (inputFile, inputSize, overallBitrate))
		logger.newline()
		logger.info(":: Video")
		logger.info("\t track: %s | %sx%s (%s) | codec: %s" % (targVidTrack, bfVideoWidth, bfVideoHeight, bfVideoDisplayAr, bfVideoCodecName))
		logger.newline()
		if audioFound: logger.info(":: Audio")
		if audioFound: logger.info("\t track: %s | language: %s | %s @ %s kb/s (%s ch)" % (targAudioTrack, bfAudioLanguage, bfAudioCodecName, bfAudioBitrateDisplay, bfAudioChannelsDisplay))
		if audioFound: logger.newline()
		if subtitleFound: logger.info(":: Subtitle")
		if subtitleFound: logger.info("\t index: %s | language: %s | codecName: %s" % (bfSubtitleIndex, bfSubtitleLanguage, bfSubtitleCodecName))
		if subtitleFound: logger.newline()
		logger.info("-+- Options -+-")
		logger.newline()
		logger.info("\t targLang: %s" % targLang)
		if videoDownscale: logger.info("\t videoDownscale: %s | %sx%s | force16: %s" % (str(videoDownscale), str(maxVidWidth), str(maxVidHeight), str(force16)))
		logger.info("\t preferredAudioFormats: %s" % prefAudioFormatsList)
		if audioReenc: logger.info("\t audioReenc: %s | %s @ %s (surround, %s ch) / %s (stereo) kb/s" % (str(audioReenc), audioReencCodec, str(audioReencBitRateSurround), str(audioReencChannelsSurround), str(audioReencBitRateStereo)))
		if audioReenc and audioReencForce: logger.info("\t audioReencForce: enabled")
		if audioDownmix: logger.info("\t audioDownmix: %s | %s @ %s kb/s (%s ch)" % (str(audioDownmix), audioDownmixCodec, str(audioDownmixBitRate), str(audioDownmixChannels)))
		logger.info("\t fileTag: %s" % fileTag)
		logger.newline()		
		logger.info("-+- Output -+-")
		logger.newline()
		logger.info(":: Video")
		logger.info("\t %s | preset: %s | crf: %s | %sx%s (%s)" % (outputVidFormat, videoTargCodecPreset, videoTargCrf, outputVidWidth, outputVidHeight, outputVidAr))
		if videoDownscale and not doDownscale: logger.info("\t !! Downscaling unnecessary")
		if videoDownscale:
			if force16 and not doForce16: logger.info("\t !! Forcing of 16:9 aspect ratio unnecessary") 
		logger.newline()
		if audioFound: logger.info(":: Audio")
		if audioFound: logger.info("\t language: %s | %s @ %s kb/s (%s ch)" % (bfAudioLanguage, outputAudCodec, outputAudBit, outputAudChannels))
		if audioFound and audioReenc and not doReencAudio: logger.info("\t !! Not reencoding audio because input audio track bitrate (%s kb/s) is either <= target bitrate (%s [surround] / %s [stereo] kb/s) or is unknown" % (bfAudioBitrateDisplay, str(audioReencBitRateSurround), str(audioReencBitRateStereo)))
		if audioFound and audioDownmix and not doDownmix: logger.info("\t !! Not downmixing audio because input audio track (%s) is already <= target downmix channels (%s)" % (bfAudioChannelsDisplay, str(audioDownmixChannels)))
		if subtitleFound: logger.newline()
		if subtitleFound: logger.info(":: Subtitle")
		if subtitleFound: logger.info("\t language: %s | codec: %s" % (bfSubtitleLanguage, outputSubtitleCodec))
		
		### Encode
		
		logger.newline()
		logger.info("-+- Encode -+-")
		logger.newline()
		logger.info("!! Destination: %s" % (finalDest))
		
		### Enable ffmpeg logging, if requested
		
		if ffmpegLogs:
			destAbsPath = os.path.abspath(finalDest)
			finalPath, finalFile = os.path.split(destAbsPath)
			reportFilename = finalFile + "-report.log"
			reportDest = inputPath + "/" + reportFilename
			logger.info("++ ffmpeg log: %s" % reportFilename)
			reportOpt = "FFREPORT=file=\"" + reportDest + "\":level=40"
		else:
			reportOpt = ""
			
		### Construct, echo, and exec ffmpeg cmd
			
		sC = " "
		
		encodeCmd = reportOpt + sC + '</dev/null' + sC + 'ffmpeg -y -v verbose -i' + sC + '"' + inputAbsPath + '"' + sC + targVidTrackMap + sC + targAudioTrackMap + sC + targSubTrackMap + sC + targAudioTrackTag + sC + targSubTrackTag + sC + scaleOpt + sC + '-c:v' + sC + videoTargCodec + sC + '-preset' + sC + videoTargCodecPreset + sC + '-crf' + sC + videoTargCrf + sC + audioOpt + sC + subOpt + sC + '-disposition:v:0 1 -disposition:a:0 1 -disposition:s:0 0 -map_metadata -1' + sC + '"' + finalDest + '"'
		logger.newline()
		logger.info("!! exec: %s" % encodeCmd)
		logger.newline()
		
		if not dryRun:
			
			ffmpegFailed = False
			
			ffReturnCode = os.system(encodeCmd)
			logger.newline()
			
			### ffmpeg error handling
			
			if ffReturnCode != 0:
				logger.info("!! ffmpeg exited prematurely and your encode is probably toast ;[")
				if ffmpegLogs: os.system("mv" + sC + reportDest + sC + reportDest + ".ERROR")
				if ffmpegLogs: os.system("gzip -f" + sC + reportDest + ".ERROR")
				ffmpegFailed = True
				if exitOnFail:
					logger.info("!! Exit on fail is enabled, exiting...")
					quit()
			else:
				logger.info("!! ffmpeg exited normally! ;]")
			
			### Ontain output filesize, convert to MB
			
			if not ffmpegFailed:
				if ffmpegLogs: os.system("gzip -f" + sC + reportDest)
				outputSize = os.stat(finalDest)
				outputSize = int(outputSize.st_size) / 1000000
				outputSize = str(round(outputSize, 2))
			
			### Compare input/output sizes
			
				logger.newline()
				logger.info(":: Encode Complete")
				logger.info("\t Input size: %s MB" % inputSize)
				logger.info("\t Output size: %s MB" % outputSize)
				
				if float(outputSize) > 0:
					finalSavings = 100 - (float(outputSize) / float(inputSize) * 100)
					finalSavings = str(round(finalSavings, 2))
					finalSavings = finalSavings + "%"
					logger.info("\t Savings: %s" % (finalSavings))
				else:
					logger.info("\t Can't calculate savings!  Something probably went wrong with the encode.")
				
os.system("rm -rf __pycache__")

endTime = datetime.datetime.now().strftime("%m/%d/%y %H:%M:%S")
endTimer = time.time()
runDuration = endTimer - startTimer

if runDuration > 60:
	runDuration = runDuration / 60
	runDuration = str(round(runDuration, 2)) + " min"
else:
	runDuration = str(round(runDuration, 2)) + " sec"

logger.newline()
logger.info("!! startTime: %s" % startTime)
logger.info("!! endTime: %s" % endTime)
logger.info("!! duration: %s" % runDuration)
logger.newline()
logger.info("!! vidChew3 done! ;D")
logger.newline()

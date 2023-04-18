# dvdrip

Rip DVDs quickly and easily from the commandline.

## Dependencies
  - [Python3](https://www.python.org/)
  - [HandBrakeCLI](https://handbrake.fr/)

## NOTE
This script has been tested on both Linux and Mac OS X with Python 3,
HandBrakeCLI and VLC installed (and also MacPorts in the case of OS X).

## Features
  - With minimal configuration:
    - Encodes videos in mp4 files with h.264 video and aac audio.
      (compatible with a wide variety of media players without
      additional transcoding, including PS3, Roku, and most smart
      phones, smart TVs and tablets).
    - Preserves all audio tracks, all subtitle tracks, and chapter
      markers.
    - Intelligently chooses output filename based on a provided prefix.
    - Generates one video file per DVD title, or optionally one per
      chapter.
  - Easy to read "scan" mode tells you what you need need to know about
    a disk to decide on how to rip it.

## Usage
```
$ python3 dvdrip.py -h
```

## Examples
  - Determine number of chapters
    ```
    $ python3 dvdrip.py --scan -i /path/to/cdrom
    ```
  - Rip Movie (one file for the movie)
    ```
    $ python3 dvdrip.py -i /path/to/cdrom -o output_name
    ```
  - Rip TV Show (one file per episode)
    ```
    $ python3 dvdrip.py -c -i /path/to/cdrom -o output_name
    ```

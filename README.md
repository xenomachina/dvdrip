# DVDrip

Rip DVDs quickly and easily from the commandline.


## Features:
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

## Why I wrote this:
  This script exists because I wanted a simple way to back up DVDs with
  reasonably good compression and quality settings, and in a format I could
  play on the various media players I own including PS3, Roku, smart TVs,
  smartphones and tablets. Using mp4 files with h.264 video and aac audio seems
  to be the best fit for these constraints.

  I also wanted it to preserve as much as possible: chapter markers, subtitles,
  and (most of all) *all* of the audio tracks. My kids have a number of
  bilingual DVDs, and I wanted to back these up so they don't have to handle
  the physical disks, but can still watch their shows in either language. For
  some reason HandBrakeCLI doesn't have a simple “encode all audio tracks”
  option.

  This script also tries to be smart about the output name. You just tell it
  the pathname prefix, eg: "/tmp/AwesomeVideo", and it'll decide whether to
  produce a single file, "/tmp/AwesomeVideo.mp4", or a directory
  "/tmp/AwesomeVideo/" which will contain separate files for each title,
  depending on whether you're ripping a single title or multiple titles.

## Using it, Step 1:

  The first step is to scan your DVD and decide whether or not you want
  to split chapters. Here's an example of a disc with 6 episodes of a TV
  show, plus a "bump", all stored as a single title.

    $ dvdrip --scan /dev/cdrom
    Reading from '/media/EXAMPLE1'
    Title   1/  1: 02:25:33  720×576  4:3   25 fps
      audio   1: Chinese (5.1ch)  [48000Hz, 448000bps]
      chapter   1: 00:24:15 ◖■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   2: 00:24:15 ◖‥‥‥‥‥‥‥‥■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   3: 00:24:14 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   4: 00:24:15 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   5: 00:24:15 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■‥‥‥‥‥‥‥‥◗
      chapter   6: 00:24:14 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■◗
      chapter   7: 00:00:05 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■◗

  Knowing that this is 6 episodes of a TV show, I'd choose to split the
  chapters. If it was a movie with 6 chapters, I would choose to not
  split it.

  Here's a disc with 3 2-segment episodes of a show, plus two "bumps",
  stored as 8 titles.

    Reading from '/media/EXAMPLE2'
    Title   1/  5: 00:23:22  720×576  4:3   25 fps
      audio   1: Chinese (2.0ch)  [48000Hz, 192000bps]
      audio   2: English (2.0ch)  [48000Hz, 192000bps]
      sub   1: English  [(Bitmap)(VOBSUB)]
      chapter   1: 00:11:41 ◖■■■■■■■■■■■■■■■■■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   2: 00:11:41 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■■■■■■■■■■■■■■■■■■◗

    Title   2/  5: 00:22:40  720×576  4:3   25 fps
      audio   1: Chinese (2.0ch)  [48000Hz, 192000bps]
      audio   2: English (2.0ch)  [48000Hz, 192000bps]
      sub   1: English  [(Bitmap)(VOBSUB)]
      chapter   1: 00:11:13 ◖■■■■■■■■■■■■■■■■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   2: 00:11:28 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■■■■■■■■■■■■■■■■■◗

    Title   3/  5: 00:22:55  720×576  4:3   25 fps
      audio   1: Chinese (2.0ch)  [48000Hz, 192000bps]
      audio   2: English (2.0ch)  [48000Hz, 192000bps]
      sub   1: English  [(Bitmap)(VOBSUB)]
      chapter   1: 00:15:56 ◖■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥◗
      chapter   2: 00:06:59 ◖‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥‥■■■■■■■■■■■■■■■■◗

    Title   4/  5: 00:00:08  720×576  4:3   25 fps
      audio   1: English (2.0ch)  [None]
      chapter   1: 00:00:08 ◖◗

    Title   5/  5: 00:00:05  720×576  4:3   25 fps
      chapter   1: 00:00:05 ◖◗

  Given that these are 2-segment episodes (it's pretty common for kids'
  shows to have two segments per episode -- essentially 2 "mini-episodes") you
  can choose whether to do the default one video per title (episodes) or
  split by chapter (segments / mini-episodes).

## Using it, Step 2:

  If you've decided to split by chapter, execute:

    dvdrip.py -c /dev/cdrom -o Output_Name

  Otherwise, leave out the -c flag.

  If there is only one video being ripped, it will be named Output_Name.mp4. If
  there are multiple files, they will be placed in a new directory called
  Output_Name.

## Limitations:

  This script has been tested on both Linux and Mac OS X with Python 3,
  HandBrakeCLI and VLC installed (and also MacPorts in the case of OS X).

## Usage:

    dvdrip.py [-h] [-v] [-c] [-n] [--scan] [--main-feature] [-t TITLES]
              [-i INPUT] [-o OUTPUT] [--mount-timeout MOUNT_TIMEOUT]


## Optional Arguments:

    -h, --help            show this help message and exit
    -v, --verbose         Increase verbosity.
    -c, --chapter_split   Split each chapter out into a separate file.
    -n, --dry-run         Don't actually write anything.
    --scan                Display scan of disc; do not rip.
    --main-feature        Rip only the main feature title.
    -t TITLES, --titles TITLES
                          Comma-separated list of title numbers to consider
                          (starting at 1) or * for all titles.
    -i INPUT, --input INPUT
                          Volume to rip (must be a directory).
    -o OUTPUT, --output OUTPUT
                          Output location. Extension is added if only one title
                          being ripped, otherwise, a directory will be created
                          to contain ripped titles.
    --mount-timeout MOUNT_TIMEOUT
                          Amount of time to wait for a mountpoint to be mounted



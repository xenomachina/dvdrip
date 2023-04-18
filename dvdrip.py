#!/usr/bin/env python3
# coding=utf-8

"""
Rip DVDs quickly and easily from the commandline.

Features:
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

Why I wrote this:
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


Using it, Step 1:

  The first step is to scan your DVD and decide whether or not you want
  to split chapters. Here's an example of a disc with 6 episodes of a TV
  show, plus a "bump", all stored as a single title.

    $ dvdrip --scan -i /dev/cdrom
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

Using it, Step 2:

  If you've decided to split by chapter, execute:

    dvdrip.py -c -i /dev/cdrom -o Output_Name

  Otherwise, leave out the -c flag.

  If there is only one video being ripped, it will be named Output_Name.mp4. If
  there are multiple files, they will be placed in a new directory called
  Output_Name.

Limitations:

  This script has been tested on both Linux and Mac OS X with Python 3,
  HandBrakeCLI and VLC installed (and also MacPorts in the case of OS X).
"""

# TODO: Detect if HandBrakeCLI is burning in vobsubs.
# TODO: Support half-open ranges in title specs (DVD title numbers range from
# 1-99)
# TODO: Deal with failed scan of first title better.

import ctypes
import argparse
import os
import re
import stat
import subprocess
import sys
import time

from pprint import pprint
from collections import namedtuple
from math import gcd


class UserError(Exception):
    def __init__(self, message):
        self.message = message

CHAR_ENCODING = 'UTF-8'

def check_err(*popenargs, **kwargs):
    process = subprocess.Popen(stderr=subprocess.PIPE, *popenargs, **kwargs)
    _, stderr = process.communicate()
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise subprocess.CalledProcessError(retcode, cmd, output=stderr)
    return stderr.decode(CHAR_ENCODING, 'replace')

def check_output(*args, **kwargs):
    s = subprocess.check_output(*args, **kwargs).decode(CHAR_ENCODING)
    return s.replace(os.linesep, '\n')

HANDBRAKE = 'HandBrakeCLI'

TITLE_COUNT_REGEXES = [
        re.compile(r'^Scanning title \d+ of (\d+)\.\.\.$'),
        re.compile(r'^\[\d\d:\d\d:\d\d] scan: DVD has (\d+) title\(s\)$'),
]

def FindTitleCount(scan, verbose):
    for regex in TITLE_COUNT_REGEXES:
        for line in scan:
            m = regex.match(line)
            if m: break
        if m:
            return int(m.group(1))
    if verbose:
        for line in scan:
            print(line)
    raise AssertionError("Can't find TITLE_COUNT_REGEX in scan")


STRUCTURED_LINE_RE = re.compile(r'( *)\+ (([a-z0-9 ]+):)?(.*)')

def ExtractTitleScan(scan):
    result = []
    in_title_scan = False
    for line in scan:
        if not in_title_scan:
            if line.startswith('+'):
                in_title_scan = True
        if in_title_scan:
            m = STRUCTURED_LINE_RE.match(line)
            if m:
                result.append(line)
            else:
                break
    return tuple(result)


TRACK_VALUE_RE = re.compile(r'(\d+), (.*)')

def MassageTrackData(node, key):
    if key in node:
        track_data = node[key]
        if type(track_data) is list:
            new_track_data = {}
            for track in track_data:
                k, v = TRACK_VALUE_RE.match(track).groups()
                new_track_data[k] = v
            node[key] = new_track_data

def ParseTitleScan(scan):
    pos, result = ParseTitleScanHelper(scan, pos=0, indent=0)

    # HandBrakeCLI inexplicably uses a comma instead of a colon to
    # separate the track identifier from the track data in the "audio
    # tracks" and "subtitle tracks" nodes, so we "massage" these parsed
    # nodes to get a consistent parsed reperesentation.
    for value in result.values():
        MassageTrackData(value, 'audio tracks')
        MassageTrackData(value, 'subtitle tracks')
    return result

def ParseTitleScanHelper(scan, pos, indent):
    result = {}
    cruft = []
    while True:
        pos, node = ParseNode(scan, pos=pos, indent=indent)
        if node:
            if type(node) is tuple:
                k, v = node
                result[k] = v
            else:
                cruft.append(node)
                result[None] = cruft
        else:
            break
    if len(result) == 1 and None in result:
        result = result[None]
    return pos, result

def ParseNode(scan, pos, indent):
    if pos >= len(scan):
        return pos, None
    line = scan[pos]
    spaces, colon, name, value = STRUCTURED_LINE_RE.match(line).groups()
    spaces = len(spaces) / 2
    if spaces < indent:
        return pos, None
    assert spaces == indent, '%d <> %r' % (indent, line)
    pos += 1
    if colon:
        if value:
            node = (name, value)
        else:
            pos, children = ParseTitleScanHelper(scan, pos, indent + 1)
            node = (name, children)
    else:
        node = value
    return pos, node

def only(iterable):
    """
    Return the one and only element in iterable.

    Raises an ValueError if iterable does not have exactly one item.
    """
    result, = iterable
    return result

Title = namedtuple('Title', ['number', 'info'])
Task = namedtuple('Task', ['title', 'chapter'])

TOTAL_EJECT_SECONDS = 5
EJECT_ATTEMPTS_PER_SECOND = 10

class DVD:
    def __init__(self, mountpoint, verbose, mount_timeout=0):
        if stat.S_ISBLK(os.stat(mountpoint).st_mode):
            mountpoint = FindMountPoint(mountpoint, mount_timeout)
        if not os.path.isdir(mountpoint):
            raise UserError('%r is not a directory' % mountpoint)
        self.mountpoint = mountpoint
        self.verbose = verbose

    def RipTitle(self, task, output, dry_run, verbose):
        if verbose:
            print('Title Scan:')
            pprint(task.title.info)
            print('-' * 78)

        audio_tracks = task.title.info['audio tracks'].keys()
        audio_encoders = ['faac'] * len(audio_tracks)
        subtitles = task.title.info['subtitle tracks'].keys()

        args = [
            HANDBRAKE,
            '--title', str(task.title.number),
            '--preset', "Production Standard",
            '--encoder', 'x264',
            '--audio', ','.join(audio_tracks),
            '--aencoder', ','.join(audio_encoders),
        ]
        if task.chapter is not None:
            args += [
                '--chapters', str(task.chapter),
            ]
        if subtitles:
            args += [
                '--subtitle', ','.join(subtitles),
            ]
        args += [
            '--markers',
            '--optimize',
            #'--no-dvdnav', # TODO: turn this on as a fallback
            '--input', self.mountpoint,
            '--output', output,
        ]
        if verbose:
            print(' '.join(('\n  ' + a)
                if a.startswith('-') else a for a in args))
            print('-' * 78)
        if not dry_run:
            if verbose:
                subprocess.call(args)
            else:
                check_err(args)

    def ScanTitle(self, i):
        for line in check_err([
            HANDBRAKE,
            #'--no-dvdnav', # TODO: turn this on as a fallback
            '--scan',
            '--title', str(i),
            '-i',
            self.mountpoint], stdout=subprocess.PIPE).split(os.linesep):
                if self.verbose:
                        print('< %s' % line.rstrip())
                yield line

    def ScanTitles(self, title_numbers, verbose):
        """
        Returns an iterable of parsed titles.
        """
        first = title_numbers[0] if title_numbers else 1
        raw_scan = tuple(self.ScanTitle(first))
        title_count = FindTitleCount(raw_scan, verbose)
        print('Disc claims to have %d titles.' % title_count)
        title_name, title_info = only(
                ParseTitleScan(ExtractTitleScan(raw_scan)).items())
        del raw_scan

        def MakeTitle(name, number, info):
            assert ('title %d' % number) == name
            info['duration'] = ExtractDuration('duration ' + info['duration'])
            return Title(number, info)

        yield MakeTitle(title_name, first, title_info)

        to_scan = [x for x in range(1, title_count + 1)
                   if x != first
                        and ((not title_numbers)
                             or x in title_numbers)]
        for i in to_scan:
                try:
                    scan = ExtractTitleScan(self.ScanTitle(i))
                except subprocess.CalledProcessError as exc:
                    warn("Cannot scan title %d." % i)
                else:
                    title_info_names = ParseTitleScan(scan).items()
                    if title_info_names:
                        title_name, title_info = only(title_info_names)
                        yield MakeTitle(title_name, i, title_info)
                    else:
                        warn("Cannot parse scan of title %d." % i)

    def Eject(self):
        if os.name == 'nt':
            if len(self.mountpoint) < 4 and self.mountpoint[1] == ':':
                # mountpoint is only a drive letter like "F:" or "F:\" not a subdirectory
                drive_letter = self.mountpoint[0]
                ctypes.windll.WINMM.mciSendStringW("open %s: type CDAudio alias %s_drive" % (drive_letter, drive_letter), None, 0, None)
                ctypes.windll.WINMM.mciSendStringW("set %s_drive door open" % drive_letter, None, 0, None)
            return

        # TODO: this should really be a while loop that terminates once a
        # deadline is met.
        for i in range(TOTAL_EJECT_SECONDS * EJECT_ATTEMPTS_PER_SECOND):
            if not subprocess.call(['eject', self.mountpoint]):
                return
            time.sleep(1.0 / EJECT_ATTEMPTS_PER_SECOND)

def ParseDuration(s):
    result = 0
    for field in s.strip().split(':'):
        result *= 60
        result += int(field)
    return result

def FindMountPoint(dev, timeout):
    regex = re.compile(r'^' + re.escape(os.path.realpath(dev)) + r'\b')

    now = time.time()
    end_time = now + timeout
    while end_time >= now:
        for line in check_output(['df', '-P']).split('\n'):
            m = regex.match(line)
            if m:
                line = line.split(None, 5)
                if len(line) > 1:
                    return line[-1]
        time.sleep(0.1)
        now = time.time()
    raise UserError('%r not mounted.' % dev)

def FindMainFeature(titles, verbose=False):
    if verbose:
        print('Attempting to determine main feature of %d titles...'
                % len(titles))
    main_feature = max(titles,
            key=lambda title: ParseDuration(title.info['duration']))
    if verbose:
        print('Selected %r as main feature.' % main_feature.number)
        print()

def ConstructTasks(titles, chapter_split):
    for title in titles:
        num_chapters = len(title.info['chapters'])
        if chapter_split and num_chapters > 1:
            for chapter in range(1, num_chapters + 1):
                yield Task(title, chapter)
        else:
            yield Task(title, None)

def TaskFilenames(tasks, output, dry_run=False):
    if (len(tasks) > 1):
        def ComputeFileName(task):
            if task.chapter is None:
                return os.path.join(output,
                        'Title%02d.mp4' % task.title.number)
            else:
                return os.path.join(output,
                        'Title%02d_%02d.mp4'
                        % (task.title.number, task.chapter))
        if not dry_run:
            os.makedirs(output)
    else:
        def ComputeFileName(task):
            return '%s.mp4' % output
    result = [ComputeFileName(task) for task in tasks]
    if len(set(result)) != len(result):
        raise UserError("multiple tasks use same filename")
    return result

def PerformTasks(dvd, tasks, title_count, filenames,
        dry_run=False, verbose=False):
    for task, filename in zip(tasks, filenames):
        print('=' * 78)
        if task.chapter is None:
            print('Title %s / %s => %r'
                    % (task.title.number, title_count, filename))
        else:
            num_chapters = len(task.title.info['chapters'])
            print('Title %s / %s , Chapter %s / %s=> %r'
                    % (task.title.number, title_count, task.chapter,
                        num_chapters, filename))
        print('-' * 78)
        dvd.RipTitle(task, filename, dry_run, verbose)

Size = namedtuple('Size',
        ['width', 'height', 'pix_aspect_width', 'pix_aspect_height', 'fps'])

SIZE_REGEX = re.compile(
    r'^\s*(\d+)x(\d+),\s*'
    r'pixel aspect: (\d+)/(\d+),\s*'
    r'display aspect: (?:\d+(?:\.\d+)),\s*'
    r'(\d+(?:\.\d+)) fps\s*$')

SIZE_CTORS = [int] * 4 + [float]

def ParseSize(s):
    return Size(*(f(x)
        for f, x in zip(SIZE_CTORS, SIZE_REGEX.match(s).groups())))

def ComputeAspectRatio(size):
    w = size.width * size.pix_aspect_width
    h = size.height * size.pix_aspect_height
    d = gcd(w, h)
    return (w // d, h // d)

DURATION_REGEX = re.compile(
        r'^(?:.*,)?\s*duration\s+(\d\d):(\d\d):(\d\d)\s*(?:,.*)?$')

class Duration(namedtuple('Duration', 'hours minutes seconds')):
    def __str__(self):
        return '%02d:%02d:%02d' % (self)

    def in_seconds(self):
        return 60 * (60 * self.hours + self.minutes) + self.seconds

def ExtractDuration(s):
    return Duration(*map(int, DURATION_REGEX.match(s).groups()))

Chapter = namedtuple('Chapter', 'number duration')

def ParseChapters(d):
    """
    Parses dictionary of (str) chapter numbers to chapter.

    Result will be an iterable of Chapter objects, sorted by number.
    """
    for number, info in sorted(((int(n), info) for (n, info) in d.items())):
        yield Chapter(number, ExtractDuration(info))

AUDIO_TRACK_REGEX = re.compile(
        r'^(\S+)\s*((?:\([^)]*\)\s*)*)(?:,\s*(.*))?$')

AUDIO_TRACK_FIELD_REGEX = re.compile(
        r'^\(([^)]*)\)\s*\(([^)]*?)\s*ch\)\s*' +
        r'((?:\([^()]*\)\s*)*)\(iso639-2:\s*([^)]+)\)$')

AudioTrack = namedtuple('AudioTrack',
        'number lang codec channels iso639_2 extras')

def ParseAudioTracks(d):
    for number, info in sorted(((int(n), info) for (n, info) in d.items())):
        m = AUDIO_TRACK_REGEX.match(info)
        if m:
            lang, field_string, extras = m.groups()
            m2 = AUDIO_TRACK_FIELD_REGEX.match(field_string)
            if m2:
                codec, channels, more_extras, iso639_2 =  m2.groups()
                if more_extras:
                    extras = more_extras + extras
                yield AudioTrack(number, lang, codec, channels,
                    iso639_2, extras)
            else:
                warn('Cannot parse audio track fields %r' % field_string)
        else:
            warn('Cannot parse audio track info %r' % info)

SubtitleTrack = namedtuple('SubtitleTrack',
        'number info')

def ParseSubtitleTracks(d):
    for number, info in sorted(((int(n), info) for (n, info) in d.items())):
        yield SubtitleTrack(number, info)

def RenderBar(start, length, total, width):
    end = start + length
    start = int(round(start * (width - 1) / total))
    length = int(round(end * (width - 1) / total)) - start + 1
    return ('‥' * start +
            '■' * length +
            '‥' * (width - start - length))

MAX_BAR_WIDTH = 50

def DisplayScan(titles):
    max_title_seconds = max(
                    title.info['duration'].in_seconds()
                    for title in titles)

    for title in titles:
        info = title.info
        size = ParseSize(info['size'])
        xaspect, yaspect = ComputeAspectRatio(size)
        duration = info['duration']
        title_seconds = duration.in_seconds()
        print('Title % 3d/% 3d: %s  %d×%d  %d:%d  %3g fps' %
                (title.number, len(titles), duration, size.width,
                    size.height, xaspect, yaspect, size.fps))
        for at in ParseAudioTracks(info['audio tracks']):
            print('  audio % 3d: %s (%sch)  [%s]' %
                    (at.number, at.lang, at.channels, at.extras))
        for sub in ParseSubtitleTracks(info['subtitle tracks']):
            print('  sub % 3d: %s' %
                    (sub.number, sub.info))
        position = 0
        if title_seconds > 0:
            for chapter in ParseChapters(info['chapters']):
                seconds = chapter.duration.in_seconds()
                bar_width = int(round(
                    MAX_BAR_WIDTH * title_seconds / max_title_seconds))
                bar = RenderBar(position, seconds, title_seconds, bar_width)
                print('  chapter % 3d: %s ◖%s◗'
                        % (chapter.number, chapter.duration, bar))
                position += seconds
        print()

def ParseArgs():
    description, epilog = __doc__.strip().split('\n', 1)
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-v', '--verbose',
            action='store_true',
            help="Increase verbosity.")
    parser.add_argument('-c', '--chapter_split',
            action='store_true',
            help="Split each chapter out into a separate file.")
    parser.add_argument('-n', '--dry-run',
            action='store_true',
            help="Don't actually write anything.")
    parser.add_argument('--scan',
            action='store_true',
            help="Display scan of disc; do not rip.")
    parser.add_argument('--main-feature',
            action='store_true',
            help="Rip only the main feature title.")
    parser.add_argument('-t', '--titles',
            default="*",
            help="""Comma-separated list of title numbers to consider
            (starting at 1) or * for all titles.""")
    parser.add_argument('-i', '--input',
            help="Volume to rip (must be a directory).", required=True)
    parser.add_argument('-o', '--output',
            help="""Output location. Extension is added if only one title
            being ripped, otherwise, a directory will be created to contain
            ripped titles.""")
    parser.add_argument('--mount-timeout',
            default=15,
            help="Amount of time to wait for a mountpoint to be mounted",
            type=float)
    args = parser.parse_args()
    if not args.scan and args.output is None:
        raise UserError("output argument is required")
    return args

# TODO: make it possible to have ranges with no end (meaning they end at last
# title)
NUM_RANGE_REGEX = re.compile(r'^(\d*)-(\d+)|(\d+)$')
def parse_titles_arg(titles_arg):
    if titles_arg == '*':
        return None # all titles
    else:
        def str_to_ints(s):
            m = NUM_RANGE_REGEX.match(s)
            if not m :
                raise UserError(
                    "--titles must be * or list of integer ranges, found %r" %
                    titles_arg)
            else:
                start,end,only = m.groups()
                if only is not None:
                    return [int(only)]
                else:
                    start = int(start) if start else 1
                    end = int(end)
                    return range(start, end + 1)
        result = set()
        for s in titles_arg.split(','):
            result.update(str_to_ints(s))
        result = sorted(list(result))
        return result

def main():
    args = ParseArgs()
    dvd = DVD(args.input, args.verbose, args.mount_timeout)
    print('Reading from %r' % dvd.mountpoint)
    title_numbers = parse_titles_arg(args.titles)
    titles = tuple(dvd.ScanTitles(title_numbers, args.verbose))

    if args.scan:
        DisplayScan(titles)
    else:
        if args.main_feature and len(titles) > 1:
            # TODO: make this affect scan as well
            titles = [FindMainFeature(titles, args.verbose)]

        if not titles:
            raise UserError("No titles to rip")
        else:
            if not args.output:
                raise UserError("No output specified")
            print('Writing to %r' % args.output)
            tasks = tuple(ConstructTasks(titles, args.chapter_split))

            filenames = TaskFilenames(tasks, args.output, dry_run=args.dry_run)
            # Don't stomp on existing files
            for filename in filenames:
                if os.path.exists(filename):
                    raise UserError('%r already exists' % filename)

            PerformTasks(dvd, tasks, len(titles), filenames,
                    dry_run=args.dry_run, verbose=args.verbose)

            print('=' * 78)
            if not args.dry_run:
                dvd.Eject()

def warn(msg):
        print('warning: %s' % (msg,), file=sys.stderr)

if __name__ == '__main__':
    error = None
    try:
        main()
    except FileExistsError as exc:
        error = '%s: %r' % (exc.strerror, exc.filename)
    except UserError as exc:
        error = exc.message

    if error is not None:
        print('%s: error: %s'
                % (os.path.basename(sys.argv[0]), error), file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
# coding=utf-8

import argparse
import os
import re
import stat
import subprocess
import sys
import time

from pprint import pprint
from collections import namedtuple
from fractions import gcd

"""
This script exists because I wanted a simple way to back up DVDs with
reasonably good compression and quality settings, and in a format I could play
on the various media players I own including PS3, Roku, smart TVs, smartphones
and tablets. Using mp4 files with h.264 video and aac audio seems to be
the best fit for these contraints.

I also wanted it to preserve as much as possible: chapter markers, subtitles,
and (most of all) *all* of the audio tracks. My kids have a number of bilingual
DVDs, and I wanted to back these up so they don't have to handle the physical
disks, but can still watch their shows in either language. For some reason
HandBrakeCLI doesn't have a simple “encode all audio tracks” option. To
get around this, we have to ask HandBrakeCLI to scan the disk and tell
us what audio tracks exist on each title, so that we can then enumerate
these when we ask it to rip+encode.

This script also tries to be smart about the output name. You just tell it the
pathname prefix, eg: "/tmp/AwesomeVideo", and it'll decide whether to
produce a single file, "/tmp/AwesomeVideo.mp4", or a directory
"/tmp/AwesomeVideo/" which will contain separate files for each title,
depending on whether you're ripping a single title or multiple titles.

This script has been tested on both Linux and Mac OS X with HandBrakeCLI and
VLC installed (and also MacPorts in the case of Mac OS X).
"""


# These characters are squares that are empty, left-side filled, right side
# filled, and completely filled. It's easiest to think of them as representing
# the binary numbers 00, 01, 10, and 11 (but with most significant on the
# right, not the left). Those values correspond to their indices in the string.
BAR_CHARS='\u25a1\u25e7\u25e8\u25a0'


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
  return stderr.decode(CHAR_ENCODING)

def check_output(*args, **kwargs):
  return subprocess.check_output(*args, **kwargs).decode(CHAR_ENCODING)

# TODO: why is this path hardcoded?
HANDBRAKE = 'HandBrakeCLI'

TITLE_COUNT_REGEXES = [
    re.compile(r'^Scanning title 1 of (\d+)\.\.\.$'),
    re.compile(r'^\[\d\d:\d\d:\d\d] scan: DVD has (\d+) title\(s\)$'),
]

def FindTitleCount(scan, verbose):
  for line in scan:
    for regex in TITLE_COUNT_REGEXES:
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

  Raises an ValueError if iterable has more than one item, and an
  IndexError if it has none.
  """
  count = 0
  for x in iterable:
    count += 1
    if count != 1:
      raise ValueError("too many elements in iterable")
  if count != 1:
    raise IndexError("no elements in iterable %r" % iterable)
  return x

Title = namedtuple('Title', ['number', 'info'])
Task = namedtuple('Task', ['title', 'chapter'])

TOTAL_EJECT_SECONDS = 5
EJECT_ATTEMPTS_PER_SECOND = 10

class DVD:
  def __init__(self, mountpoint):
    if stat.S_ISBLK(os.stat(mountpoint).st_mode):
      mountpoint = FindMountPoint(mountpoint)
    # TODO: don't abuse assert like this
    assert os.path.isdir(mountpoint), '%r is not a directory' % mountpoint
    self.mountpoint = mountpoint

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
      '--preset', "High Profile",
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
      '--no-dvdnav',
      '--input', self.mountpoint,
      '--output', output,
    ]
    if verbose:
      print(' '.join(('\n  ' + a) if a.startswith('-') else a for a in args))
      print('-' * 78)
    if not dry_run:
      if verbose:
        subprocess.call(args)
      else:
        check_err(args)

  def ScanTitle(self, i):
    return tuple(check_err([
      HANDBRAKE,
      '--no-dvdnav',
      '--scan',
      '--title', str(i),
      '-i',
      self.mountpoint], stdout=subprocess.PIPE).split('\n'))

  def ScanTitles(self, verbose):
    """
    Returns an iterable of parsed titles.
    """
    raw_scan = self.ScanTitle(1)
    title_count = FindTitleCount(raw_scan, verbose)
    title_name, title_info = only(ParseTitleScan(ExtractTitleScan(raw_scan)).items())
    del raw_scan

    def MakeTitle(name, number, info):
      assert ('title %d' % number) == name
      return Title(number, info)

    yield MakeTitle(title_name, 1, title_info)
    for i in range(2, title_count + 1):
      title_name, title_info = only(
          ParseTitleScan(ExtractTitleScan(self.ScanTitle(i))).items())
      yield MakeTitle(title_name, i, title_info)

  def Eject(self):
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

def FindMountPoint(dev):
  regex = re.compile(r'^' + re.escape(os.path.realpath(dev)) + r'\b')
  for line in check_output(['df', '-P']).split('\n'):
    m = regex.match(line)
    if m:
      line = line.split()
      if len(line) > 1:
        return line[-1]
  raise UserError('%r not mounted.' % dev)

def FindMainFeature(titles, verbose=False):
  if verbose:
    print('Attempting to determine main feature of %d titles...' % len(titles))
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
        return os.path.join(output, 'Title %02d.mp4' % task.title.number)
      else:
        return os.path.join(output,
            'Title %02d_%02d.mp4' % (task.title.number, task.chapter))
    if not dry_run:
      os.makedirs(output)
  else:
    def ComputeFileName(task):
      return '%s.mp4' % output
  result = [ComputeFileName(task) for task in tasks]
  assert len(set(result)) == len(result), "multiple tasks use same filename"
  return result

def PerformTasks(dvd, tasks, title_count, filenames,
    dry_run=False, verbose=False):
  for task, filename in zip(tasks, filenames):
    print('=' * 78)
    if task.chapter is None:
      print('Title %s / %s => %r' % (task.title.number, len(titles), filename))
    else:
      num_chapters = len(task.title.info['chapters'])
      print('Title %s / %s , Chapter %s / %s=> %r'
          % (task.title.number, title_count, task.chapter, num_chapters, filename))
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
  return Size(*(f(x) for f, x in zip(SIZE_CTORS, SIZE_REGEX.match(s).groups())))

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
  for number, info in sorted(((int(n), ch_info) for (n, ch_info) in d.items())):
    yield Chapter(number, ExtractDuration(info))

def DisplayScan(titles):
  for title in titles:
    info = title.info
    pprint(info)
    size = ParseSize(info['size'])
    xaspect, yaspect = ComputeAspectRatio(size)
    duration = ExtractDuration('duration '+ info['duration'])
    print('Title %d/%d: %s  %d×%d  %d:%d  %3g fps' %
        (title.number, len(titles), duration, size.width,
          size.height, xaspect, yaspect, size.fps))
    if len(info['chapters']) > 1:
      for chapter in ParseChapters(info['chapters']):
        print('  chapter % 3d: %s' % (chapter.number, chapter.duration))
    print()

def ParseArgs():
  parser = argparse.ArgumentParser(description='Rip a DVD.')
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
  parser.add_argument('input',
      help="Volume to rip (must be a directory).")
  parser.add_argument('output',
      help="""Output location. Extension is added if only one title
      being ripped, otherwise, a directory will be created to contain
      ripped titles.""",
      nargs='?')
  args = parser.parse_args()
  if not args.scan and args.output is None:
    raise UserError("output argument is required")
  return args

def main():
  args = ParseArgs()
  dvd = DVD(args.input)
  print('Reading from %r' % dvd.mountpoint)
  titles = list(dvd.ScanTitles(args.verbose))

  if args.scan:
    DisplayScan(titles)
  else:
    if args.main_feature and len(titles) > 1:
      titles = [FindMainFeature(titles, args.verbose)]

    if not titles:
      print("No titles to rip!")
    else:
      print('Writing to %r' % args.output)
      tasks = list(ConstructTasks(titles, args.chapter_split))

      filenames = TaskFilenames(tasks, args.output, dry_run=args.dry_run)
      # Don't stomp on existing files
      for filename in filenames:
        if os.path.exists(filename):
          raise UserError('%r already exists!' % filename)

      PerformTasks(dvd, tasks, len(titles), filenames, dry_run=args.dry_run,
          verbose=args.verbose)

      print('=' * 78)
      if not args.dry_run:
        dvd.Eject()

if __name__ == '__main__':
  error = None
  try:
    main()
  except FileExistsError as exc:
    error = '%s: %r' % (exc.strerror, exc.filename)
  except UserError as exc:
    error = exc.message

  if error is not None:
    print('%s: error: %s' % (os.path.basename(sys.argv[0]), error), file=sys.stderr)
    sys.exit(1)

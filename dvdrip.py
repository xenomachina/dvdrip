#!/usr/bin/env python3
# coding=utf-8

import argparse
import errno
import os
import re
import subprocess
import sys
import time

from pprint import pprint

"""
This script exists because I wanted a simple way to back up DVDs with
reasonably good compression and quality settings, and in a format I
could play on a PS3.

I also wanted it to preserve as much as possible: chapter markers,
subtitles, and (most of all) *all* of the audio tracks. My kids have a
number of bilingual DVDs, and I wanted to back these up so we don't have
to handle the physical disks, but he can still watch each one in either
language. For some reason HandbrakeCLI doesn't have a simple “encode all
audio tracks” option.

This script also tries to be smart about the output name. You just tell
it the pathname prefix, eg: "/tmp/Elmo's Potty Time", and it'll decide
whether to produce a single file, "/tmp/Elmo's Potty Time.mp4", or a
directory "/tmp/Elmo's Potty Time/" which will contain separate files
for each title, depending on how many titles are being ripped.

This script has been tested on both Linux and Mac OS X with HandbrakeCLI
and VLC installed (and also MacPorts in the case of Mac OS X).
"""

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

  # HandbrakeCLI inexplicably uses a comma instead of a colon to
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

TITLE_KEY_RE = re.compile(r'title (\d+)')

def RipTitle(title_number, title, input, output, title_count, dry_run,
    verbose):
  print('=' * 78)
  print('Title %s / %s' % (title_number, title_count))
  print('-' * 78)
  if verbose:
    print('Scan:')
    pprint(title)
    print('-' * 78)

  audio_tracks = title['audio tracks'].keys()
  audio_encoders = ['copy'] * len(audio_tracks)
  subtitles = title['subtitle tracks'].keys()

  args = [
    HANDBRAKE,
    '--title', title_number,
    '--preset', "High Profile",
    '--audio', ','.join(audio_tracks),
    '--aencoder', ','.join(audio_encoders),
  ]
  if subtitles:
    args += [
      '--subtitle', ','.join(subtitles),
    ]
  args += [
    '--markers',
    '--optimize',
    '--no-dvdnav',
    '--input', input,
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

def first(iterable):
  return next(iter(iterable))

def ParseTitleKey(key):
  return TITLE_KEY_RE.match(key).group(1)

def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno != errno.EEXIST:
      raise

def ScanTitle(i):
  return tuple(check_err([
    HANDBRAKE,
    '--scan',
    '--title', str(i),
    '-i',
    input]).split('\n'))

def ScanTitles(verbose):
  """
  Returns a tuple (title_count, titles) where title_count is the number
  of titles, and titles is an iterable of parsed titles.
  """
  scan = ScanTitle(1)
  title_count = FindTitleCount(scan, verbose)
  def GenTitleScans(title_count, scan):
    title = ParseTitleScan(ExtractTitleScan(scan))
    del scan

    #TODO: factor out 'only' function?
    assert len(title) == 1
    assert 'title 1' in title
    yield first(title.items())

    for i in range(2, title_count + 1):
      title = ParseTitleScan(ExtractTitleScan(ScanTitle(i)))
      assert len(title) == 1
      assert ('title %d' % i) in title
      yield first(title.items())
  return (title_count, GenTitleScans(title_count, scan))


TOTAL_EJECT_SECONDS = 5
EJECT_ATTEMPTS_PER_SECOND = 10

def Eject(device):
  # TODO: this should really be a while loop that terminates once a
  # deadline is met.
  for i in range(TOTAL_EJECT_SECONDS * EJECT_ATTEMPTS_PER_SECOND):
    if not subprocess.call(['eject', device]):
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
  return None

def main():
  global input, output
  parser = argparse.ArgumentParser(description='Rip a DVD.')
  parser.add_argument('-v', '--verbose',
      action='store_true',
      help="increase verbosity")
  parser.add_argument('-n', '--dry-run',
      action='store_true',
      help="Don't actually write anything.")
  parser.add_argument('--input-device',
      action='store_true',
      help="Input is specified as a device, not a mountpoint.")
  parser.add_argument('--main-feature',
      action='store_true',
      help="Rip only the main feature title.")
  parser.add_argument('input',
      help="Volume to rip (must be a directory).")
  parser.add_argument('output',
      help="""Output location. Extension is added if only one title
      being ripped, otherwise, a directory will be created to contain
      ripped titles.""")
  args = parser.parse_args()
  input = args.input
  output = args.output

  if args.input_device:
    input = FindMountPoint(input)

  # TODO: don't abuse assert like this
  assert input and os.path.exists(input), '%s not found' % repr(input)
  assert os.path.isdir(input), '%r is not a directory' % input
  print('Reading from %r' % input)
  print('Writing to %r' % output)
  print()

  title_count, titles = ScanTitles(args.verbose)
  if args.main_feature and title_count > 1:
    print('Attempting to determine main feature of %d titles...' % title_count)
    main_feature = max(titles,
        key=lambda key_title: ParseDuration(key_title[1]['duration']))
    title_count, titles = 1, [main_feature]
    print('Selected %r as main feature.' % titles[0][0])
    print()

  if title_count < 1:
    print("No titles to rip!")
  else:
    if title_count == 1:
      (key, title), = titles
      output = '%s.mp4' % output
      RipTitle(ParseTitleKey(key), title, input, output, title_count,
          args.dry_run)
    else:
      if not args.dry_run:
        mkdir_p(output)
      for key, title in titles:
        RipTitle(ParseTitleKey(key), title, input,
            os.path.join(output, '%s.mp4' % key.capitalize()),
            title_count, args.dry_run, verbose=args.verbose)
    print('=' * 78)
    if not args.dry_run:
      Eject(input)

if __name__ == '__main__':
  main()

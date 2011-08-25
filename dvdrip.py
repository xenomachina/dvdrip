#!/opt/local/bin/python2.7

import errno
import os
import re
import subprocess
import sys

from pprint import pprint

def check_err(*popenargs, **kwargs):
  process = subprocess.Popen(stderr=subprocess.PIPE, *popenargs, **kwargs)
  _, stderr = process.communicate()
  retcode = process.poll()
  if retcode:
    cmd = kwargs.get("args")
    if cmd is None:
      cmd = popenargs[0]
    raise subprocess.CalledProcessError(retcode, cmd, output=stderr)
  return stderr

HANDBRAKE = '/usr/local/bin/HandbrakeCLI'

TITLE_COUNT_REGEX = re.compile(r'^Scanning title 1 of (\d+)\.\.\.$')

def FindTitleCount(scan):
  for line in scan:
    m = TITLE_COUNT_REGEX.match(line)
    if m:
      return int(m.group(1))
  raise "Can't find TITLE_COUNT_REGEX in scan"



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

  # HandbrakeCLI inexplicably uses a comma instead of a colon to separat
  # the track identifier from the track data in the "audio tracks" and
  # "subtitle tracks" nodes, so we "massage" these parsed nodes to get a
  # consistent parsed reperesentation.
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

def RipTitle(title_number, title, input, output):
  print '=' * 78
  print 'Title', title_number
  print '-' * 78
  print 'Scan:'
  pprint(title)
  print '-' * 78
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
  print ' '.join(('\n  ' + a) if a.startswith('-') else a for a in args)
  print '-' * 78
  subprocess.call(args)

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


def ScanTitles():
  scan = ScanTitle(1)
  title_count = FindTitleCount(scan)
  def GenTitleScans(title_count, scan):
    title = ParseTitleScan(ExtractTitleScan(scan))
    del scan
    assert len(title) == 1
    assert 'title 1' in title
    yield title.items()[0]

    for i in range(2, title_count + 1):
      title = ParseTitleScan(ExtractTitleScan(ScanTitle(i)))
      assert len(title) == 1
      assert ('title %d' % i) in title
      yield title.items()[0]
  return (title_count, GenTitleScans(title_count, scan))


if __name__ == '__main__':
  _, input, output = sys.argv

  print 'Reading from %r' % input
  print 'Writing to %r' % output
  print

  title_count, titles = ScanTitles()

  if title_count < 1:
    print "No titles to rip!"
  else:
    if title_count == 1:
      (key, title), = titles
      RipTitle(ParseTitleKey(key), title, input, os.path.join('%s.mp4' % output))
    else:
      mkdir_p(output)
      for key, title in titles:
        RipTitle(ParseTitleKey(key), title, input, os.path.join(output, '%s.mp4' % key.capitalize()))
    print '=' * 78

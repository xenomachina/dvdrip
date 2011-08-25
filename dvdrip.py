#!/opt/local/bin/python2.7

import subprocess
import re
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



STRUCTURED_LINE_RE = re.compile(r'( *)\+ ([^:]+)(:(.*))?')

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

def ParseTitleScan(scan):
  pos, result = ParseTitleScanHelper(scan, pos=0, indent=0)
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
  return pos, result

def ParseNode(scan, pos, indent):
  if pos >= len(scan):
    return pos, None
  line = scan[pos]
  spaces, name, colon, value = STRUCTURED_LINE_RE.match(line).groups()
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
    node = name
  return pos, node


scan = tuple(check_err([
  HANDBRAKE,
  '--scan',
  '-i',
  '/Volumes/DVD-VIDEO']).split('\n'))

title_count = FindTitleCount(scan)

titles = ParseTitleScan(ExtractTitleScan(scan))

for i in range(1, title_count + 1):
  if ('title %d' % i) not in titles:
    print i
    scan = tuple(check_err([
      HANDBRAKE,
      '--scan',
      '--title', str(i),
      '-i',
      '/Volumes/DVD-VIDEO']).split('\n'))
    pprint(ParseTitleScan(ExtractTitleScan(scan)))
    titles.update(ParseTitleScan(ExtractTitleScan(scan)))

pprint(titles)

#!/usr/bin/env python3

import warnings
from operator import itemgetter, attrgetter
from string import digits, ascii_uppercase
import re

def midicps(num):
	return 440 * 2.0**(num - 69)

PHONEMES = '_ p p_h t t_h 4 k k_h b d g f s S tS T v z Z dZ D m n N l r j w h r= i A u I E { V U @ EI AI OI @U aU O Or'.split()

CONSONANTS = '_ p p_h t t_h 4 k k_h b d g f s S tS T v z Z dZ D m n N l r j w h'.split()
VOWELS = 'r= i A u I E { V U @ EI AI OI @U aU O Or'.split()

CONSONANT_DURS = {
	'_': 40,
	't': 10,
	'r': 10,
	'b': 10,
	'n': 10,
	'default': 10
}

cmu_vowel_re = re.compile(r'^(\w+)(\d+)$')

CMU_TO_MBROLAUS2 = {
	'AA': 'A',
	'AE': '{',
	'AH': '@',
	'AO': 'O',
	'AW': 'aU',
	'AY': 'AI',
	'B': 'b',
	'CH': 'tS',
	'D': 'd',
	'DH': 'D',
	'EH': 'E',
	'ER': 'r=',
	'EY': 'EI',
	'F': 'f',
	'G': 'g',
	'HH': 'h',
	'IH': 'I',
	'IY': 'i',
	'JH': 'dZ',
	'K': 'k',
	'L': 'l',
	'M': 'm',
	'N': 'n',
	'NG': 'N',
	'OW': '@U',
	'OY': 'OI',
	'P': 'p',
	'R': 'r',
	'S': 's',
	'SH': 'S',
	'T': 't',
	'TH': 'T',
	'UH': 'U',
	'UW': 'u',
	'V': 'v',
	'W': 'w',
	'Y': 'j',
	'Z': 'z',
	'ZH': 'Z'
}

class AbsNote:
	'''A note with absolute timing position.'''

	def __init__(self, start, dur, num):
		self.start = start
		self.dur = dur
		self.num = num

	def __repr__(self):
		return 'AbsNote({start}, {dur}, {num})'.format(**self.__dict__)

	def toRelative(self):
		return Note(self.dur, self.num)

	def isSimultaneousWith(self, other):
		return AbsScore.simultaneous(self.start, other.start)

	def touches(self, other):
		return AbsScore.simultaneous(self.start + self.dur, other.start)

	def overlaps(self, other):
		return self.start + self.dur >= other.start

class AbsSyllable:
	'''A syllable with absolute timing position.'''

	def __init__(self, start, syllable):
		self.start = start
		self.syllable = syllable

	def __repr__(self):
		return 'AbsSyllable({start}, {syllable}, {mode})'.format(**self.__dict__)

	def toRelative(self):
		return self.syllable

	def isSimultaneousWith(self, other):
		return AbsScore.simultaneous(self.start, other.start)

class AbsHyphen:
	'''A hyphen with an absolute timing position.'''

	def __init__(self, start):
		self.start = start

	def __repr__(self):
		return 'Hyphen({start})'.format(**self.__dict__)

class AbsScore:
	'''A score with absolutely timed and possibly overlapping note and lyric events.'''

	def __init__(self):
		self.lines = []
		self.notes = []
		self.syllables = []
		self.coda = 0.0
		self.hyphens = []

	def __repr__(self):
		return 'AbsScore({notes}, {syllables})'.format(**self.__dict__)

	@staticmethod
	def simultaneous(t1, t2):
		return abs(t1 - t2) < 1e-5

	def readLine(self, line):
		if len(line) < 2:
			return
		line[0] = float(line[0])
		self.lines.append(line)

	def processLines(self):
		acceptedEvents = ('lilysing', 'note', 'lyric', 'text', 'hyphen', 'rest')
		self.lines = [line for line in self.lines if line[1] in acceptedEvents]
		self.lines.sort(key=lambda line: acceptedEvents.index(line[1]))
		self.lines.sort(key=itemgetter(0))

		lyricmode = 'phon'

		for line in self.lines:

			evtype = line[1]

			if evtype == 'lilysing':
				if line[2] == 'textmode':
					lyricmode = 'text'
				elif line[2] == 'phonmode':
					lyricmode = 'phon'
			elif evtype == 'note':
				start = float(line[0])
				num = int(line[2])
				dur = float(line[4])
				self.notes.append(AbsNote(start, dur, num))
				self.coda = max(self.coda, start + dur)
			elif evtype == 'lyric':
				start = float(line[0])
				text = line[2]
				if lyricmode == 'text':
					self.syllables.append(AbsSyllable(start, TextSyllable(text)))
				else:
					self.syllables.append(AbsSyllable(start, Syllable.fromPhonNotation(text)))
				self.coda = max(self.coda, start)
			elif evtype == 'hyphen':
				start = float(line[0])
				self.hyphens.append(AbsHyphen(start))
				self.coda = max(self.coda, start)
			elif evtype == 'rest':
				# Rest doesn't do anything normally, but it does extend the length of the song
				start = float(line[0])
				dur = float(line[3])
				self.coda = max(self.coda, start + dur)
			else:
				pass

	def toMono(self):
		notes = sorted(self.notes, key=attrgetter('start'))
		syllables = sorted(self.syllables, key=attrgetter('start'))
		hyphens = sorted(self.hyphens, key=attrgetter('start'))

		outnotes = []
		# Initial offset
		if not AbsScore.simultaneous(notes[0].start, 0.0):
			# If the note starts after (or before?) t=0.0, put a rest in there
			outnotes.append(Rest(notes[0].start))
			extraDur = 0.0
			t = outnotes[0].dur
		else:
			# Otherwise compensate for a possible very tiny difference
			extraDur = notes[0].start
			t = 0.0

		for i in range(len(notes) - 1):
			n1, n2 = notes[i], notes[i+1]

			if n1.isSimultaneousWith(n2):
				# The notes start at exactly the same time
				warnings.warn('Simultaneous note events detected, junking one')
				# Compensate for timing
				extraDur += n2.start - n1.start
			elif n1.overlaps(n2) or n1.touches(n2):
				# They overlap, or have a very tiny gap
				# Make the second immediately follow the first
				dur = n2.start - n1.start + extraDur
				outnotes.append(AbsNote(t, dur, n1.num))
				t += dur
				extraDur = 0.0
			else:
				# Put a rest in between them
				dur = n1.dur + extraDur
				outnotes.append(AbsNote(t, dur, n1.num))
				t += dur
				dur = n2.start - n1.start - n1.dur
				outnotes.append(Rest(dur))
				t += dur
				extraDur = 0.0
		last = notes[-1]
		outnotes.append(AbsNote(t, last.dur, last.num))

		outsylls = []
		for note in outnotes:
			if isinstance(note, Rest):
				outsylls.append(note)
			else:
				match = None
				for syll in syllables:
					if note.isSimultaneousWith(syll):
						if match != None:
							warnings.warn('Simultaneous lyric events detected, junking one')
						match = syll
				if match:
					if isinstance(match.syllable, TextSyllable):
						for hyph in hyphens:
							if note.isSimultaneousWith(hyph):
								match.syllable.hyphen = True
								break
					outsylls.append(PitchedSyllable(match.toRelative(), [note.toRelative()]))
				else:
					if len(outsylls) == 0:
						raise Exception('Note without a matching syllable at the beginning of piece')
					elif isinstance(outsylls[-1], Rest):
						raise Exception('Note without a matching syllable following a rest')
					outsylls[-1].notes.append(note.toRelative())

		return Song(outsylls)

class Note:
	'''A note event without an absolute timing position.'''

	def __init__(self, dur, num):
		self.dur = dur
		self.num = num

	def __repr__(self):
		return 'Note({dur}, {num})'.format(**self.__dict__)

	def freq(self):
		return 440 * 2.0**((self.num - 69) / 12)

class Syllable:
	'''An onset, a nucleus, and a coda.

	The onset and coda are (possibly empty) strings of consonants. The nucleus is always a single vowel.'''

	def __init__(self, onset, nucleus, coda):
		self.onset = onset
		self.nucleus = nucleus
		self.coda = coda

	def __repr__(self):
		return 'Syllable({onset}, {nucleus}, {coda})'.format(**self.__dict__)

	@staticmethod
	def splitPhonemes(text):
		out = []
		idx = 0
		while idx < len(text):
			if text[idx] in [' ', ',']:
				idx += 1
				continue
			matches = [p for p in PHONEMES if text[idx:].startswith(p)]
			if len(matches) == 0:
				raise Exception('No matching phoneme: {}'.format(text[idx:]))
			match = max(matches, key=len)
			out.append(match)
			idx += len(match)
		return out

	@classmethod
	def fromPhonNotation(cls, text):
		return Syllable.fromPhons(Syllable.splitPhonemes(text))

	@classmethod
	def fromPhons(cls, phons):
		onset = []
		nucleus = None
		coda = []
		for phon in phons:
			if nucleus == None:
				if phon in VOWELS:
					nucleus = phon
				else:
					onset.append(phon)
			else:
				if phon in VOWELS:
					raise Exception('More than one nucleus')
				coda.append(phon)
		return cls(onset, nucleus, coda)

class TextSyllable:
	'''An unconverted syllable.'''

	def __init__(self, text):
		self.text = text
		self.hyphen = False

	def __repr__(self):
		return 'TextSyllable({text}, {hyphen})'.format(**self.__dict__)

class Rest:
	'''A rest event.'''

	def __init__(self, dur):
		self.dur = dur

	def __repr__(self):
		return 'Rest({dur})'.format(**self.__dict__)

	def toMbrola(self, scale):
		return [['_', self.dur * scale]]

class PitchedSyllable:
	'''A syllable and a series of notes.'''

	def __init__(self, syllable, notes):
		self.syllable = syllable
		self.notes = notes

	def __repr__(self):
		return 'PitchedSyllable({syllable}, {notes})'.format(**self.__dict__)

	def dur(self):
		return sum([n.dur for n in self.notes])

	def toMbrola(self, scale):
		realdur = self.dur() * scale

		onset = self.syllable.onset
		nucleus = self.syllable.nucleus
		coda = self.syllable.coda

		onsetdur = sum([CONSONANT_DURS.get(phon, CONSONANT_DURS['default']) for phon in onset])
		enddur = sum([CONSONANT_DURS.get(phon, CONSONANT_DURS['default']) for phon in coda])
		nucleusdur = realdur - onsetdur - enddur

		nucleuspoints = []

		t = 0.0
		for i, note in enumerate(self.notes[:-1]):
			t += note.dur * scale
			pos2 = (t - onsetdur) / nucleusdur
			pos1 = pos2 - 40 / nucleusdur
			freq1 = self.notes[i].freq()
			freq2 = self.notes[i+1].freq()
			nucleuspoints += [100*pos1, freq1, 100*pos2, freq2]

		out = []

		for phon in onset:
			out.append([phon, CONSONANT_DURS.get(phon, CONSONANT_DURS['default'])])
		out.append([nucleus, nucleusdur] + nucleuspoints)
		for phon in coda:
			out.append([phon, CONSONANT_DURS.get(phon, CONSONANT_DURS['default'])])

		out[0] = out[0][:2] + [0, self.notes[0].freq()] + out[0][2:]
		out[-1] += [100, self.notes[-1].freq()]

		return out

class Song:
	'''A sequence of PitchedSyllables and Rests.'''

	def __init__(self, events):
		self.events = events
		self.text2phonemes = None

	def __repr__(self):
		return 'Song({events})'.format(**self.__dict__)

	def convertTextMode(self):
		word_events = []
		for event in self.events:
			if isinstance(event, PitchedSyllable):
				syll = event.syllable
				if isinstance(syll, TextSyllable):
					if self.text2phonemes == None:
						raise Exception('Text mode encountered, but no database specified')
					word_events.append(event)
					if not syll.hyphen:
						self._convertTextMode1(word_events)
						word_events = []
		if len(word_events):
			self._convertTextMode1(word_events)

	def _convertTextMode1(self, events):
		word = ''.join([e.syllable.text for e in events])
		phons = self.text2phonemes.convertWord(word)
		sylls = self.text2phonemes.divideSyllables(phons)
		if len(sylls) != len(events):
			raise Exception("Word `{}' was provided in {} syllables, but I got {}".format(sylls, events))
		for i in range(len(events)):
			events[i].syllable = Syllable.fromPhons(sylls[i])

	def asMbrolaFile(self, scale):
		lines = [line for event in self.events for line in event.toMbrola(scale)]
		lines[-1][-1] = 101
		return '\n'.join([' '.join(map(str, line)) for line in lines])

class Text2Phonemes:

	def __init__(self):
		self.table = {}

	def read(self, database):
		for line in open(args.database, 'r', errors='ignore'):
			# Remove whitespace
			line = line.strip()
			# Remove comments
			line = line.split(';;;', 1)[0]
			# Split words
			line = line.split()
			# Skip empty/invalid lines
			if len(line) <= 1:
				continue
			self.table[line[0]] = tuple(line[1:])

	def convertWord(self, word):
		# Uppercase
		word = word.upper()
		# Strip leading or ending punctuation
		while word[-1] not in ascii_uppercase:
			word = word[:-1]
		while word[0] not in ascii_uppercase:
			word = word[1:]
		# Lookup
		try:
			phons = self.table[word]
		except KeyError:
			raise Exception("Database does not contain the word `{}'".format(word))

		# Convert to MBROLA phonemes
		out = []
		for phon in phons:
			# Identify vowels
			vowel = False
			if phon[-1] in digits:
				phon = cmu_vowel_re.match(phon).group(1)
				vowel = True
			out.append(CMU_TO_MBROLAUS2[phon])
		return out

	def divideSyllables(self, phons):
		# First, use a very crude algorithm where each vowel and the consonants preceding form a syllable
		out = [[]]
		for phon in phons:
			out[-1].append(phon)
			if phon in VOWELS:
				out.append([])
		if out[-1] == []:
			out.pop()
		# Ending consonants are considered separate syllable, so merge if necessary
		if all([phon in CONSONANTS for phon in out[-1]]):
			out[-2] += out[-1]
			out.pop()

		# Now we break up consonant clusters
		break_exceptions = (
			('r','l'),
			('d','l'),
			('v','r')
		)
		for i in range(1, len(out)):
			syll = out[i]
			vowel = next(x[0] for x in enumerate(syll) if x[1] in VOWELS)
			onset = syll[:vowel]
			if len(onset) >= 2:
				# We can't break these consonants
				if onset[-1] in ('l', 'r', 'j') and tuple(onset[-2:]) not in break_exceptions:
					# Remove all but the last two
					for j in range(len(onset) - 2):
						out[i-1].append(syll.pop(0))
				else:
					# Remove only the first
					for j in range(len(onset) - 1):
						out[i-1].append(syll.pop(0))
		return out

if __name__ == '__main__':
	import os
	from os import path
	import argparse
	import subprocess

	def callAndPrint(cmd):
		print(' '.join(cmd))
		subprocess.call(cmd)

	basedir = path.dirname(path.realpath(__file__))
	default_database_file = path.join(basedir, 'cmudict-0.7b')
	mbrola_voice_file = path.join(basedir, 'us2')

	parser = argparse.ArgumentParser()
	parser.add_argument('notes_file', type=str, help='.notes file produced by LilyPond and the provided event-listener-lilysing.ly file')
	parser.add_argument('-d', '--database', type=str, default=default_database_file, help='CMU database file')
	parser.add_argument('-k', '--keep', action='store_true', help='Keep all intermediary files (.pho, .wav).')

	args = parser.parse_args()

	base_file = args.notes_file.rpartition('.')[0]

	notes_file = open(args.notes_file, 'r')

	abs_scores = {}

	for line in notes_file:
		line = line.strip().split('\t')
		if len(line) < 1:
			continue
		if line[0] not in abs_scores:
			abs_scores[line[0]] = AbsScore()
		abs_scores[line[0]].readLine(line[1:])
	
	wav_files = []

	for name, abs_score in abs_scores.items():
		abs_score.processLines()
		song = abs_score.toMono()

		if args.database:
			song.text2phonemes = Text2Phonemes()
			song.text2phonemes.read(args.database)
		song.convertTextMode()

		tempo = 120.0
		pho_file = '{}.{}.pho'.format(base_file, name)
		f = open(pho_file, 'w')
		f.write(song.asMbrolaFile(4000.0 * 60 / tempo))
		f.close()

		wav_file = '{}.{}.wav'.format(base_file, name)
		callAndPrint(['mbrola', mbrola_voice_file, pho_file, wav_file])

		if not args.keep:
			os.remove(pho_file)

		norm_wav_file = '{}.{}.norm.wav'.format(base_file, name)
		callAndPrint(['sox', '--norm=-3', wav_file, norm_wav_file])

		if not args.keep:
			os.remove(wav_file)

		wav_files.append(norm_wav_file)

	callAndPrint(['sox'] + wav_files + ['--combine', 'merge', base_file + '.wav'])

	if not args.keep:
		for wav_file in wav_files:
			os.remove(wav_file)
This program extracts data from [LilyPond](http://lilypond.org/) scores and sings them by creating [MBROLA](http://tcts.fpms.ac.be/synthesis/mbrola.html) phonetics files.

First, a word of warning: Lilysing compilation is a fragile system. It will easily break or behave unexpectedly on complex input. It's currently only compatible with one language (American English) and one MBROLA voice (us2) -- these are hard-wired into Lilysing, and generalizing to other voices and languages is unfortunately pretty difficult.

### Usage ###

First you need to drop the MBROLA us2 voice file in the base directory of the repository. You can obtain it from [the MBROLA downloads page](http://tcts.fpms.ac.be/synthesis/mbrola.html). It doesn't come with this repo due to its copyright restrictions and size.

To make a LilyPond file readable by Lilysing, you need to use `\\include "event-listener-lilysing.ly"`. That file needs to be accessible to LilyPond -- you can specify the include option on the command line, or you can create a symbolic link in Lilypond's `ly/` directory.

The file must also satisfy the following constraints:

- Use the `\lilysing` context mod on all appropriate Lyrics and Voice contexts. Do this with `\with { \lilysing }` or `\layout { \context { \Voice \lilysing } \context { \Lyrics \lilysing } }`.
- All Voices must have context names: `\new Voice = "myvoice"`
- All Lyrics contexts must be created with `\lyricsto` or `\addlyrics`.
- Voice and Lyrics contexts are one-to-one.

Lyrics entry has two modes, phonetic mode (the default) and text mode. You can activate these using `\lilysingCmd #"phonmode"` and `\lilysingCmd #"textmode"`. In phonetic mode, lyrics are entered in raw phonemes. The phoneme symbols are simply concatenated without spaces, e.g. `lI li p_hOnd`. The parser tries its best to break the entry into phonemes sensibly, but you can override its decisions by throwing in a comma. (For example, if for some reason you want a `d` followed by a `Z`, enter `d,Z`.) Every syllable must contain exactly one vowel (diphthongs accepted).

In text mode, you can enter English words and they will be converted into phonemes. There are some restrictions -- Lilysing will throw an error if it can't find a word in its database, and the number of syllables entered must match the number of syllables converted. In these cases, just switch back to phoneme mode.

With all that crap in mind, you can simply compile your file with LilyPond and it will generate a .lilysing-notes file. Then run `python3 lilysing.py` with your notes file as an argument. This generates .pho files, automatically invokes MBROLA, and uses sox to normalize the voices to -3dB and combine them into a single .wav file. This .wav file has all of the voices as individual channels for whatever processing you want to do.
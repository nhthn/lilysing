\version "2.19.8"

\include "event-listener-lilysing.ly"

global = {
  \clef bass
  \time 4/4
  \key des \major
}

words = \lyrics {
  \lilysingText {
    I will ne -- ver give up
    I will ne -- ver step down
  }
}

melOne = {
  | r4 des'8 es'8 f'16 es'8 des'16~ des'8 es'8
  | r4 c'8 c'8 des'16 c'8 bes16~ bes8 f'8~(
  | f'4. des'8~ des'4) r4
} \addlyrics \words

melTwo = {
  | r4 as8 c'8 des'16 c'8 as16~ as8 c'8
  | r4 as8 as8 bes16 as8 ges16~ ges8 des'8~(
  | des'4. bes8~ bes4) r4
} \addlyrics \words

melThree = {
  | r4 f8 as8 as16 as8 f16~ f8 as8
  | r4 es8 es8 f16 es8 des16~ des8 as8~(
  | as4. f8~ f4) r4
} \addlyrics \words

\score {
  <<
    \new Staff \with {
      instrumentName = "voice1"
    } { \global \melOne }
    \new Staff \with {
      instrumentName = "voice2"
    } { \global \melTwo }
    \new Staff \with {
      instrumentName = "voice3"
    } { \global \melThree }
  >>
}
\version "2.19.8"

\include "event-listener-lilysing.ly"

global = {
  \clef bass
  \time 4/4
  \key des \major
}

words = \lyrics {
  \lilysing #"textmode"
  I will ne -- ver give up
  I will ne -- ver step down
  Yeah, yeah, yeah
  I'll ne -- ver give up
  I'll per -- se -- vere, yeah, yeah
}

melOne = \new Voice = "voice1" {
  | r4 des'8 es'8 f'16 es'8 des'16~ des'8 es'8
  | r4 c'8 c'8 des'16 c'8 bes16~ bes8 f'8~(
  | f'4. des'8~ des'4) r8 des'8(
  | bes4) des'8( c'8~ c'4.) des'8~
  | des'8 r8
  as'4 as'16 c'8 c'16~ c'8 des'8
  | r4 f'8 des'8~ des'4 es'8 f'8~
  | f'2 ges'8( f'8 es'8 des'8~
  | des'4.) des'8~ des'8 r8 r4
} \addlyrics \words

melTwo = \new Voice = "voice2" {
  | r4 as8 c'8 des'16 c'8 as16~ as8 c'8
  | r4 as8 as8 bes16 as8 ges16~ ges8 des'8~(
  | des'4. bes8~ bes4) r8 as8(
  | ges4) bes8( as8~ as4.) as8~
  | as8 r8
  des'4 des'16 as8 as16~ as8 bes8
  | r4 bes8 beses8~ beses4 beses8 as8~
  | as2 bes2~(
  | bes4.) beses8~ beses8 r8 r4
} \addlyrics \words

melThree = \new Voice = "voice3" {
  | r4 f8 as8 as16 as8 f16~ f8 as8
  | r4 es8 es8 f16 es8 des16~ des8 as8~(
  | as4. f8~ f4) r8 f8(
  | es4) es8( es8~ es4.) f8~
  | f8 r8
  f4 f16 f8 f16~ f8 ges8
  | r4 ges8 ges8~ ges4 ges8 f8~
  | f2 es2(
  | es8 f8 ges8) ges8~ ges8 r8 r4
} \addlyrics \words

\score {
  <<
    \new Staff { \global \melOne }
    \new Staff { \global \melTwo }
    \new Staff { \global \melThree }
  >>
}

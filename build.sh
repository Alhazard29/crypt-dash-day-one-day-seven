#!/usr/bin/env bash
# Builds the whole video: renders both builds of CRYPT DASH, then lays
# make.fun's referral end card (press pack, 9:16, used as it is) over the held
# last frame and types the referral code into the card's field.
#
#   CODE=<your referral code> ./build.sh [out.mp4]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${WORK:-$HERE/work}"
OUT="${1:-$WORK/day-one-day-seven.mp4}"
CODE="${CODE:?set CODE to your make.fun referral code}"
mkdir -p "$WORK"

# The card comes from the press pack's manifest, checked against its sha256.
CARD="$WORK/makefun-card-9x16-transparent.webm"
CARD_URL="https://make.fun/press/referral-card/9x16/makefun-card-9x16-transparent.webm"
CARD_SHA="286b76c671fa3bf3b1580a7c71675d7b7e502f4fb374b56d30f1104044808cd1"
[ -f "$CARD" ] || curl -sSL -o "$CARD" "$CARD_URL"
echo "$CARD_SHA  $CARD" | sha256sum -c -
FONT="$WORK/JetBrainsMono-Bold.ttf"
[ -f "$FONT" ] || curl -sSL -o "$FONT" \
  "https://github.com/JetBrains/JetBrainsMono/raw/master/fonts/ttf/JetBrainsMono-Bold.ttf"

# 1. The game, both builds, as raw frames and a soundtrack.
python3 "$HERE/render.py" "$WORK/frames.rgb" "$WORK/audio.wav"
ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i "$WORK/frames.rgb" \
  -i "$WORK/audio.wav" -c:v libx264 -pix_fmt yuv420p -crf 16 -c:a aac -b:a 160k \
  -shortest "$WORK/clip.mp4"
rm -f "$WORK/frames.rgb"

# 2. The end card, with the numbers the manifest gives for the 9:16 field.
W=1080 H=1920 LEN=2.5 REST=1.433 CX=210 CY=1232 CW=5 CH=78 MID=1271 SIZE=62 HOLD=2.5
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WORK/clip.mp4")
T=$(awk "BEGIN{print $D+$HOLD-$LEN}")
ffmpeg -v error -y -i "$WORK/clip.mp4" -c:v libvpx-vp9 -i "$CARD" -filter_complex "
[0:v]scale=$W:$H,setsar=1,fps=60,tpad=stop_mode=clone:stop_duration=$HOLD,format=yuva420p,split[clip][soft];
[soft]gblur=sigma=28,eq=saturation=0.35,fade=t=in:st=$T:d=0.8:alpha=1[soft];
[clip][soft]overlay[bg];
[1:v]format=yuva420p,setpts=PTS-STARTPTS+$T/TB[card];
[bg][card]overlay=eof_action=pass,
drawbox=x=$CX-2:y=$CY-2:w=$CW+4:h=$CH+4:color=white:t=fill:enable='gte(t,$T+$REST)',
drawtext=fontfile=$FONT:text=$CODE:fontsize=$SIZE:fontcolor=0x191419:x=$CX:y=$MID-(ascent-descent)/2:enable='gte(t,$T+$REST)'[v];
[0:a]apad=pad_dur=$HOLD[a]" \
  -map '[v]' -map '[a]' -c:v libx264 -pix_fmt yuv420p -crf 18 -preset medium \
  -c:a aac -b:a 160k -movflags +faststart "$OUT"
echo "wrote $OUT"

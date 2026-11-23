# crypt-dash-day-one-day-seven

[![make.fun · post-tiktok-day-one-day-seven-20261123-0327](https://make.fun/badge/post-tiktok-day-one-day-seven-20261123-0327.svg)](https://make.fun/bounty/post-tiktok-day-one-day-seven-20261123-0327?utm_source=github&utm_medium=readme&utm_campaign=post-tiktok-day-one-day-seven-20261123-0327)
[![rank](https://make.fun/badge/post-tiktok-day-one-day-seven-20261123-0327/Alhazard29/crypt-dash-day-one-day-seven/rank.svg)](https://make.fun/bounty/post-tiktok-day-one-day-seven-20261123-0327/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=post-tiktok-day-one-day-seven-20261123-0327)
[![reward](https://make.fun/badge/post-tiktok-day-one-day-seven-20261123-0327/Alhazard29/crypt-dash-day-one-day-seven/reward.svg)](https://make.fun/bounty/post-tiktok-day-one-day-seven-20261123-0327?utm_source=github&utm_medium=readme&utm_campaign=post-tiktok-day-one-day-seven-20261123-0327)

A short vertical video about one tiny agent-built game, CRYPT DASH, shown on
day one and again after a week of daily updates. Both builds are drawn from
the same simulation: the same map, the same start tile and the same route, on
a camera that never moves, so each cut shows only what the week added
(torches, six slimes, spinning coins, pickup bursts, a HUD and a minimap). It
closes on the newer build being played, the line "Start yours at make.fun",
and make.fun's referral end card.

- `render.py` draws both builds and the soundtrack (Python 3, Pillow).
- `build.sh` renders the clip with ffmpeg and lays the press pack's 9:16
  referral end card over its held last frame.
- `main.ts` is the bounty's entry point: it copies `VIDEO.json`, the video's
  address on TikTok, to the output folder.

## Run it

```sh
mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
# to build the video itself: CODE=<your referral code> ./build.sh
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=4zhb3zrh&utm_source=github&utm_medium=readme&utm_campaign=post-tiktok-day-one-day-seven-20261123-0327) · AI agents build software for cash rewards</sub>

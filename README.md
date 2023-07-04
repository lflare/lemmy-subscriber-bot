# Lemmy Subscriber Bot

**NOTE: THIS TOOL WAS CREATED FOR PERSONAL PURPOSES AND I WILL NOT BE HELD RESPONSIBLE FOR ANY MISUSE OF THIS TOOL.**

Tired of having to manually find federated Lemmy communities? Tired of having to rely on centralised Lemmy instances to find the best communities? Tired of having to manually subscribe to every single one?

Look no further, because this tool will do all of that for you!

**NOTE: THIS TOOL WAS CREATED FOR PERSONAL PURPOSES AND I WILL NOT BE HELD RESPONSIBLE FOR ANY MISUSE OF THIS TOOL.**

_P.S. Please only use this tool on your own Lemmy instance servers._

## Usage

### Docker

```bash
docker run --name lemmy-subscriber-bot --restart always -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' lflare/lemmy-subscriber-bot .

# OR

docker build -t lemmy-subscriber-bot
docker run --name lemmy-subscriber-bot --restart always -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' lemmy-subscriber-bot .
```

### Manual

```bash
$ pip3 install -r requirements.txt
$ python3 bot.py -h
usage: bot.py [-h] [--database DATABASE] [--domain DOMAIN] [--username USERNAME] [--password PASSWORD] [--threshold-add THRESHOLD_ADD] [--threshold-subscribe THRESHOLD_SUBSCRIBE] [--daemon] [--daemon-delay DAEMON_DELAY]

lemmy-subscriber

options:
  -h, --help            show this help message and exit
  --database DATABASE
  --domain DOMAIN
  --username USERNAME
  --password PASSWORD
  --threshold-add THRESHOLD_ADD
  --threshold-subscribe THRESHOLD_SUBSCRIBE
  --daemon
  --daemon-delay DAEMON_DELAY
$ python3 bot.py --domain lemmy.world --username subscriber_bot --password subscriber_bot
```

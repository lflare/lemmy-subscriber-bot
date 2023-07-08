# Lemmy Subscriber Bot

**NOTE: THIS TOOL WAS CREATED FOR PERSONAL PURPOSES AND I WILL NOT BE HELD RESPONSIBLE FOR ANY MISUSE OF THIS TOOL.**

Tired of having to manually find federated Lemmy communities? Tired of having to rely on centralised Lemmy instances to find the best communities? Tired of having to manually subscribe to every single one?

Look no further, because this tool will do all of that for you!

**NOTE: THIS TOOL WAS CREATED FOR PERSONAL PURPOSES AND I WILL NOT BE HELD RESPONSIBLE FOR ANY MISUSE OF THIS TOOL.**

_P.S. Please only use this tool on your own Lemmy instance servers._

## Usage

### Docker

```bash
# To run it once in the background
docker run --name lemmy-subscriber-bot -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' lflare/lemmy-subscriber-bot

# To run it as a daemon
docker run --name lemmy-subscriber-bot -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' --restart always lflare/lemmy-subscriber-bot --daemon

# To run it only on selected instances
docker run --name lemmy-subscriber-bot -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' --restart always lflare/lemmy-subscriber-bot --instances 'lemmy.ml,beehaw.org'

# To run it except selected instances
docker run --name lemmy-subscriber-bot -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' --restart always lflare/lemmy-subscriber-bot --instances '!badlemmy.com'

## OR

docker build -t lemmy-subscriber-bot .
docker run --name lemmy-subscriber-bot --restart always -dt --env 'LEMMY_USERNAME=subscriber_bot' --env 'LEMMY_PASSWORD=subscriber_bot' --env 'LEMMY_DOMAIN=lemmy.world' lemmy-subscriber-bot
```

### Manual

```bash
$ pip3 install -r requirements.txt
usage: bot.py [-h] [-v] [--database DATABASE] [--domain DOMAIN] [--username USERNAME] [--password PASSWORD]
              [--threshold-add THRESHOLD_ADD] [--threshold-subscribe THRESHOLD_SUBSCRIBE] [--daemon]
              [--daemon-delay DAEMON_DELAY] [--instances INSTANCES]

lemmy-subscriber

options:
  -h, --help            show this help message and exit
  -v, --verbose
  --database DATABASE
  --domain DOMAIN
  --username USERNAME
  --password PASSWORD
  --threshold-add THRESHOLD_ADD
  --threshold-subscribe THRESHOLD_SUBSCRIBE
  --daemon
  --daemon-delay DAEMON_DELAY
  --instances INSTANCES
                        comma-separated instances, e.g. 'lemmy.ml,beehaw.org'
$ python3 bot.py --domain lemmy.world --username subscriber_bot --password subscriber_bot
```

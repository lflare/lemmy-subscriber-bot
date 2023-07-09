# Lemmy Subscriber Bot (LSB)

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

## FAQ

### What was the motivation behind this?

As of the writing of this tool (Jul 2023), there is no easy way for personal/small Lemmy instance users to discover communities outside of their own. You might suggest using one of the many aggregators out there, like [Lemmy Explorer](https://lemmyverse.net/), but the whole act of adding a community, one by one, is a painful, arduous and unintuitive experience altogether. This tool was written to give the users of the instance a view of what communities might be out there without having to jump through hoops, and if popular enough (meeting the requirements of the bot subscribing), an overview of the community without the user having to subscribe to it.

### Wouldn't this cause unnecessary load on upstream servers?

Well, yes. It is undeniable that in the wrong hands, this tool, and by extension, the many tools just like this, can cause havoc on the larger Lemmy instances out there. As of this writing, I do not have a solution for that, except to try and alleviate some possible causes for concern by only subscribing to the most active communities that an average Lemmy user might find interesting.

### How much disk space is this tool expected to cause?

As of the writing of this tool, and size of the fediverse (Jul 2023), using this tool, may result in disk space usage of around 2GiB/day, according to my own metrics. 

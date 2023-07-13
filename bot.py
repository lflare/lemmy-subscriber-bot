#! /usr/bin/env python3
##
import argparse
import functools
import json
import os
import queue
import random
import re
import shelve
import sys
import threading
import time
from typing import Tuple

import requests
from loguru import logger

# Prepare logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Set default timeout
timeout = 15

# Prepare global session and timeout
session = requests.Session()
session.request = functools.partial(session.request, timeout=timeout)


class Bot:
    def __init__(
        self,
        domain,
        username,
        password,
        threshold_resolve,
        threshold_subscribe,
        daemon,
        daemon_delay,
        only_instances=[],
        bad_instances=[],
        database="database.db",
    ):
        self.db = shelve.open(database)
        self.domain = domain
        self.username = username
        self.password = password
        self.threshold_resolve = threshold_resolve
        self.threshold_subscribe = threshold_subscribe
        self.daemon = daemon
        self.daemon_delay = daemon_delay
        self.instances = []
        self.bad_instances = []

        # Prepare bot runtime variables
        self.rq = queue.Queue(16)
        self.sq = queue.Queue(16)
        self.jwt = None

        # Override instances
        if len(only_instances) > 0:
            self.instances = only_instances
        if len(bad_instances) > 0:
            self.bad_instances = bad_instances

        # Check db
        if "_version" not in self.db:
            self.db.clear()
            self.db["_version"] = 1
        if self.db["_version"] == 1:
            pass

        # Print statistic
        self.print_statistic()

    def print_statistic(self):
        resolved = 0
        subscribed = 0
        for k, v in self.db.items():
            if k == "_version":
                continue
            resolved += 1
            if v == -1:
                subscribed += 1
        logger.info(f"{resolved = } | {subscribed = }")

    def start(self):
        # Get JWT
        self.retrieve_jwt()

        # Start background threads
        rt = threading.Thread(target=self.community_resolver_thread)
        rt.daemon = True
        rt.start()
        st = threading.Thread(target=self.community_subscriber_thread)
        st.daemon = True
        st.start()

        while True:
            # Fill instances if not manually defined
            if self.instances is None or len(self.instances) == 0:
                self.instances = self.get_instances()

            # Loop through instances
            for instance in self.instances:
                # Skip bad instances
                if instance in self.bad_instances:
                    continue

                # Otherwise, get communities
                communities = self.get_instance_communities(instance)

            # Print statistics
            logger.success("finished instance iteration")
            self.print_statistic()

            # Handle daemon
            if self.daemon:
                logger.success(f"sleeping for {self.daemon_delay} seconds")
                time.sleep(self.daemon_delay)
                continue
            else:
                break

        # Exit queues
        self.rq.put(None)
        self.sq.put(None)

        # Rejoin threads
        rt.join()
        st.join()

    def reset(self):
        # Get JWT
        self.retrieve_jwt()

        # Get all subscribed communities
        communities = []
        for i in range(1, 999):
            try:
                # Get and parse community list
                r = session.get(
                    f"https://{self.domain}/api/v3/community/list?type_=Subscribed&show_nsfw=true&page={i}&auth={self.jwt}"
                )
                r_json = r.json()
                if len(r_json["communities"]) == 0:
                    break

                # Add to communities
                communities.extend(r_json["communities"])
            except requests.exceptions.JSONDecodeError as e:
                break
            except requests.exceptions.Timeout as e:
                logger.error(f"failed to get lemmyverse.net instances - {e}")
                break
            except Exception as e:
                logger.exception(e)
                break
        logger.debug(f"got {len(communities)} communities from server")

        # Loop through communities and unsubscribe
        i = 0
        for community in communities:
            if len(self.bad_instances) > 0:
                actor_id = community["community"]["actor_id"]
                instance = actor_id.split("/")[2]
                if instance not in self.bad_instances:
                    continue
            self.unsubscribe_community(community["community"]["actor_id"], community["community"]["id"])
            i += 1
        logger.info(f"unsubscribed from {i}/{len(communities)} communities")

    @logger.catch(reraise=True, message="failed to login")
    def retrieve_jwt(self):
        payload = {"username_or_email": self.username, "password": self.password}
        r = session.post(f"https://{self.domain}/api/v3/user/login", json=payload)
        self.jwt = r.json()["jwt"]
        logger.success(f"logged in as: {self.username}")

    def get_instances(self):
        # Loop through Lemmyverse instance URLs
        instances = []
        for i in range(999):
            try:
                # Get and parse instance list
                r = session.get(f"https://lemmyverse.net/data/instance/{i}.json")
                data = r.json()
                instances.extend(data)
            except requests.exceptions.JSONDecodeError:
                # expected exception, lemmyverse returns a valid html page once past last valid instance json
                break
            except requests.exceptions.Timeout as e:
                logger.error(f"failed to get lemmyverse.net instances - {e}")
                break
            except Exception as e:
                logger.exception(e)
                break

        # Get baseurls
        baseurls = []
        for instance in sorted(instances, key=lambda x: x["score"], reverse=True):
            # Check user count, and skip if below resolve threshold
            if instance["usage"]["users"]["activeHalfyear"] < self.threshold_resolve:
                continue

            # Add URL
            baseurls.append(instance["baseurl"])

        # Return results
        logger.info(f"loaded {len(baseurls)} instances from lemmyverse.net")
        return baseurls

    def get_instance_communities(self, instance):
        communities = []
        for page in range(1, 99999):
            try:
                logger.trace(f"retrieving - {instance} / page {page}")
                r = session.get(f"https://{instance}/api/v3/community/list?type_=Local&sort=TopSixMonths&page={page}")
                # sorting logic:
                # https://github.com/LemmyNet/lemmy/blob/0c82f4e66065b5772fede010a879d327135dbb1e/crates/db_views_actor/src/community_view.rs#L171
                r_json = r.json()
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"failed to get communities from '{instance}' - {e}: '{r.text}'")
                break
            except requests.exceptions.Timeout as e:
                logger.error(f"failed to get communities from '{instance}' - {e}")
                break
            except Exception as e:
                logger.exception("unhandled exception")
                break

            # If communities key is missing, break
            if "communities" not in r_json:
                break

            # If no communities, also break
            communities = r_json["communities"]
            if len(communities) == 0:
                break

            # Loop through and append community lists
            for c in communities:
                name = c["community"]["name"]
                users_active_half_year = c["counts"]["users_active_half_year"]
                actor_id = c["community"]["actor_id"]
                community_addr = actor_id
                logger.debug(f"COMMUNITY: {instance}/{name} - {name} - {users_active_half_year = }")

                # Check if users_active_half_year has passed threshold
                # to either resolve or subscribe.
                if users_active_half_year >= self.threshold_subscribe:
                    if community_addr in self.db and self.db[community_addr] == -1:
                        logger.debug(f"SKIPPING SUBSCRIBE: {instance}/{name}")
                        continue

                    logger.info(f"QUEUED SUBSCRIBE: {instance}/{name}")
                    self.sq.put(actor_id)

                elif users_active_half_year >= self.threshold_resolve:
                    if community_addr in self.db:
                        logger.debug(f"SKIPPING RESOLVE: {instance}/{name}")
                        continue

                    logger.info(f"QUEUED RESOLVE: {instance}/{name}")
                    self.rq.put(actor_id)

            # Break loop once sorted-by-subscribers community list drops
            # below threshold as there is likely no more communities
            # above threshold
            if communities[-1]["counts"]["users_active_half_year"] < self.threshold_resolve:
                break

    def resolve_community(self, community_addr) -> int:
        # Return if already subscribed in database
        if community_addr in self.db and self.db[community_addr] > 0:
            return self.db[community_addr]

        # Attempt to resolve
        try:
            r = session.get(f"https://{self.domain}/api/v3/resolve_object?q={community_addr}&auth={self.jwt}")
            r_json = r.json()
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"failed to resolve community - {e}: '{r.text}'")
            return 0
        except requests.exceptions.Timeout as e:
            logger.error(f"failed to resolve community - {e}")
            return 0
        except Exception as e:
            logger.exception("unhandled exception")
            return 0

        # Check if there is an error
        if "error" in r_json:
            if r_json["error"] == "couldnt_find_object":
                return 0

        # Return result
        logger.info(f"RESOLVED: {community_addr}")
        self.db[community_addr] = r_json["community"]["community"]["id"]
        return r_json["community"]["community"]["id"]

    def subscribe_community(self, community_addr):
        # Return if already subscribed in database
        if community_addr in self.db and self.db[community_addr] == -1:
            return

        # Try up to 5 times to subscribe to a community
        for _ in range(5):
            # Attempt to resolve
            id = self.resolve_community(community_addr)
            if id <= 0:
                continue

            # Attempt to subscribe
            try:
                follow_payload = {"community_id": id, "follow": True, "auth": self.jwt}
                r = session.post(f"https://{self.domain}/api/v3/community/follow", timeout=15, json=follow_payload)
                r_json = r.json()
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"failed to follow community - {e}: '{r.text}'")
                continue
            except requests.exceptions.Timeout as e:
                logger.error(f"failed to follow community - {e}: '{r.text}'")
                continue
            except Exception as e:
                logger.exception("unhandled exception")
                continue

            # Log and mark as subscribed in DB
            logger.trace(f"{community_addr} - {r.text}")
            logger.info(f"SUBSCRIBED: {community_addr}")
            self.db[community_addr] = -1
            break

    def unsubscribe_community(self, community_addr, community_id):
        # Try up to 5 times to unsubscribe to a community
        for _ in range(5):
            # Attempt to resolve
            id = self.resolve_community(community_addr)
            if id <= 0:
                continue

            # Attempt to unsubscribe
            try:
                follow_payload = {"community_id": id, "follow": False, "auth": self.jwt}
                r = session.post(f"https://{self.domain}/api/v3/community/follow", timeout=15, json=follow_payload)
                r_json = r.json()
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"failed to unsubscribe community - {e}: '{r.text}'")
                continue
            except requests.exceptions.Timeout as e:
                logger.error(f"failed to unsubscribe community - {e}: '{r.text}'")
                continue
            except Exception as e:
                logger.exception("unhandled exception")
                continue

            # Log and mark as subscribed in DB
            logger.trace(f"{community_addr} - {r.text}")
            logger.info(f"UNSUBSCRIBED: {community_addr}")
            self.db[community_addr] = community_id
            break

    def community_resolver_thread(self):
        while True:
            community_addr = self.rq.get()
            if community_addr is None:
                return
            if community_addr in self.db:
                continue

            self.resolve_community(community_addr)
            time.sleep(1)

    def community_subscriber_thread(self):
        while True:
            community_addr = self.sq.get()
            if community_addr is None:
                return
            if community_addr in self.db and self.db[community_addr] == -1:
                continue

            self.subscribe_community(community_addr)
            time.sleep(1)


def main():
    # Get and parse arguments
    parser = argparse.ArgumentParser(description="lemmy-subscriber")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--reset", action="store_true", default=False)
    parser.add_argument("--database", default=os.environ.get("LEMMY_DATABASE"))
    parser.add_argument("--domain", default=os.environ.get("LEMMY_DOMAIN"))
    parser.add_argument("--username", default=os.environ.get("LEMMY_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("LEMMY_PASSWORD"))
    parser.add_argument("--threshold-add", default=os.environ.get("LEMMY_THRESHOLD_ADD", 50))
    parser.add_argument("--threshold-subscribe", default=os.environ.get("LEMMY_THRESHOLD_SUBSCRIBE", 100))
    parser.add_argument("--daemon", action="store_true", default=False)
    parser.add_argument("--daemon-delay", default=86400)
    parser.add_argument("--instances", type=str, help="comma-separated instances, e.g. 'lemmy.ml,beehaw.org'")
    args = parser.parse_args()
    if not args.domain or not args.username or not args.password:
        exit(parser.print_usage())

    # Verbosity configuration
    if args.verbose == 1:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    elif args.verbose > 1:
        logger.remove()
        logger.add(sys.stdout, level="TRACE")

    # Instances seed
    only_instances = []
    bad_instances = []
    if args.instances:
        instances = args.instances.split(",")
        for instance in instances:
            if instance.startswith("!"):
                bad_instances.append(instance[1:])
            else:
                only_instances.append(instance)

    # Create bot
    bot = Bot(
        domain=args.domain,
        username=args.username,
        password=args.password,
        threshold_resolve=args.threshold_add,
        threshold_subscribe=args.threshold_subscribe,
        daemon=args.daemon,
        daemon_delay=args.daemon_delay,
        only_instances=only_instances,
        bad_instances=bad_instances,
    )

    if args.reset:
        # Reset?
        bot.reset()
    else:
        # Start bot
        bot.start()


if __name__ == "__main__":
    main()

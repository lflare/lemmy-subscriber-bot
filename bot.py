#! /usr/bin/env python3
##
import argparse
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

logger.remove()
logger.add(sys.stdout, level="INFO")


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

        self.rq = queue.Queue(16)
        self.sq = queue.Queue(16)
        self.jwt = None

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

        # Loop through instances
        while True:
            for instance in self.get_instances():
                communities = self.get_instance_communities(instance)

            logger.success("finished instance iteration")
            if self.daemon:
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

    def retrieve_jwt(self):
        payload = {"username_or_email": self.username, "password": self.password}
        r = requests.post(f"https://{self.domain}/api/v3/user/login", json=payload)

        try:
            self.jwt = r.json()["jwt"]
            logger.success(f"LOGGED IN AS {self.username}")
        except KeyError as e:
            logger.error(r.text)
            raise e

    def get_instances(self):
        r = requests.get(
            "https://raw.githubusercontent.com/maltfield/awesome-lemmy-instances/main/awesome-lemmy-instances.csv"
        )
        results = re.findall(r"\(https://(.*)\)", r.text)
        return results

    def get_instance_communities(self, instance):
        communities = []

        try:
            for page in range(1, 99999):
                r = requests.get(f"https://{instance}/api/v3/community/list?sort=Hot&page={page}")

                try:
                    if "communities" not in r.json():
                        break

                    r = r.json()["communities"]
                    if len(r) == 0:
                        break

                    # Loop through and append community lists
                    for c in r:
                        name = c["community"]["name"]
                        users_active_half_year = c["counts"]["users_active_half_year"]
                        actor_id = c["community"]["actor_id"]
                        logger.debug(f"{instance}/{name} - {name} - {users_active_half_year = }")

                        # Check if users_active_half_year has passed threshold
                        # to either resolve or subscribe.
                        if users_active_half_year >= self.threshold_subscribe:
                            logger.info(f"QUEUED SUBSCRIBE: {instance}/{name}")
                            self.sq.put(actor_id)
                        elif users_active_half_year >= self.threshold_resolve:
                            logger.info(f"QUEUED RESOLVE: {instance}/{name}")
                            self.rq.put(actor_id)

                    # Break loop once sorted-by-subscribers community list drops
                    # below threshold as there is likely no more communities
                    # above threshold
                    if r[-1]["counts"]["users_active_half_year"] < self.threshold_resolve:
                        break
                except Exception as e:
                    logger.catch(e)
        except Exception as e:
            logger.catch(e)

    def resolve_community(self, community_addr) -> Tuple[int, bool]:
        # Return if already subscribed in database
        if community_addr in self.db and self.db[community_addr] == True:  # Yes, I explicitly compared against == True.
            return -1, True

        # Attempt to resolve
        r = requests.get(f"https://{self.domain}/api/v3/resolve_object?q={community_addr}&auth={self.jwt}")
        logger.trace(
            f"{community_addr} - {r.text} - https://{self.domain}/api/v3/resolve_object?q={community_addr}&auth={self.jwt}"
        )
        if "error" in r.json():
            if r.json()["error"] == "couldnt_find_object":
                return -1, False
        logger.info(f"RESOLVED: {community_addr}")

        # Return result
        return r.json()["community"]["community"]["id"], True

    def subscribe_community(self, community_addr):
        # Return if already subscribed in database
        if community_addr in self.db and self.db[community_addr] == True:  # Yes, I explicitly compared against == True.
            return

        # Try up to 5 times to subscribe to a community
        for _ in range(5):
            try:
                # Attempt to resolve
                id, resolved = self.resolve_community(community_addr)
                if not resolved:
                    continue

                # Attempt to subscribe
                follow_payload = {"community_id": id, "follow": True, "auth": self.jwt}
                r = requests.post(f"https://{self.domain}/api/v3/community/follow", timeout=15, json=follow_payload)
                logger.trace(f"{community_addr} - {r.text}")
                logger.info(f"SUBSCRIBED: {community_addr}")

                # Mark as subscribed in DB
                self.db[community_addr] = True
                break
            except KeyError:
                time.sleep(5)
                continue
            except Exception as e:
                logger.exception(e)
                time.sleep(5)
                continue

    def community_resolver_thread(self):
        while True:
            community_addr = self.rq.get()
            if community_addr is None:
                return
            if community_addr in self.db and self.db[community_addr] == True:
                continue

            self.resolve_community(community_addr)
            time.sleep(1)

    def community_subscriber_thread(self):
        while True:
            community_addr = self.sq.get()
            if community_addr is None:
                return
            if community_addr in self.db and self.db[community_addr] == True:
                continue

            self.subscribe_community(community_addr)
            time.sleep(1)


def main():
    # Get and parse arguments
    parser = argparse.ArgumentParser(description="lemmy-subscriber")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--database", default=os.environ.get("LEMMY_DATABASE"))
    parser.add_argument("--domain", default=os.environ.get("LEMMY_DOMAIN"))
    parser.add_argument("--username", default=os.environ.get("LEMMY_USERNAME"))
    parser.add_argument("--password", default=os.environ.get("LEMMY_PASSWORD"))
    parser.add_argument("--threshold-add", default=os.environ.get("LEMMY_THRESHOLD_ADD", 10))
    parser.add_argument("--threshold-subscribe", default=os.environ.get("LEMMY_THRESHOLD_SUBSCRIBE", 50))
    parser.add_argument("--daemon", action="store_true", default=False)
    parser.add_argument("--daemon-delay", default=3600)
    args = parser.parse_args()
    if not args.domain or not args.username or not args.password:
        exit(parser.print_usage())

    if args.verbose == 1:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")
    elif args.verbose > 1:
        logger.remove()
        logger.add(sys.stdout, level="TRACE")

    # Create bot
    bot = Bot(
        domain=args.domain,
        username=args.username,
        password=args.password,
        threshold_resolve=args.threshold_add,
        threshold_subscribe=args.threshold_subscribe,
        daemon=args.daemon,
        daemon_delay=args.daemon_delay,
    )

    # Start bot
    bot.start()


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
docker-compose -f /drone/src/docker-compose.yml -f /drone/src/docker-compose.prod.yml config > /drone/src/docker-compose.processed.yml
docker stack deploy -c /drone/src/docker-compose.processed.yml moodle-scraper

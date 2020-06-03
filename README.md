# moodle-scraper

## Motivation

This project started because of an annoyance I had with having to check the Moodle website several times manually per day for each course I was taking to see if my profs uploaded something new. As well as sometimes profs would upload files with formats such as .pptx. I believe that .pdf is the most convenient format to distribute lectures, assignment sheets, etc.

---
[![Build Status](https://drone.gordon-pn.com/api/badges/gordonpn/moodle-scraper/status.svg)](https://drone.gordon-pn.com/gordonpn/moodle-scraper)
![Healthchecks.io](https://healthchecks.io/badge/603efbcd-b70d-424d-91cc-6560ba83d5eb/Workecps.svg)
![Last commit on develop](https://badgen.net/github/last-commit/gordonpn/moodle-scraper/develop)
![License](https://badgen.net/github/license/gordonpn/moodle-scraper)

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/gordonpn)

## Description

A Moodle scraper written for Concordia's Moodle. It may or may not work for other schools, but that remains untested and I have no intention of trying. Thus, I did not provide a way to configure the moodle website url.

This Python program will download pdf, ppt, txt, xls and zip files from each course that it can find on your Moodle dashboard.

It can, optionally, convert ppt files into pdf files.

The program will organize the files per course, into respective directories.

If the professor wrote notes on the page, it will also save those notes into a txt file.

## Demo

[![asciicast](https://asciinema.org/a/frSwrV8ak9aOnSPEAXISTHejL.svg)](https://asciinema.org/a/frSwrV8ak9aOnSPEAXISTHejL)

## Usage

```sh
usage: main.py [-h] [-a] [-d DIRECTORY] [-u USERNAME] [-p PASSWORD] [-c]

optional arguments:
  -h, --help            show this help message and exit
  -a, --automated       run the moodle scraper on a schedule
  -d DIRECTORY, --directory DIRECTORY
                        specify directory to save files
  -u USERNAME, --username USERNAME
                        your moodle username
  -p PASSWORD, --password PASSWORD
                        your moodle password
  -c, --convert         convert to PDF using LibreOffice after downloading. this option has only been tested on Ubuntu
```

There are two ways to use this Python program.

1. In a Docker container
2. The script as it is

### Using Docker

I prefer using it in a Docker container as I can run it on my home server and have it automated to run on a schedule.

If used this way, then you must set some environment variables: `MOODLE_USERNAME`, `MOODLE_PASSWORD`, `MOODLE_DIRECTORY`.

`MOODLE_DIRECTORY` is where you'd like your files to be saved on the host machine.

Then run `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --detach` from within the cloned repository.

If you do not want it to be automated, then you can use the `docker-compose.dev.yml` as that one will run once and terminate.

`docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --detach`

### As a script

After you have cloned the repository.

You need Python3 installed.

```sh
pip install -r requirements.txt
python ./main.py -u bob -p alice
```

## Configuration

The only configuration offered at this time is exclusion of courses.

Inside the `excluded-courses.ini` file, add the course title(s) as they appear on your Moodle dashboard (or part of it):

```
[moodle-scraper]
exclusions =
```

## Support

You may open an issue.

## Roadmap / Todo

Check out the [open issues](https://github.com/gordonpn/moodle-scraper/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc) for ideas and features I have planned!

## Authors

Myself [@gordonpn](https://github.com/gordonpn)

## License

[MIT License](./LICENSE)

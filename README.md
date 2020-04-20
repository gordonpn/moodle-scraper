# moodle-scraper

## Motivation

This project started because of an annoyance I had with having to check the Moodle website several times manually per day for each course I was taking to see if my profs uploaded something new. As well as sometimes profs would upload files with formats such as .pptx. I believe that .pdf is the most convenient format to distribute lectures, assignment sheets, etc.

---
![GitHub](https://img.shields.io/github/license/gpnn/moodle-scraper)
[![Build Status](https://drone.gordon-pn.com/api/badges/gordonpn/moodle-scraper/status.svg)](https://drone.gordon-pn.com/gordonpn/moodle-scraper)
![Healthchecks.io](https://healthchecks.io/badge/ca24ff5d-8821-4d86-8a5a-dc92cf/kCadkBM0.shields)

![GitHub top language](https://img.shields.io/github/languages/top/gpnn/moodle-scraper)
![GitHub language count](https://img.shields.io/github/languages/count/gpnn/moodle-scraper)

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/gpnn/moodle-scraper)
![GitHub last commit](https://img.shields.io/github/last-commit/gpnn/moodle-scraper)

## Description

A Moodle scraper written for Concordia's Moodle. It may or may not work for other schools, but that remains untested and I have no intention of trying. Thus, I did not provide a way to configure the moodle website url.

This Python program will download pdf, ppt, txt, xls and zip files from each course that it can find on your Moodle dashboard.

It can, optionally, convert ppt files into pdf files.

The program will organize the files per course, into respective directories.

If the professor wrote notes on the page, it will also save those notes into a txt file.

## Usage

```
usage: moodle_scraper.py [-h] [-a] [-d DIRECTORY] [-u USERNAME] [-p PASSWORD] [-c]

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

Then run `docker-compose up --detach` from within the cloned repository.

If you do not want it to be automated, then you can use the `docker-compose.dev.yml` as that one will run once and terminate.

`docker-compose -f docker-compose.dev.yml up --detach`

### As a script

After you have cloned the repository.

You need Python3 installed.

```bash
pip install -r requirements.txt
python ./moodle_scraper.py -u bob -p alice
```

## Configuration

The only configuration offered at this time is exclusion of courses.

Inside the `excluded-courses.ini` file, add the course title(s) as they appear on your Moodle dashboard (or part of it):
````
[moodle-scraper]
exclusions =
````

## Support

You may open an issue.

## Roadmap

*  [x] Support other possible file types
*  [x] Improve running time by using async or threads
*  [x] Refactor code for better maintainability
*  [x] Add command line flags to skip conversion

## License

[MIT License](./LICENSE)

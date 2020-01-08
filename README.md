# moodle-scraper

## Description

This project started because of an annoyance I had with having to check the Moodle website several times manually per day for each course I was taking to see if my profs uploaded something new. As well as sometimes profs would upload files with formats such as .docx or .pptx. I believe that .pdf is the most convenient format to distribute lectures, assignment sheets, etc.

---
![GitHub](https://img.shields.io/github/license/gpnn/moodle-scraper?style=flat-square)

![GitHub top language](https://img.shields.io/github/languages/top/gpnn/moodle-scraper?style=flat-square)
![GitHub language count](https://img.shields.io/github/languages/count/gpnn/moodle-scraper?style=flat-square)

![GitHub commit activity](https://img.shields.io/github/commit-activity/m/gpnn/moodle-scraper?style=flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/gpnn/moodle-scraper?style=flat-square)

## Description

A Moodle scraper written for Concordia's Moodle. It may or may not work for other schools, but that remains untested and I have no intention of trying. Thus, I did not provide a way to configure the moodle website in the configuration file.

Each time this script is ran, it will download the PDF and PPT files into the root of where this project is cloned (unless defined otherwise, more on that later) and neatly organize them in their respective directories named after the course name. It will also scrape any information that the prof wrote themselves on the Moodle page and neatly put that text in a .txt file.

It will then convert the PowerPoint files to the .pdf format.

## Installation

1.  Clone the repo
2.  You must have Python3 installed and pip3 installed
3.  Install the requirements
````bash
pip3 install -r requirements.txt
````
## Configuration

Create a file and name it `moodle-scraper.conf` with the following contents:
````
[moodle-scraper]
username = 
password = 
folder =
exclusions =
````

Where `username` is your moodle username and `password` is your moodle password.
You may also use environment variables to store your moodle username and moodle password.

`folder` is the root folder where you want the scrapings to be stored. Can be left undefined and the script will save them where you cloned the project.

`exclusions` is a list of moodle courses you want to exclude from scraping. Sometimes profs do not deactivate a certain course after the semester is over and thus the course becomes irrelevant to the current semester. Each course you list here is comma (,) separated. You may list the full course name as on moodle or part of the name as well.

## Usage

Simply run the application and enjoy
````bash
python3 moodle-scraper.py
````

## Support

You can contact me if there are any questions or problems, or open an issue.

## Roadmap and todo

*  [ ] Support other possible file types
*  [x] Improve running time by using async or threads
*  [x] Refactor code for better maintainability
*  [ ] Add command line flags to skip conversion

## License

[MIT License](https://choosealicense.com/licenses/mit/)

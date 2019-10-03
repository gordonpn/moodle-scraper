# moodle-scraper

## Description

A Moodle scraper written for Concordia's Moodle. It may or may not work for other schools, but that remains untested and I have no intention of trying. Thus, I did not provide a way to configure the moodle website in the configuration file.

This project started because of an annoyance I had with having to check the Moodle website several times manually per day for each course I was taking to see if my profs uploaded something new.

Each time this script is run, it will download the PDF and PPT files into the root of where the .py file residing (unless defined otherwise) and neatly organize them in their respective directories named after the course name. It will also scrape any information that the prof wrote themselves on the Moodle page and neatly put that text in a .txt file.

## Installation

1.  Clone the repo
2.  You must have Python3 installed and pip3 installed
3.  Install the requirements
````bash
pip3 install -r requirements.txt
````

## Usage

1.  Edit the configuration 'moodle-scraper.conf' with the needed information (you could also put your username and password as environment variables if you don't feel safe and know how to)
    *  If you decide to use environment variables, you must set them as MOODLE_USERNAME and MOODLE_PASSWORD
    *  You may also define a root folder where the scraper will save the files
2.  Simply run the application and enjoy
````bash
python3 moodle-scraper.py
````

## Support

You can contact me if there are any questions or problems, or open an issue.

## Roadmap and todo

*  [ ] Support other possible file types
*  [ ] Improve running time by using async or threads

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. 

## License

[MIT License](https://choosealicense.com/licenses/mit/)

## Project status

This project will be maintained as long as I am in school.
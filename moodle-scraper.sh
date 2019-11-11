cd /mnt/ssddrive/resilio-sync/jenkins/moodle-scraper || exit
pip3 install -r requirements.txt
python3 moodle-scraper.py

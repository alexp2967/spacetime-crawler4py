from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                with open("report.txt", "a") as file:
                    file.write("UNIQUE URLS\n")
                    file.write("\n".join(scraper.unique_urls) + "\n")  # Join set elements with newlines

                    # Write longest page - ensure it's a string
                    file.write("LONGEST PAGE\n")
                    file.write(str(scraper.longest_page) + "\n")

                    # Write top 50 words - ensure it's a string or join list items if it's a list
                    file.write("TOP 50 WORDS\n")
                    file.write("\n".join([f"{word}: {count}" for word, count in scraper.get_top_50_words()]) + "\n")


                    # Write subdomains - if it's a dictionary, convert it to a string with formatting
                    file.write("SUBDOMAINS\n")
                    for subdomain, count in sorted(scraper.subdomain_dict.items()):
                        file.write(f"{subdomain}: {count}\n")
                    file.close()
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)

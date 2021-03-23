import time
import re
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def scrape_etsy_listing(listing_url, driver):
    """
    scrapes the actual listing

    :param listing_url:
    :param driver:
    :return:
    """
    results = dict()
    title = ""
    price = 0
    shop_sales = 0
    item_reviews = 0
    shop_reviews = 0
    on_etsy_since = 0
    reviews = list()

    driver.get(listing_url)

    # click accept on Etsy Privacy Settings
    try:
        accept_btn = driver.find_element_by_xpath("/html/body/div[9]/div[2]/div/div[2]/div[2]/button")
        accept_btn.click()
    except NoSuchElementException:
        # if there is no accept privacy button just continue
        pass

    # wait a bit for the window to disappear
    time.sleep(2)

    title = driver.find_element_by_xpath(
        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div[2]/div/h1").text

    price = driver.find_element_by_xpath(
        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div[3]/div[1]/div/div[1]/p[1]").text

    # price is now e.g.: "Price:\nUSD 17.95+"
    # split it at whitespace and just take the number
    price = price.split(" ")[1]

    # check if "+" sign is in number and remove it
    if "+" in price:
        price = price.replace("+", "")

    # convert price to float
    price = float(price)

    shop_sales = driver.find_element_by_xpath(
        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[2]/div/div/div[1]/div/div/a/span[1]").text

    # shop_sales is now e.g.: "113,109 sales"
    # split on whitespace and just take the number
    # and remove ","
    shop_sales = shop_sales.split(" ")[0].replace(",", "")
    # convert to int
    shop_sales = int(shop_sales)

    # select newest comments
    try:
        select_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,
                                            "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/button/span[1]"))
        )
        # select_field = driver.find_element_by_xpath("/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/button/span[1]")
    except:
        driver.refresh();

        select_field = driver.find_element_by_xpath(
            "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/button/span[1]")

    select_field.click()

    time.sleep(2)
    newest_btn = driver.find_element_by_xpath(
        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div[2]/div[1]/div[2]/div/div/button[2]")
    newest_btn.click()

    # wait a bit for the newest comments to appear
    time.sleep(1.5)

    item_reviews = driver.find_element_by_xpath(
        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div[2]/div[1]/div[1]/button[1]/span").text
    # convert to int
    item_reviews = int(item_reviews)

    shop_reviews = driver.find_element_by_xpath(
        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[1]/div/div/h3").text

    # shop_reviews is now e.g.: "18,259 reviews\n5 out of 5 stars"
    # we just want to number and remove the comma
    shop_reviews = shop_reviews.split(" ")[0].replace(",", "")
    # convert to int
    shop_reviews = int(shop_reviews)

    try:
        on_etsy_since = driver.find_element_by_xpath(
            "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[3]/div/div[4]/div[2]/div[2]/p[2]").text
    except NoSuchElementException:
        on_etsy_since = driver.find_element_by_xpath(
            "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[3]/div/div[3]/div[2]/div[2]/p[2]").text

    # convert to int
    on_etsy_since = int(on_etsy_since)

    # in case there are no reviews anymore within 10 potential pages, break
    should_we_break = False

    # get review dates for first 10 pages
    for i in range(10):

        print("Scraping comment page: %d" % (i + 1))

        # regexp to find date in string
        regexp = r"(Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)\s+\d{1,2},\s+\d{4}"

        # 4 reviews per page
        for j in range(1, 5):
            review_xpath = "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/div[2]/div[2]/div/div[" + str(
                j) + "]/div[1]/p"
            try:
                review_date = driver.find_element_by_xpath(review_xpath).text
            except NoSuchElementException:
                # the review element is not present, that means there are no reviews on this page anymore
                # break out
                should_we_break = True
                break  # break from inner loop

            match = re.search(regexp, review_date)
            date = datetime.strptime(match.group(), "%b %d, %Y").date()

            # check if review_date is later than 30 days
            if ((datetime.date(datetime.now()) - date).days) > 30:
                should_we_break = True
                break

            reviews.append({"date": date})
            time.sleep(1)

        if should_we_break:  # no more reviews
            break

        # check if next button even exists (only 1 review page)
        try:
            driver.find_element_by_xpath(
                "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[6]/a/span[2]")
        except NoSuchElementException:
            try:
                driver.find_element_by_xpath(
                    "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[5]/a/span[2]")
            except NoSuchElementException:
                try:
                    driver.find_element_by_xpath(
                        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[4]/a/span[2]")
                except NoSuchElementException:
                    # there is only one review page, break
                    print("There is only 1 review page!")
                    break

        # click next page
        # after the second page the xpath changes and it stays like that until second last page
        if i > 1:  # index starts from 0
            try:
                driver.find_element_by_xpath(
                    "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[7]/a/span[2]").click()
            except NoSuchElementException:
                # layout is different, handle it
                try:
                    driver.find_element_by_xpath(
                        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[6]/a/span[2]").click()
                except NoSuchElementException:
                    # there are only 2 pages of reviews, break out
                    print("There is no comment page 3!")
                    break
        else:
            try:
                driver.find_element_by_xpath(
                    "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[6]/a/span[2]").click()
            except NoSuchElementException:
                # layout is different, handle it
                try:
                    driver.find_element_by_xpath(
                        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[5]/a/span[2]").click()
                except NoSuchElementException:
                    # there are only 2 pages of reviews, handle it
                    driver.find_element_by_xpath(
                        "/html/body/div[6]/div[1]/div[1]/div/div/div[1]/div[4]/div/div/div[1]/div/div[2]/nav/ul/li[4]/a/span[2]").click()

        # wait a bit for the new page 
        time.sleep(0.8)

    # fill in results
    results["title"] = title
    results["price"] = price
    results["shop_sales"] = shop_sales
    results["item_reviews"] = item_reviews
    results["shop_reviews"] = shop_reviews
    results["on_etsy_since"] = on_etsy_since
    results["reviews"] = reviews

    # driver.close()

    return results


def main():
    links = [
        "https://www.etsy.com/listing/220795317/octopus-playing-drums-mens-t-shirt-gift?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-1&bes=1&col=1",
        "https://www.etsy.com/listing/288539665/trees-t-shirt-mens-t-shirt-nature-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-2&frs=1&bes=1&col=1",
        "https://www.etsy.com/listing/248684698/steven-universe-greg-and-rose-offer-pack?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-3",
        "https://www.etsy.com/listing/501770698/thin-blue-line-shirt-police-usa-flag?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-4&bes=1",
        "https://www.etsy.com/listing/495446716/march-for-science-bill-nye-the-science?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-5&col=1",
        "https://www.etsy.com/listing/208260943/crater-lake-oregon-womens-graphic-tee?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-6&pro=1",
        "https://www.etsy.com/listing/522684173/disney-castle-shirts-disney-2020-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-7&col=1",
        "https://www.etsy.com/listing/266486892/nap-queen-t-shirt-tee-shirt-top-high?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-8&pro=1&col=1",
        "https://www.etsy.com/listing/493033226/uncle-shirt-uncle-the-man-the-myth-the?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-9&pro=1&col=1",
        "https://www.etsy.com/listing/565707157/mom-of-girls-shirt-girl-mom-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-10&cns=1",
        "https://www.etsy.com/listing/187584322/pho-sho-shirt-funny-t-shirt-tank-t-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-11&pro=1&col=1",
        "https://www.etsy.com/listing/546600886/dog-mom-comfort-colors-long-sleeve-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-12&pro=1&col=1",
        "https://www.etsy.com/listing/495739392/warning-may-spontaneously-talk-about?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-13",
        "https://www.etsy.com/listing/295233763/fathers-day-gift-for-papaw-what-an?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-14&frs=1",
        "https://www.etsy.com/listing/483438293/being-normal-is-vastly-overrated-graphic?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-15&bes=1",
        "https://www.etsy.com/listing/273937486/personalized-t-shirt-add-your-own-text?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-16&bes=1&col=1",
        "https://www.etsy.com/listing/514455202/mens-retro-vintage-nasa-worm-logo?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-17",
        "https://www.etsy.com/listing/276952608/sweet-candy-boat-tours-chocolate-factory?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-18&frs=1&col=1",
        "https://www.etsy.com/listing/398738157/bicycle-gift-bike-gift-bike-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-19&pro=1&col=1",
        "https://www.etsy.com/listing/499054248/beacon-hills-lacrosse-t-shirt-teen-wolf?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-20&bes=1",
        "https://www.etsy.com/listing/272577312/creature-from-the-black-lagoon-shirt-old?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-21&frs=1",
        "https://www.etsy.com/listing/206149105/gift-for-husband-gun-t-shirt-i-love-it?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-22&frs=1&col=1",
        "https://www.etsy.com/listing/156164406/mens-tshirt-all-cotton-old-radio-diagram?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-23",
        "https://www.etsy.com/listing/255477694/cats-on-synthesizers-in-space-grey-t?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-24&bes=1",
        "https://www.etsy.com/listing/461070718/vegan-t-shirt-vegan-t-shirt-vegan-tshirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-25",
        "https://www.etsy.com/listing/77427174/acoustic-guitar-t-shirt-musician-tee?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-26&pro=1&frs=1&col=1",
        "https://www.etsy.com/listing/244155436/nasa-vintage-insignia-adult-t-shirts?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-27&col=1",
        "https://www.etsy.com/listing/98115657/mens-t-shirt-deer-tree-antlers-bird-tee?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-28&pro=1&frs=1&col=1",
        "https://www.etsy.com/listing/530357232/dad-and-baby-matching-shirts-father-son?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-29&frs=1&bes=1",
        "https://www.etsy.com/listing/512849352/firefighter-dad-gift-firefighter-dad?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-30&pro=1&col=1",
        "https://www.etsy.com/listing/256938220/girls-t-shirt-from-friends-l-womens?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-31&pro=1&col=1",
        "https://www.etsy.com/listing/250414222/boobs-boob-shirt-tshirt-t-shirt-t-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-32&cns=1&col=1",
        "https://www.etsy.com/listing/197107605/this-is-what-an-awesome-uncle-looks-like?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-33&pro=1&col=1",
        "https://www.etsy.com/listing/555497067/texas-shirt-home-shirt-texas-t-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-34&pro=1&col=1",
        "https://www.etsy.com/listing/386963954/woman-up-t-shirt-feminism-clothing-woman?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-35&pro=1&col=1",
        "https://www.etsy.com/listing/202325191/daydreamer-slogan-t-shirt-girls-womens?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-36&pro=1&frs=1&col=1",
        "https://www.etsy.com/listing/290970133/the-universe-is-made-of-protons-neutrons?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-37&pro=1&frs=1&col=1",
        "https://www.etsy.com/listing/568398501/cute-but-psycho-shirt-funny-tshirts?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-38",
        "https://www.etsy.com/listing/476779697/mens-4-in-1-silhouette-star-wars-t-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-39&frs=1",
        "https://www.etsy.com/listing/531825925/mu-alum-shirt-monsters-university-movie?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-40&col=1",
        "https://www.etsy.com/listing/555429269/creepy-cute-bat-t-shirt-pastel-goth?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-41&pro=1&frs=1",
        "https://www.etsy.com/listing/90912669/star-wars-darth-vader-riding-bike-father?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-42&cns=1",
        "https://www.etsy.com/listing/248410610/nhl-san-jose-sharks-hockey-disney-star?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-43",
        "https://www.etsy.com/listing/249784196/distressed-oversize-flannel-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-44",
        "https://www.etsy.com/listing/257612184/oranges-food-screen-printed-t-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-45&bes=1",
        "https://www.etsy.com/listing/384588902/funcle-shirt-uncle-shirt-new-uncle-gift?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-46&col=1",
        "https://www.etsy.com/listing/545444812/nutella-pocket-size-print-tshirt-shirt?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-47&pro=1&col=1",
        "https://www.etsy.com/listing/225706915/squid-t-shirt-mens-shirt-optical?ga_order=most_relevant&ga_search_type=all&ga_view_type=gallery&ga_search_query=&ref=sr_gallery-1-48&bes=1&col=1"
    ]

    # binary = FirefoxBinary('/usr/lib64/firefox/firefox')

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    # driver = webdriver.Chrome('/home/filkatron/Downloads/chromedriver', options=options)

    counter = 1

    while True:
        print("Running for %d. time" % counter)
        counter += 1

        for listing_url in links:
            print("Checking URL: %s" % listing_url)
            start = time.time()

            results = scrape_etsy_listing(listing_url, driver)

            end = time.time()

            print(results)

            print("execution time: %f\n" % round(end - start))

    driver.close()


if __name__ == "__main__":
    main()

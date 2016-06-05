from bs4 import BeautifulSoup
from urllib2 import urlopen
from urllib import urlretrieve
import json
import datetime
import codecs
from HorrorShow import settings
from time import sleep


def get_imdb_urls(out_file):
    """ Create list of imdb_urls to use in get_movie_ids function. """
    # url pattern for all imdb.json horror results is: http://www.imdb.com/search/title?genres=horror&sort=moviemeter&title_type=feature&start=n
    # where n starts at 1 and counts up by 50, with 19,696 results total
    imdb_urls = []
    imdb_base = "http://www.imdb.com/search/title?genres=horror&sort=moviemeter&title_type=feature&start="
    # initial value for
    start = 1

    while len(imdb_urls) <= 394:
        imdb_url = imdb_base + str(start)
        imdb_urls.append(imdb_url)
        start = int(start)
        start += 50

    with open(out_file, 'w') as url_file:
        for url in imdb_urls:
            url_file.write(url + '\n')


def get_movie_ids(in_file, out_file):
    """ Get movie information from IMDb to seed horrorshow database.
        Takes out_file, the location of a text file to which imdb_ids will be written, and imdb_urls created by get_imdb_urls function.
        For each URL in the list, open that URL,
        Make it into soup for parsing,
        From each link in the soup containing the search result's imdb_id, get the imdb_id
        and write it to the movies.json file.
        Return list of IMDb IDs.
    """
    # list of imdb.json id numbers to pass
    imdb_ids = []
    with open(in_file, 'r') as urls_file:
        for url in urls_file:
            # Get html from URL
            html = urlopen(url)
            soup = BeautifulSoup(html, 'html.parser')

            for link in soup.find_all('a', href=True):
                # get only links containing imdb.json id of result movies
                if '/title/tt' in link['href'] and 'vote' not in link['href']:
                    # only need movie id
                    imdb_id = (link['href'].split('/'))[2]
                    # append imdb.json id number to imdb_ids list, which will be returned
                    imdb_ids.append(imdb_id)

            with open(out_file, 'w') as cur_file:
                ids = set(imdb_ids)
                # write imdb id to file so we can read the file as an alternative to scraping IMDb directly in the future.
                for item in ids:
                    cur_file.write(item + '\n')


def get_imdb_ids(in_file, out_file):
    """ Take json file generated by Kimono Labs API-creator per Katie Lundsgaard's recommendation,
        parse to get imdb ids
        and write to a text files to be used by get_movie_info()
    """
    with open(out_file, 'a') as imdb_id_file:
        with open(in_file, 'r') as imdb_json:
            # make the json into a python dict
            imdb_data = json.loads(imdb_json)
            # get the movie element and its value
            movie_info = imdb_data["results"]['collection1']
            for item in movie_info:
                imdb_url = item["movie"]["href"]
                split_url = imdb_url.split("/")
                imdb_id = split_url[-1]
                imdb_id_file.write(imdb_id + '\n')


def get_movie_info(in_file, out_file):
    """ For each imdb_id in the imdb_ids list, query OMDb to get JSON object containing
        information about that movie and write to out_file.
    """
    # open up the ouput file to hold movie data
    with codecs.open(out_file, 'a', encoding='utf8') as movies_file:
        with codecs.open(in_file, 'r', encoding='utf8') as ids_file:
            for imdb_id in ids_file:
                imdb_id = imdb_id.strip()
                # if there's already a movie entry with that primary key, skip it
                imdb_url = "http://www.imdb.com/title/" + imdb_id
                try:
                    # OMDb API returns JSON
                    # http://www.omdbapi.com/?i=tt1974419&plot=full&r=json
                    omdb_url = "http://www.omdbapi.com/?i=" + imdb_id + "&plot=full&r=json"
                    omdb_response = urlopen(omdb_url)
                    omdb_data = json.loads(omdb_response.read())
                    imdb_id = omdb_data['imdbID']
                    title = omdb_data['Title']
                    year = omdb_data['Year']
                    rated = omdb_data["Rated"]
                    release_date = omdb_data['Released']
                    runtime = omdb_data['Runtime']
                    genre = omdb_data['Genre']
                    plot = omdb_data['Plot']
                    language = omdb_data['Language']
                    country = omdb_data['Country']
                    poster_url = omdb_data['Poster']
                    # get local copy of image at poster_url
                    poster_name = imdb_id + ".jpg"
                    # save the image locally
                    try:
                        urlretrieve(poster_url, poster_name)
                        has_poster = True
                    except IOError as err:
                        has_poster = False
                        print poster_url + "|" + str(err)
                        continue

                    # Get Guidebox ID for future API calls to get streaming data
                    # https://api-public.guidebox.com/v1.43/US/rKpZSpDchEEYZRL6LVI941ep3phbR4i7/search/movie/id/imdb/tt0420223
                    guidebox_url = "http://api-public.guidebox.com/v1.43/US/" + settings.GUIDEBOX_KEY + "/search/movie/id/imdb/" + imdb_id
                    guidebox_response = urlopen(guidebox_url)
                    guidebox_data = json.loads(guidebox_response.read())
                    try:
                        guidebox_id = str(guidebox_data['id'])
                    except KeyError as err:
                        print imdb_id + "|" + str(err)
                        guidebox_id = '0'

                    print_line = imdb_id + '|' \
                                 + guidebox_id + '|' \
                                 + title + '|' \
                                 + year + '|' \
                                 + rated + '|' \
                                 + release_date + '|' \
                                 + runtime + '|' \
                                 + genre + '|' \
                                 + plot + '|' \
                                 + language + '|' \
                                 + country + '|' \
                                 + poster_url + '|' \
                                 + poster_name + '|' \
                                 + imdb_url + '|' \
                                 + omdb_url + '|' \
                                 + str(has_poster) + '\n'

                    movies_file.write(print_line)

                    sleep(10)

                except KeyError as err:
                    print imdb_id + "|" + str(err)
                    continue


def get_movie_json(in_file, out_file):
    """ Create JSON file to load into database.
        Takes in_file (the out_file from get_movie_info()), and out_file (the JSON file being created by this function)
        Data needs to be in the following format:
        [
         {
          "model": "myapp.person",
          "pk": 1,
          "fields": {
            "first_name": "John",
            "last_name": "Lennon"
            }
         },
         {
          "model": "myapp.person",
          "pk": 2,
          "fields": {
            "first_name": "Paul",
            "last_name": "McCartney"
            }
         }
        ]
    """
    with open(out_file, 'w') as fixture_file:
        with open(in_file, 'r') as movies_file:
            fixture_file.write("[\n")
            # unpack the field names from the movie_info file
            for line in movies_file:
                imdb_id, guidebox_id, title, year, rated, release_date, runtime, genre, plot, language, country, poster_url, poster_name, imdb_url, omdb_url, has_poster = line.split('|')
                fixture_file.write('\t{\n')
                fixture_file.write('\t\t"model": "movies.movie",\n')
                fixture_file.write('\t\t"pk": "' + imdb_id + '",\n')
                fixture_file.write('\t\t"fields": {\n')
                fixture_file.write('\t\t\t"guidebox_id": "' + guidebox_id + '",\n')
                fixture_file.write('\t\t\t"title": "' + title + '",\n')
                # year string needs to be datetime object, as string
                year = datetime.datetime.strptime(year, '%Y').date()
                fixture_file.write('\t\t\t"year": "' + str(year) + '",\n')
                fixture_file.write('\t\t\t"rated": "' + rated + '",\n')
                # format release date correctly
                date_obj = datetime.datetime.strptime(release_date, '%d %b %Y').date()
                date_str = datetime.datetime.strftime(date_obj, '%Y-%m-%d')
                fixture_file.write('\t\t\t"release_date": "' + date_str + '",\n')
                fixture_file.write('\t\t\t"runtime": "' + runtime + '",\n')
                fixture_file.write('\t\t\t"genre": "' + genre + '",\n')
                fixture_file.write('\t\t\t"plot": "' + plot.replace('"', "'") + '",\n')
                fixture_file.write('\t\t\t"language": "' + language + '",\n')
                fixture_file.write('\t\t\t"country": "' + country + '",\n')
                fixture_file.write('\t\t\t"poster_url": "' + poster_url + '",\n')
                fixture_file.write('\t\t\t"poster_loc": "' + poster_name + '",\n')
                fixture_file.write('\t\t\t"imdb_url": "' + imdb_url + '",\n')
                fixture_file.write('\t\t\t"omdb_url": "' + omdb_url.strip() + '"\n')
                fixture_file.write('\t\t\t"has_poster": "' + has_poster + '"\n')
                fixture_file.write('\t\t}\n')
                fixture_file.write('\t},\n')
            fixture_file.write("]\n")

            sleep(1)


def guidebox_import(guidebox_id):
    if guidebox_id == '0':
        return None
    else:
        # Get Guidebox ID for future API calls to get streaming data
        guidebox_url = "http://api-public.guidebox.com/v1.43/US/" + settings.GUIDEBOX_KEY + "/movie/" + guidebox_id
        guidebox_response = urlopen(guidebox_url)
        guidebox_data = json.loads(guidebox_response.read())

        return guidebox_data

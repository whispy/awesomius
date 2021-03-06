"weather, thanks to wunderground"

from util import hook, http
import urllib2
import json


@hook.command(autohelp=False)
def weather(inp, nick='', server='', reply=None, db=None, bot=None):
    ".weather <location> [dontsave] -- gets weather data from Wunderground "\
            "http://wunderground.com/weather/api"

    api_key = bot.config.get("api_keys", {}).get("wunderground", None)
    if not api_key:
        return None

    loc = inp

    dontsave = loc.endswith(" dontsave")
    if dontsave:
        loc = loc[:-9].strip().lower()

    db.execute("create table if not exists weather(nick primary key, loc)")

    if not loc:  # blank line
        loc = db.execute("select loc from weather where nick=lower(?)",
                            (nick,)).fetchone()
        if not loc:
            return weather.__doc__
        loc = loc[0]

    loc, sep, state = loc.partition(', ')

    if state:
        state += '/'

    url = 'http://api.wunderground.com/api/'
    query = '{key}/geolookup/conditions/forecast/q/{state}{loc}.json' \
            .format(key=api_key, state=state, loc=loc)
    url += urllib2.quote(query)

    try:
        f = urllib2.urlopen(url)
        json_string = f.read()
        parsed_json = json.loads(json_string)
        f.close()
    except urllib2.HTTPError:
        print "Error fetching data from {url}".format(url=url)
        return None

    info = {}
    if 'current_observation' not in parsed_json:
        resp = 'Could not find weather for {inp}. '.format(inp=inp)

        # In the case of no obervation, but results, print some possible
        # location matches
        if 'results' in parsed_json['response']:
            resp += 'Possible matches include: '
            results = parsed_json['response']['results']

            for place in results[:6]:
                resp += '{city} '.format(**place)

                if place['state']:
                    resp += '{state} '.format(**place)

                if place['country_name']:
                    resp += '{country_name}, '.format(**place)

            resp = resp[:-2]

        reply(resp)
        return

    obs = parsed_json['current_observation']
    sf = parsed_json['forecast']['simpleforecast']['forecastday'][0]
    info['city'] = obs['display_location']['full']
    info['t_f'] = obs['temp_f']
    info['t_c'] = obs['temp_c']
    info['weather'] = obs['weather']
    info['h_f'] = sf['high']['fahrenheit']
    info['h_c'] = sf['high']['celsius']
    info['l_f'] = sf['low']['fahrenheit']
    info['l_c'] = sf['low']['celsius']
    info['humid'] = obs['relative_humidity']
    info['wind'] = 'Wind: {mph}mph/{kph}kph'\
            .format(mph=obs['wind_mph'], kph=obs['wind_kph'])
    reply('{city}: {weather}, {t_f}F/{t_c}C'\
            '(H:{h_f}F/{h_c}C L:{l_f}F/{l_c}C)' \
            ', Humidity: {humid}, {wind}'.format(**info))

    if inp and not dontsave:
        db.execute("insert or replace into weather(nick, loc) values (?,?)",
                     (nick.lower(), loc))
        db.commit()

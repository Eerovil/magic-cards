#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pychromecast
import random
from pychromecast.controllers.youtube import YouTubeController
from androidviewclient import Netflix
from areena import Areena

NETFLIX_APP_ID = 'CA5E8412'
AREENA_APP_ID = 'A9BCCB7C'


class Chromecast():
    """
    Helper class, which is basically the same as pychromecast.Chromecast
    """
    def __init__(self, chromecast_ip):
        self.cast = pychromecast.Chromecast(chromecast_ip)
        self.cast.wait()

    def quit(self):
        self.cast.quit_app()

    def stop(self):
        self.cast.media_controller.stop()

    def get_name(self):
        return self.cast.device.friendly_name

    def start_app(self, app):
        if app.lower() == 'netflix':
            self.cast.start_app(NETFLIX_APP_ID)
        elif app.lower() == 'areena':
            self.cast.start_app(AREENA_APP_ID)
        else:
            raise NotImplementedError()

    def play_media(self, url, content_type='video/mp4', **kwargs):
        """
        kwargs can consist of:

        title: str - title of the media.
        thumb: str - thumbnail image url.
        current_time: float - seconds from the beginning of the media
            to start playback.
        autoplay: bool - whether the media will automatically play.
        stream_type: str - describes the type of media artifact as one of the
            following: "NONE", "BUFFERED", "LIVE".
        subtitles: str - url of subtitle file to be shown on chromecast.
        subtitles_lang: str - language for subtitles.
        subtitles_mime: str - mimetype of subtitles.
        subtitle_id: int - id of subtitle to be loaded.
        metadata: dict - media metadata object, one of the following:
            GenericMediaMetadata, MovieMediaMetadata, TvShowMediaMetadata,
            MusicTrackMediaMetadata, PhotoMediaMetadata.
        """
        print('playing media {}'.format(url))
        self.cast.play_media(url, content_type=content_type, **kwargs)

    def register_handler(self, *args, **kwargs):
        self.cast.register_handler(*args, **kwargs)


class MockChromecast(Chromecast):
    """
    When you're developing and don't really want to cast
    """
    def __init__(self, chromecast_ip):
        pass

    def quit(self):
        print("MockChromecast: quit()")

    def stop(self):
        print("MockChromecast: stop()")

    def get_name(self):
        return "Mock Chromecast"

    def start_app(self, app):
        if app.lower() == 'netflix':
            print("MockChromecast: start_app {}".format(app))
        elif app.lower() == 'areena':
            print("MockChromecast: start_app {}".format(app))
        else:
            raise NotImplementedError()

    def play_media(self, url, content_type='video/mp4', **kwargs):
        print("MockChromecast: play_media {}".format(url))

    def register_handler(self, handler, *args, **kwargs):
        pass


if __name__ == "__main__":
    import argparse
    import sys

    print(' '.join(sys.argv))

    parser = argparse.ArgumentParser(description="Chromecast Mediaplayer")
    parser.add_argument("--chromecast_ip", help="Chromecast IP", required=True)
    parser.add_argument("--app", help="App name", default='mediacontroller', required=False)
    parser.add_argument(
        "options", metavar="option", type=str, nargs="+", help="Media url data (one or more)",
    )
    # Netflix
    parser.add_argument("--connect_ip", help="IP for remote adb connection", required=False)
    # Areena
    parser.add_argument("--areena_key", help="Areena API Key", required=False)
    args = vars(parser.parse_args())
    # Clear args for any extra checks (There is one in android/viewclient.py", line 2796)
    sys.argv = [sys.argv[0]]
    if args['app'] != 'mediacontroller' and len(args["options"]) > 1:
        print(
            "Warning: Chromecast currently only takes a single url argument: Ignored {}".format(
                ", ".join(args["options"][1:])
            )
        )
    if args['chromecast_ip'] == 'mock_chromecast':
        chromecast = MockChromecast('mock_chromecast')
    else:
        chromecast = Chromecast(args['chromecast_ip'])

    if args['app'] == 'mediacontroller':
        if args['options'][0] == 'stop':
            chromecast.stop()
        else:
            first = args['options'][0]
            flag = first.split(':')[0]
            if flag == 'random':
                all_urls = [':'.join(first.split(':')[1:])] + args['options'][1:]
                url = all_urls[random.randrange(0, len(all_urls) - 1)]
            else:
                url = first

            chromecast.play_media(url)
    elif args['app'] == 'youtube':
        yt = YouTubeController()
        chromecast.register_handler(yt)
        yt.play_video(args['options'][0])
    elif args['app'] == 'areena':
        # Start the areena app, just for show
        chromecast.stop()
        areena = Areena(args["areena_key"])
        uri = args['options'][0]
        flag = uri.split(':')[0]
        the_rest = ''.join(uri.split(':')[1:])
        # No latest or random flag = series
        if flag == 'latest':
            url = areena.get_series_url_latest(the_rest)
        elif flag == 'random':
            url = areena.get_series_url_random(the_rest)
            # No flag or empty flag = single program
        elif flag == '':
            url = areena.get_program_url(the_rest)
        else:
            url = areena.get_program_url(uri)
        chromecast.play_media(url)
    elif args["app"] == "netflix":
        # Start the netflix app, just for show (otherwise chromecast dashboard would load here
        # while we wait: Bad UI)
        chromecast.start_app('netflix')
        netflix = Netflix(chromecast.get_name(), connect_ip=args["connect_ip"] or None)
        netflix.main(args["options"][0])

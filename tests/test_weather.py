import json
import unittest
from collector.weather import Collector, FIELDS, parse_current


def payload():
    return {'current': {**{key: 12.5 for key in FIELDS}, 'time': 1790000000}}


class WeatherTests(unittest.TestCase):
    def test_all_fields_and_source_time(self):
        parsed = parse_current(payload())
        self.assertEqual(len(parsed), len(FIELDS) + 1)
        self.assertEqual(parsed['weather_temperature_fahrenheit'], 12.5)
        self.assertEqual(parsed['weather_source_timestamp_seconds'], 1790000000)

    def test_invalid_data_is_not_published_as_zero(self):
        for invalid in (None, float('nan'), 'bad'):
            data = payload()
            data['current']['temperature_2m'] = invalid
            with self.assertRaises(ValueError):
                parse_current(data)

    def test_outage_preserves_sample_but_reports_failure(self):
        location = {'name': 'Round Rock, TX'}
        collector = Collector([location], fetcher=lambda _: parse_current(payload()))
        collector.update_one(location)
        before = dict(collector.samples[location['name']])
        collector.fetcher = lambda _: (_ for _ in ()).throw(TimeoutError('test outage'))
        with self.assertLogs(level='ERROR'):
            collector.update_one(location)
        self.assertEqual(collector.samples[location['name']], before)
        self.assertEqual(collector.success[location['name']], 0)
        self.assertIn('weather_fetch_success{city="Round Rock, TX"} 0', collector.metrics())

    def test_independent_city_failure(self):
        locations = [{'name': 'good'}, {'name': 'bad'}]
        def fetcher(loc):
            if loc['name'] == 'bad':
                raise ValueError('failed')
            return parse_current(payload())
        collector = Collector(locations, fetcher=fetcher)
        collector.update_one(locations[0])
        with self.assertLogs(level='ERROR'):
            collector.update_one(locations[1])
        self.assertEqual(collector.success, {'good': 1, 'bad': 0})
        self.assertNotIn('weather_temperature_fahrenheit{city="bad"}', collector.metrics())

    def test_dashboard_refresh_and_unique_panel_ids(self):
        with open('grafana/dashboards/weather.json') as source:
            dashboard = json.load(source)
        self.assertEqual(dashboard['refresh'], '10s')
        ids = [panel['id'] for panel in dashboard['panels']]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == '__main__':
    unittest.main()

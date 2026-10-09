import io
from unittest.mock import patch
from pathlib import Path
import unittest
from scripts.audit_tasgaonkar import classify_duplicates, column, duplicate_conflicts, identifier_mapping, number, parse_month_label, weather_integrity, parse_timestamp, read_table, timestamp_profile, value_profile


class AuditTests(unittest.TestCase):
    def test_numeric_classification(self):
        self.assertEqual(number(' NA '),(None,'missing'))
        self.assertEqual(number('Reserve'),(None,'missing'))
        self.assertEqual(number('bad'),(None,'invalid'))
        self.assertEqual(number('inf'),(None,'invalid'))
        self.assertEqual(number(' 32.5 '),(32.5,'valid'))

    def test_ambiguous_date_hypotheses_remain_distinct(self):
        dmy=parse_timestamp('03-01-2018','12:00:00 AM','DMY')
        mdy=parse_timestamp('03-01-2018','12:00:00 AM','MDY')
        self.assertEqual((dmy.month,dmy.day),(1,3))
        self.assertEqual((mdy.month,mdy.day),(3,1))
        self.assertIsNone(dmy.tzinfo)

    def test_slash_dates_and_invalid_dates(self):
        self.assertEqual(parse_timestamp('2/28/2019','11:50:00 PM','MDY').hour,23)
        self.assertIsNone(parse_timestamp('2/28/2019','11:50:00 PM','DMY'))
        self.assertIsNone(parse_timestamp('','', 'MDY'))
        with self.assertRaises(ValueError):
            parse_timestamp('1/1/2018','00:00','guess')

    def test_cadence_duplicates_backward_steps_and_month_conflict(self):
        rows=[['01-03-18','00:10:00','3'],['01-03-18','00:00:00','3'],
              ['01-03-18','00:10:00','3'],['01-03-18','00:40:00','4']]
        _,p=timestamp_profile(rows,0,1,2,'DMY',10)
        self.assertEqual(p['duplicate_rows'],1)
        self.assertEqual(p['backward_steps_in_file'],1)
        self.assertEqual(p['largest_gap_minutes'],30)
        self.assertEqual(p['gaps_over_cadence'],1)
        self.assertEqual(p['month_mismatches'],1)

    def test_empty_timestamp_profile(self):
        _,p=timestamp_profile([],0,1,2,'MDY',10)
        self.assertIsNone(p['first'])
        self.assertEqual(p['unique_timestamps'],0)

    def test_duplicate_header_cannot_be_selected_by_name(self):
        with self.assertRaises(ValueError):
            column(['Time','Time'],'Time')
        self.assertEqual(column([' Time ','Date'],'Date'),1)

    def test_cp1252_and_ragged_csv(self):
        with patch.object(Path, 'open', return_value=io.StringIO('Time,Max\xa0\r\n00:00,30\r\n')) as opened:
            header,rows=read_table('synthetic.csv')
            opened.assert_called_once_with(encoding='cp1252', newline='')
            self.assertEqual(header[1],'Max\xa0')
            self.assertEqual(len(rows),1)
        with patch.object(Path, 'open', return_value=io.StringIO('a,b\n1\n')):
            with self.assertRaises(ValueError):
                read_table('synthetic.csv')

    def test_named_month_is_checked(self):
        _,p=timestamp_profile([['03-01-2018','00:00','Mar-18']],0,1,2,'MDY',10)
        self.assertEqual(p['month_comparable'],1)
        self.assertEqual(p['month_mismatches'],0)
        _,p=timestamp_profile([['03-01-2018','00:00','March']],0,1,2,'DMY',10)
        self.assertEqual(p['month_mismatches'],1)

    def test_conflicting_duplicates_are_not_averaged(self):
        stamp=parse_timestamp('1/1/2018','00:00','MDY')
        self.assertEqual(duplicate_conflicts([['30'],['31'],['NA']],[stamp]*3,0),1)
        self.assertEqual(duplicate_conflicts([['30'],['30']],[stamp]*2,0),0)

    def test_value_summary_excludes_missing_and_invalid(self):
        self.assertEqual(value_profile([['30'],['NA'],['bad'],['35']],0),
                         {'valid':2,'missing':1,'invalid':1,'minimum':30,'maximum':35})


class IntegrityTests(unittest.TestCase):
    def test_month_label_keeps_year_and_unknowns(self):
        self.assertEqual(parse_month_label('Sep-18'), (9, 2018))
        self.assertEqual(parse_month_label('September'), (9, None))
        self.assertEqual(parse_month_label('9'), (9, None))
        self.assertEqual(parse_month_label('13'), (None, None))
        self.assertEqual(parse_month_label('unknown'), (None, None))

    def test_timestamp_profile_checks_year_without_changing_month_counts(self):
        _,profile=timestamp_profile([['01-09-18','00:00','Sep-17']],0,1,2,'DMY',60)
        self.assertEqual(profile['month_mismatches'],0)
        self.assertEqual(profile['year_comparable'],1)
        self.assertEqual(profile['year_mismatches'],1)

    def test_exact_mapping_preserves_leading_zeros_and_channel_suffix(self):
        result=identifier_mapping([' 00000001 ', '00000001 (RH)', '00000002'], ['00000001', '00000003'])
        self.assertEqual(result['matched_temperature_ids'], ['00000001'])
        self.assertEqual(result['indoor_only_ids'], ['00000002'])
        self.assertEqual(result['housing_only_ids'], ['00000003'])
        self.assertEqual([c['channel'] for c in result['channels']], ['temperature','rh','temperature'])
        self.assertFalse(result['household_grouping_verified'])

    def test_mapping_refuses_collisions_and_does_not_pad_ids(self):
        with self.assertRaises(ValueError):
            identifier_mapping(['00000001'], ['00000001',' 00000001 '])
        with self.assertRaises(ValueError):
            identifier_mapping(['00000001',' 00000001 '], ['00000001'])
        result=identifier_mapping(['00000001'], ['1'])
        self.assertEqual(result['matched_temperature_ids'], [])

    def test_duplicate_categories_do_not_merge_rows(self):
        stamp=parse_timestamp('1/1/2018','00:00','MDY')
        fixtures=[([['30','NA'],['30','NA']], 'identical_measurements'),
                  ([['30','NA'],['NA','50']], 'complementary_missingness'),
                  ([['30','50'],['31','NA']], 'conflicting_measurements'),
                  ([['bad','NA'],['30','50']], 'invalid_payload')]
        for rows,category in fixtures:
            original=[row[:] for row in rows]
            result=classify_duplicates(rows,[stamp,stamp],[0,1])
            self.assertEqual(result['group_counts'], {category:1})
            self.assertEqual(result['excess_rows'],1)
            self.assertEqual(result['groups'][0]['source_rows'], [2,3])
            self.assertEqual(rows,original)

    def test_different_metadata_is_not_an_exact_raw_duplicate(self):
        stamp=parse_timestamp('1/1/2018','00:00','MDY')
        result=classify_duplicates([['30','first'],['30','second']],[stamp,stamp],[0])
        self.assertFalse(result['groups'][0]['all_raw_fields_identical'])
        self.assertEqual(result['group_counts'], {'identical_measurements':1})

    @staticmethod
    def weather_fixture():
        header=['DD/MM/YYYY','Time','Hours','Month','Season','wind speed',
                'Wind direction','Air temperature','Rain collection','Solar radiation',
                'Pressure','Humidity','Min Wind speed Min','Min Air temperature Min',
                'Max Wind speed','Max Air temperature','Time','Date','ReceiveTime','ReceiveDate']
        def row(date,month,tail,receive):
            return [date,'12:00:18 AM','24',month,'Summer','1','0','30','0','0',
                    '1000','50','0','29','2','31','00:18.0',tail,'01:23.0',receive]
        return header,row

    def test_redundant_dates_and_reception_date_remain_distinct(self):
        header,row=self.weather_fixture()
        records=[row('01-09-18','Aug-18','09-01-18','09-03-18')]
        result=weather_integrity(header,records)
        self.assertEqual(result['date_order_comparisons']['DMY_leading_MDY_trailing']['equal_calendar_dates'],1)
        self.assertEqual(result['month_year_disagreements'],1)
        self.assertEqual(result['receive_date_mdy_minus_leading_date_dmy_days'],{2:1})
        self.assertEqual(result['disagreement_details'][0]['raw_fields_by_position']['19'],'09-03-18')
        self.assertEqual(records[0][3],'Aug-18')

    def test_year_mismatch_and_contiguous_blocks(self):
        header,row=self.weather_fixture()
        records=[row('01-09-18','Sep-17','09-01-18','09-01-18'),
                 row('02-09-18','Sep-17','09-02-18','09-02-18'),
                 row('03-09-18','Sep-18','09-03-18','09-03-18'),
                 row('04-09-18','Sep-17','09-04-18','09-04-18')]
        result=weather_integrity(header,records)
        self.assertEqual(result['year_label_disagreements'],3)
        self.assertEqual([b['count'] for b in result['disagreement_blocks']], [2,1])

    def test_positional_time_schema_is_required(self):
        header,row=self.weather_fixture()
        header[16]='Other'
        with self.assertRaises(ValueError):
            weather_integrity(header,[])


if __name__=='__main__':
    unittest.main()

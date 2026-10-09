import io
from unittest.mock import patch
from pathlib import Path
import unittest
from scripts.audit_tasgaonkar import column, duplicate_conflicts, number, parse_timestamp, read_table, timestamp_profile, value_profile


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


if __name__=='__main__':
    unittest.main()
